"""
動態難度調整服務 (Adaptive Difficulty Service)

Phase 2 P0 功能 - Week 2
技術方案：IRT 2PL 模型 + 冷啟動策略（L3/前 5 題）
驗收標準：響應時間 < 1 秒，用戶滿意度 ≥ 4/5

功能：
1. IRT 2PL 模型（難度 b + 區分度 a，移除猜測參數 c）
2. 冷啟動策略（新用戶默認 L3，前 5 題不調整）
3. 實時能力追蹤（正確率、響應時間、嘗試次數）
4. 難度分級（L1-L5）
5. 調整策略（連續 3 題正確→升級，連續 2 題錯誤→降級）
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import math


@dataclass
class ItemParameters:
    """題目參數（IRT 2PL 模型）"""
    item_id: str
    difficulty: float  # b parameter (-3 to +3)
    discrimination: float  # a parameter (0.5 to 2.0)
    difficulty_level: int = 3  # L1-L5 (1-5)
    knowledge_point_id: str = ""
    calibrated_by: str = "expert"  # 'expert' | 'sample_test'
    calibration_date: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "item_id": self.item_id,
            "difficulty": round(self.difficulty, 3),
            "discrimination": round(self.discrimination, 3),
            "difficulty_level": self.difficulty_level,
            "knowledge_point_id": self.knowledge_point_id,
            "calibrated_by": self.calibrated_by,
            "calibration_date": self.calibration_date.isoformat()
        }


@dataclass
class UserProgress:
    """用戶進度數據結構"""
    user_id: str
    current_level: int = 3  # L1-L5，默認 L3
    questions_answered: int = 0  # 用於冷啟動計數
    ability_estimate: float = 0.0  # theta estimate
    ability_std: float = 1.0  # 能力估計標準誤
    last_5_responses: List[bool] = field(default_factory=list)  # 冷啟動期記錄
    consecutive_correct: int = 0  # 連續正確數
    consecutive_wrong: int = 0  # 連續錯誤數
    total_correct: int = 0
    total_answered: int = 0
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "current_level": self.current_level,
            "questions_answered": self.questions_answered,
            "ability_estimate": round(self.ability_estimate, 3),
            "ability_std": round(self.ability_std, 3),
            "cold_start_complete": self.questions_answered >= 5,
            "consecutive_correct": self.consecutive_correct,
            "consecutive_wrong": self.consecutive_wrong,
            "accuracy_rate": round(self.total_correct / max(self.total_answered, 1), 3),
            "last_updated": self.last_updated.isoformat()
        }


@dataclass
class ItemResponse:
    """用戶作答記錄"""
    user_id: str
    item_id: str
    correct: bool
    response_time: float  # seconds
    attempted_at: datetime = field(default_factory=datetime.now)
    ability_estimate: float = 0.0  # theta at time of response
    is_cold_start: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "item_id": self.item_id,
            "correct": self.correct,
            "response_time": round(self.response_time, 2),
            "attempted_at": self.attempted_at.isoformat(),
            "ability_estimate": round(self.ability_estimate, 3),
            "is_cold_start": self.is_cold_start
        }


class IRT2PLModel:
    """
    IRT 二參數 Logistic 模型 (2PL)
    
    P(X=1|θ,a,b) = 1 / (1 + exp(-a*(θ-b)))
    
    其中：
    - θ: 用戶能力 (ability)
    - a: 題目區分度 (discrimination)
    - b: 題目難度 (difficulty)
    """
    
    @staticmethod
    def probability(theta: float, a: float, b: float) -> float:
        """
        計算答對概率
        
        Args:
            theta: 用戶能力估計
            a: 題目區分度 (0.5-2.0)
            b: 題目難度 (-3 to +3)
        
        Returns:
            float: 答對概率 (0-1)
        """
        # 限制 a 在合理範圍
        a = max(0.1, min(a, 3.0))
        
        # 2PL 公式
        exponent = -a * (theta - b)
        
        # 防止數值溢出
        if exponent > 100:
            return 0.0
        elif exponent < -100:
            return 1.0
        
        return 1.0 / (1.0 + math.exp(exponent))
    
    @staticmethod
    def log_likelihood(theta: float, responses: List[Tuple[float, float, bool]]) -> float:
        """
        計算對數似然函數
        
        Args:
            theta: 用戶能力估計
            responses: [(a_i, b_i, correct_i), ...]
        
        Returns:
            float: 對數似然值
        """
        ll = 0.0
        for a, b, correct in responses:
            p = IRT2PLModel.probability(theta, a, b)
            if correct:
                ll += math.log(max(p, 1e-10))
            else:
                ll += math.log(max(1 - p, 1e-10))
        return ll
    
    @staticmethod
    def estimate_ability(responses: List[Tuple[float, float, bool]], 
                        theta_init: float = 0.0,
                        max_iter: int = 20,
                        tolerance: float = 1e-6) -> Tuple[float, float]:
        """
        使用最大似然估計 (MLE) 估計用戶能力
        
        Args:
            responses: [(a_i, b_i, correct_i), ...]
            theta_init: 初始能力估計
            max_iter: 最大迭代次數
            tolerance: 收斂容差
        
        Returns:
            (theta, std_error): 能力估計和標準誤
        """
        if len(responses) < 2:
            # 數據不足，返回初始值和較大標準誤
            return theta_init, 1.0
        
        theta = theta_init
        
        for iteration in range(max_iter):
            # 計算一階導數 (score function) 和二階導數 (information)
            score = 0.0
            info = 0.0
            
            for a, b, correct in responses:
                p = IRT2PLModel.probability(theta, a, b)
                
                # 一階導數
                score += a * (correct - p)
                
                # 二階導數 (Fisher information)
                info += a * a * p * (1 - p)
            
            # Newton-Raphson 更新
            if info < 1e-10:
                break
            
            delta = score / info
            theta_new = theta + delta
            
            # 檢查收斂
            if abs(delta) < tolerance:
                theta = theta_new
                break
            
            theta = theta_new
        
        # 計算標準誤
        std_error = 1.0 / math.sqrt(max(info, 1e-10))
        
        return theta, std_error


class AdaptiveDifficultyService:
    """動態難度調整服務"""
    
    # 難度等級映射
    LEVEL_THRESHOLDS = {
        1: (-float('inf'), -1.5),    # L1: b < -1.5
        2: (-1.5, -0.5),              # L2: -1.5 ≤ b < -0.5
        3: (-0.5, 0.5),               # L3: -0.5 ≤ b < 0.5
        4: (0.5, 1.5),                # L4: 0.5 ≤ b < 1.5
        5: (1.5, float('inf'))        # L5: b ≥ 1.5
    }
    
    COLD_START_THRESHOLD = 5  # 前 5 題不調整
    UPGRADE_THRESHOLD = 3     # 連續 3 題正確升級
    DOWNGRADE_THRESHOLD = 2   # 連續 2 題錯誤降級
    
    def __init__(self):
        # 模擬數據庫存儲
        self._item_parameters: Dict[str, ItemParameters] = {}
        self._user_progress: Dict[str, UserProgress] = {}
        self._response_history: Dict[str, List[ItemResponse]] = {}
    
    def register_item(self, item_id: str, difficulty: float, discrimination: float,
                     knowledge_point_id: str = "", calibrated_by: str = "expert") -> ItemParameters:
        """
        註冊題目參數
        
        Args:
            item_id: 題目 ID
            difficulty: 難度參數 b (-3 to +3)
            discrimination: 區分度參數 a (0.5 to 2.0)
            knowledge_point_id: 知識點 ID
            calibrated_by: 標定來源
        
        Returns:
            ItemParameters: 題目參數
        """
        # 限制參數範圍
        difficulty = max(-3.0, min(3.0, difficulty))
        discrimination = max(0.5, min(2.0, discrimination))
        
        # 根據難度 b 值確定難度等級
        difficulty_level = self._get_difficulty_level(difficulty)
        
        item = ItemParameters(
            item_id=item_id,
            difficulty=difficulty,
            discrimination=discrimination,
            difficulty_level=difficulty_level,
            knowledge_point_id=knowledge_point_id,
            calibrated_by=calibrated_by
        )
        
        self._item_parameters[item_id] = item
        return item
    
    def _get_difficulty_level(self, difficulty: float) -> int:
        """根據難度 b 值確定難度等級 L1-L5"""
        for level, (low, high) in self.LEVEL_THRESHOLDS.items():
            if low <= difficulty < high:
                return level
        return 3  # 默認 L3
    
    def get_user_progress(self, user_id: str) -> UserProgress:
        """獲取用戶進度（不存在則創建）"""
        if user_id not in self._user_progress:
            self._user_progress[user_id] = UserProgress(user_id=user_id)
        return self._user_progress[user_id]
    
    def is_cold_start(self, user_id: str) -> bool:
        """檢查用戶是否處於冷啟動期"""
        progress = self.get_user_progress(user_id)
        return progress.questions_answered < self.COLD_START_THRESHOLD
    
    def get_next_item(self, user_id: str, 
                     candidate_items: List[str]) -> Optional[Dict]:
        """
        為用戶選擇下一道題目
        
        Args:
            user_id: 用戶 ID
            candidate_items: 候選題目 ID 列表
        
        Returns:
            Dict: {item_id, difficulty_level, estimated_success_rate, is_cold_start}
        """
        progress = self.get_user_progress(user_id)
        
        # 冷啟動期：選擇難度 L3 的題目
        if self.is_cold_start(user_id):
            # 優先選擇 L3 題目
            l3_items = [
                item_id for item_id in candidate_items
                if item_id in self._item_parameters 
                and self._item_parameters[item_id].difficulty_level == 3
            ]
            
            if l3_items:
                selected_item = l3_items[0]
            elif candidate_items:
                # 沒有 L3 則隨機選擇
                selected_item = candidate_items[0]
            else:
                return None
            
            item = self._item_parameters[selected_item]
            return {
                "item_id": selected_item,
                "difficulty_level": 3,  # 冷啟動期固定 L3
                "estimated_success_rate": 0.5,  # 冷啟動期不預測
                "is_cold_start": True
            }
        
        # 冷啟動結束後：根據能力估計選擇題目
        theta = progress.ability_estimate
        
        # 選擇難度最匹配用戶能力的題目（b ≈ θ）
        best_item = None
        best_diff = float('inf')
        
        for item_id in candidate_items:
            if item_id not in self._item_parameters:
                continue
            
            item = self._item_parameters[item_id]
            diff = abs(item.difficulty - theta)
            
            if diff < best_diff:
                best_diff = diff
                best_item = item
        
        if best_item is None:
            return None
        
        # 計算預估成功率
        success_rate = IRT2PLModel.probability(
            theta, 
            best_item.discrimination, 
            best_item.difficulty
        )
        
        return {
            "item_id": best_item.item_id,
            "difficulty_level": best_item.difficulty_level,
            "estimated_success_rate": round(success_rate, 3),
            "is_cold_start": False
        }
    
    def update_ability(self, user_id: str, item_id: str, 
                      correct: bool, response_time: float) -> Dict:
        """
        更新用戶能力估計
        
        Args:
            user_id: 用戶 ID
            item_id: 題目 ID
            correct: 是否答對
            response_time: 響應時間（秒）
        
        Returns:
            Dict: {new_ability, confidence_interval, questions_answered}
        """
        if item_id not in self._item_parameters:
            raise ValueError(f"未知的題目 ID: {item_id}")
        
        item = self._item_parameters[item_id]
        progress = self.get_user_progress(user_id)
        
        # 記錄作答
        is_cold_start = self.is_cold_start(user_id)
        response = ItemResponse(
            user_id=user_id,
            item_id=item_id,
            correct=correct,
            response_time=response_time,
            ability_estimate=progress.ability_estimate,
            is_cold_start=is_cold_start
        )
        
        if user_id not in self._response_history:
            self._response_history[user_id] = []
        self._response_history[user_id].append(response)
        
        # 更新統計
        progress.questions_answered += 1
        progress.total_answered += 1
        if correct:
            progress.total_correct += 1
            progress.consecutive_correct += 1
            progress.consecutive_wrong = 0
        else:
            progress.consecutive_wrong += 1
            progress.consecutive_correct = 0
        
        # 冷啟動期：只記錄，不更新能力估計
        if is_cold_start:
            progress.last_5_responses.append(correct)
            # 保持前 5 題的記錄
            if len(progress.last_5_responses) > 5:
                progress.last_5_responses.pop(0)
            
            progress.last_updated = datetime.now()
            
            return {
                "new_ability": progress.ability_estimate,
                "confidence_interval": [
                    round(progress.ability_estimate - 1.96 * progress.ability_std, 3),
                    round(progress.ability_estimate + 1.96 * progress.ability_std, 3)
                ],
                "questions_answered": progress.questions_answered,
                "is_cold_start": True
            }
        
        # 冷啟動結束後：使用 IRT MLE 更新能力估計
        # 收集所有作答記錄用於 MLE
        responses_for_mle = []
        for resp in self._response_history[user_id][-20:]:  # 使用最近 20 題
            if resp.item_id in self._item_parameters:
                item_param = self._item_parameters[resp.item_id]
                responses_for_mle.append((
                    item_param.discrimination,
                    item_param.difficulty,
                    resp.correct
                ))
        
        # MLE 估計
        new_theta, new_std = IRT2PLModel.estimate_ability(
            responses_for_mle,
            theta_init=progress.ability_estimate
        )
        
        progress.ability_estimate = new_theta
        progress.ability_std = new_std
        
        # 難度調整策略
        self._adjust_difficulty_level(progress)
        
        progress.last_updated = datetime.now()
        
        # 計算 95% 置信區間
        ci_low = new_theta - 1.96 * new_std
        ci_high = new_theta + 1.96 * new_std
        
        return {
            "new_ability": round(new_theta, 3),
            "confidence_interval": [round(ci_low, 3), round(ci_high, 3)],
            "questions_answered": progress.questions_answered,
            "is_cold_start": False
        }
    
    def _adjust_difficulty_level(self, progress: UserProgress) -> None:
        """
        根據表現調整難度等級
        
        策略：
        - 連續 3 題正確 → 升級
        - 連續 2 題錯誤 → 降級
        """
        if progress.consecutive_correct >= self.UPGRADE_THRESHOLD:
            if progress.current_level < 5:
                progress.current_level += 1
                progress.consecutive_correct = 0  # 重置計數
        
        elif progress.consecutive_wrong >= self.DOWNGRADE_THRESHOLD:
            if progress.current_level > 1:
                progress.current_level -= 1
                progress.consecutive_wrong = 0  # 重置計數
    
    def get_item_parameters(self, item_id: str) -> Optional[ItemParameters]:
        """獲取題目參數"""
        return self._item_parameters.get(item_id)
    
    def get_response_history(self, user_id: str) -> List[ItemResponse]:
        """獲取用戶作答歷史"""
        return self._response_history.get(user_id, [])
    
    def calibrate_item_from_responses(self, item_id: str, 
                                      responses: List[Tuple[float, bool]]) -> ItemParameters:
        """
        根據用戶作答數據校準題目參數（小樣本測試用）
        
        Args:
            item_id: 題目 ID
            responses: [(theta_i, correct_i), ...] 用戶能力和作答結果
        
        Returns:
            ItemParameters: 校準後的題目參數
        """
        if len(responses) < 10:
            raise ValueError("至少需要 10 個作答記錄用於校準")
        
        # 簡化校準：使用邏輯回歸估計 b 和 a
        # 實際生產環境應使用更複雜的 MLE 或貝葉斯方法
        
        # 計算平均正確率
        accuracy = sum(1 for _, correct in responses if correct) / len(responses)
        
        # 計算平均用戶能力
        avg_theta = sum(theta for theta, _ in responses) / len(responses)
        
        # 估計難度 b：當 P=0.5 時，θ=b
        # 如果準確率>0.5，說明題目偏簡單（b 偏低）
        # 如果準確率<0.5，說明題目偏難（b 偏高）
        b_estimate = avg_theta - math.log(accuracy / (1 - accuracy + 1e-10)) * 0.5
        
        # 限制 b 在合理範圍
        b_estimate = max(-3.0, min(3.0, b_estimate))
        
        # 估計區分度 a：根據準確率分佈的陡峭程度
        # 簡化：假設 a=1.0（中等區分度）
        a_estimate = 1.0
        
        # 更新題目的參數
        if item_id in self._item_parameters:
            item = self._item_parameters[item_id]
            item.difficulty = b_estimate
            item.discrimination = a_estimate
            item.calibrated_by = "sample_test"
            item.calibration_date = datetime.now()
        else:
            item = self.register_item(
                item_id=item_id,
                difficulty=b_estimate,
                discrimination=a_estimate,
                calibrated_by="sample_test"
            )
        
        return item


# 全局服務實例
_service_instance: Optional[AdaptiveDifficultyService] = None


def get_service() -> AdaptiveDifficultyService:
    """獲取動態難度調整服務單例"""
    global _service_instance
    if _service_instance is None:
        _service_instance = AdaptiveDifficultyService()
    return _service_instance


if __name__ == "__main__":
    # 測試示例
    service = AdaptiveDifficultyService()
    
    # 1. 註冊題目
    print("=== 註冊題目 ===")
    service.register_item("item_001", difficulty=-2.0, discrimination=1.2, knowledge_point_id="kp_01")
    service.register_item("item_002", difficulty=-1.0, discrimination=1.0, knowledge_point_id="kp_01")
    service.register_item("item_003", difficulty=0.0, discrimination=1.5, knowledge_point_id="kp_02")
    service.register_item("item_004", difficulty=1.0, discrimination=1.3, knowledge_point_id="kp_02")
    service.register_item("item_005", difficulty=2.0, discrimination=1.1, knowledge_point_id="kp_03")
    
    # 2. 冷啟動期測試
    print("\n=== 冷啟動期測試 ===")
    candidate_items = ["item_001", "item_002", "item_003", "item_004", "item_005"]
    
    for i in range(5):
        next_item = service.get_next_item("user_001", candidate_items)
        print(f"第 {i+1} 題：{next_item}")
        
        # 模擬作答（假設用戶能力θ=0.5）
        service.update_ability(
            "user_001", 
            next_item["item_id"], 
            correct=(i >= 2),  # 前 2 題錯，後 3 題對
            response_time=30.0
        )
    
    # 3. 冷啟動結束後
    print("\n=== 冷啟動結束後 ===")
    progress = service.get_user_progress("user_001")
    print(f"用戶進度：{progress.to_dict()}")
    
    next_item = service.get_next_item("user_001", candidate_items)
    print(f"推薦題目：{next_item}")
    
    # 4. 連續答對升級測試
    print("\n=== 連續答對升級測試 ===")
    for i in range(3):
        service.update_ability("user_001", "item_003", correct=True, response_time=20.0)
    
    progress = service.get_user_progress("user_001")
    print(f"升級後等級：L{progress.current_level}")
    
    # 5. IRT 概率計算測試
    print("\n=== IRT 概率計算 ===")
    theta = 0.5
    for item_id in ["item_001", "item_002", "item_003", "item_004", "item_005"]:
        item = service.get_item_parameters(item_id)
        p = IRT2PLModel.probability(theta, item.discrimination, item.difficulty)
        print(f"  {item_id} (b={item.difficulty}): P(correct|θ={theta}) = {p:.3f}")
