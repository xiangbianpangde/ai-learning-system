"""
遺忘曲線校準服務 (Forgetting Curve Calibration Service)

Phase 2 P1 功能 - Week 4
技術方案：Ebbinghaus + SM-2 改進版
驗收標準：復習提醒準時率 ≥ 95%

功能：
1. Ebbinghaus 遺忘曲線基礎模型 (R = e^(-t/S))
2. 個體校準：記憶衰減係數 S 根據用戶歷史數據調整
3. SM-2 改進版算法
4. 復習提醒推送（復習時間前 1 小時）
5. 遺忘閾值：保留率 < 70% 觸發復習
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import math


@dataclass
class ReviewRecord:
    """復習記錄"""
    review_number: int  # 第幾次復習
    quality_score: int  # 0-5 質量評分
    reviewed_at: datetime = field(default_factory=datetime.now)
    interval_days: float = 0.0  # 距上次復習的天數
    
    def to_dict(self) -> Dict:
        return {
            "review_number": self.review_number,
            "quality_score": self.quality_score,
            "reviewed_at": self.reviewed_at.isoformat(),
            "interval_days": round(self.interval_days, 2)
        }


@dataclass
class ForgettingCurve:
    """遺忘曲線數據結構"""
    user_id: str
    item_id: str
    learned_at: datetime = field(default_factory=datetime.now)
    decay_coefficient: float = 1.0  # S parameter (個體記憶衰減係數)
    reviews: List[ReviewRecord] = field(default_factory=list)
    next_review: datetime = field(default_factory=datetime.now)
    retention_rate: float = 1.0  # 當前記憶保留率 (0-1)
    ease_factor: float = 2.5  # SM-2 難度係數 (初始 2.5)
    interval_days: float = 0.0  # 當前間隔天數
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "item_id": self.item_id,
            "learned_at": self.learned_at.isoformat(),
            "decay_coefficient": round(self.decay_coefficient, 3),
            "next_review": self.next_review.isoformat(),
            "retention_rate": round(self.retention_rate, 3),
            "ease_factor": round(self.ease_factor, 3),
            "interval_days": round(self.interval_days, 2),
            "total_reviews": len(self.reviews),
            "last_updated": self.last_updated.isoformat()
        }


class EbbinghausModel:
    """
    Ebbinghaus 遺忘曲線模型
    
    R = e^(-t/S)
    
    其中：
    - R: 記憶保留率 (0-1)
    - t: 時間（天）
    - S: 記憶衰減係數（個體差異）
    """
    
    @staticmethod
    def retention_rate(t_days: float, S: float) -> float:
        """
        計算記憶保留率
        
        Args:
            t_days: 經過的天數
            S: 記憶衰減係數
        
        Returns:
            float: 記憶保留率 (0-1)
        """
        if S <= 0:
            S = 1.0  # 防止除以零
        
        return math.exp(-t_days / S)
    
    @staticmethod
    def time_to_threshold(retention_target: float, S: float) -> float:
        """
        計算到達目標保留率所需的時間
        
        Args:
            retention_target: 目標保留率 (如 0.7 表示 70%)
            S: 記憶衰減係數
        
        Returns:
            float: 天數
        """
        if retention_target <= 0 or retention_target >= 1:
            return 1.0
        
        if S <= 0:
            S = 1.0
        
        # R = e^(-t/S) => t = -S * ln(R)
        return -S * math.log(retention_target)


class SM2Algorithm:
    """
    SM-2 間隔重複算法（改進版）
    
    參考：SuperMemo-2 算法
    """
    
    # 初始間隔（天）
    INITIAL_INTERVALS = [1, 3, 7]
    
    # 質量評分閾值
    FORGET_THRESHOLD = 3  # < 3 分視為遺忘
    
    # 難度係數調整
    EF_MIN = 1.3  # 最小難度係數
    EF_MAX = 3.0  # 最大難度係數
    
    @staticmethod
    def calculate_next_interval(ease_factor: float, review_number: int, 
                                quality_score: int, current_interval: float) -> float:
        """
        計算下次復習間隔
        
        Args:
            ease_factor: 難度係數 (1.3-3.0)
            review_number: 復習次數
            quality_score: 質量評分 (0-5)
            current_interval: 當前間隔天數
        
        Returns:
            float: 下次間隔天數
        """
        if quality_score < SM2Algorithm.FORGET_THRESHOLD:
            # 遺忘：重置間隔
            return 1.0
        
        if review_number == 0:
            # 第一次復習：1 天後
            return 1.0
        elif review_number == 1:
            # 第二次復習：3 天後
            return 3.0
        elif review_number == 2:
            # 第三次復習：7 天後
            return 7.0
        else:
            # 後續復習：根據難度係數計算
            return current_interval * ease_factor
    
    @staticmethod
    def update_ease_factor(ease_factor: float, quality_score: int) -> float:
        """
        更新難度係數
        
        Args:
            ease_factor: 當前難度係數
            quality_score: 質量評分 (0-5)
        
        Returns:
            float: 新難度係數
        """
        # SM-2 公式
        new_ef = ease_factor + (0.1 - (5 - quality_score) * (0.08 + (5 - quality_score) * 0.02))
        
        # 限制範圍
        return max(SM2Algorithm.EF_MIN, min(SM2Algorithm.EF_MAX, new_ef))


class ForgettingCurveService:
    """遺忘曲線校準服務"""
    
    # 遺忘閾值
    FORGET_THRESHOLD = 0.7  # 保留率 < 70% 觸發復習
    
    # 提醒提前時間
    REMINDER_ADVANCE_HOURS = 1  # 復習前 1 小時提醒
    
    def __init__(self):
        # 模擬數據庫存儲
        self._forgetting_curves: Dict[Tuple[str, str], ForgettingCurve] = {}
        self._calibrated_decay_coefficients: Dict[str, float] = {}  # 用戶級衰減係數
    
    def learn_item(self, user_id: str, item_id: str, 
                   quality_score: int = 4) -> ForgettingCurve:
        """
        學習新知識點
        
        Args:
            user_id: 用戶 ID
            item_id: 知識點 ID
            quality_score: 學習質量評分 (0-5)
        
        Returns:
            ForgettingCurve: 遺忘曲線記錄
        """
        key = (user_id, item_id)
        
        # 獲取用戶的個體衰減係數
        decay_coefficient = self._get_user_decay_coefficient(user_id)
        
        # 創建遺忘曲線記錄
        curve = ForgettingCurve(
            user_id=user_id,
            item_id=item_id,
            learned_at=datetime.now(),
            decay_coefficient=decay_coefficient,
            ease_factor=2.5,
            interval_days=0.0
        )
        
        # 初始復習記錄
        if quality_score >= SM2Algorithm.FORGET_THRESHOLD:
            curve.reviews.append(ReviewRecord(
                review_number=0,
                quality_score=quality_score,
                interval_days=0.0
            ))
        
        # 計算第一次復習時間
        next_interval = SM2Algorithm.calculate_next_interval(
            curve.ease_factor, 0, quality_score, 0.0
        )
        curve.next_review = datetime.now() + timedelta(days=next_interval)
        curve.interval_days = next_interval
        
        self._forgetting_curves[key] = curve
        return curve
    
    def review_item(self, user_id: str, item_id: str, 
                   quality_score: int) -> ForgettingCurve:
        """
        復習知識點
        
        Args:
            user_id: 用戶 ID
            item_id: 知識點 ID
            quality_score: 復習質量評分 (0-5)
        
        Returns:
            ForgettingCurve: 更新後的遺忘曲線記錄
        """
        key = (user_id, item_id)
        
        if key not in self._forgetting_curves:
            raise ValueError(f"用戶 {user_id} 未學習知識點 {item_id}")
        
        curve = self._forgetting_curves[key]
        
        # 計算距上次學習/復習的天數
        last_review = curve.reviews[-1] if curve.reviews else None
        if last_review:
            days_since_last = (datetime.now() - last_review.reviewed_at).days
        else:
            days_since_last = (datetime.now() - curve.learned_at).days
        
        # 更新難度係數
        curve.ease_factor = SM2Algorithm.update_ease_factor(
            curve.ease_factor, quality_score
        )
        
        # 計算下次間隔
        review_number = len(curve.reviews)
        next_interval = SM2Algorithm.calculate_next_interval(
            curve.ease_factor, review_number, quality_score, curve.interval_days
        )
        
        # 如果是遺忘（質量<3），重置衰減係數校準
        if quality_score < SM2Algorithm.FORGET_THRESHOLD:
            self._adjust_decay_coefficient(user_id, days_since_last, quality_score)
        
        # 添加復習記錄
        curve.reviews.append(ReviewRecord(
            review_number=review_number,
            quality_score=quality_score,
            interval_days=days_since_last
        ))
        
        # 更新下次復習時間
        curve.next_review = datetime.now() + timedelta(days=next_interval)
        curve.interval_days = next_interval
        
        # 更新當前保留率
        curve.retention_rate = self._calculate_current_retention(curve)
        curve.last_updated = datetime.now()
        
        return curve
    
    def get_due_items(self, user_id: str) -> List[Dict]:
        """
        獲取待復習項目
        
        Args:
            user_id: 用戶 ID
        
        Returns:
            List[Dict]: 待復習項目列表
        """
        due_items = []
        now = datetime.now()
        
        for (uid, item_id), curve in self._forgetting_curves.items():
            if uid != user_id:
                continue
            
            # 檢查是否到期
            time_to_review = (curve.next_review - now).total_seconds() / 3600
            
            # 到期或即將到期（1 小時內）
            if time_to_review <= self.REMINDER_ADVANCE_HOURS:
                # 計算當前保留率
                retention = self._calculate_current_retention(curve)
                
                due_items.append({
                    "item_id": item_id,
                    "due_at": curve.next_review.isoformat(),
                    "priority": self._calculate_priority(retention, time_to_review),
                    "retention_rate": round(retention, 3),
                    "hours_until_due": max(0, time_to_review),
                    "total_reviews": len(curve.reviews)
                })
        
        # 按優先級排序
        due_items.sort(key=lambda x: x["priority"], reverse=True)
        
        return due_items
    
    def _calculate_current_retention(self, curve: ForgettingCurve) -> float:
        """計算當前記憶保留率"""
        # 計算距上次復習的天數
        last_review = curve.reviews[-1] if curve.reviews else None
        if last_review:
            days_since = (datetime.now() - last_review.reviewed_at).days
        else:
            days_since = (datetime.now() - curve.learned_at).days
        
        # 使用 Ebbinghaus 模型計算
        retention = EbbinghausModel.retention_rate(days_since, curve.decay_coefficient)
        
        # 根據質量評分調整
        if curve.reviews:
            avg_quality = sum(r.quality_score for r in curve.reviews) / len(curve.reviews)
            # 質量越高，保留率越高
            retention *= (0.7 + 0.3 * (avg_quality / 5.0))
        
        return min(1.0, max(0.0, retention))
    
    def _calculate_priority(self, retention: float, hours_until_due: float) -> float:
        """
        計算復習優先級
        
        Args:
            retention: 當前保留率
            hours_until_due: 距復習時間的小時數
        
        Returns:
            float: 優先級分數 (越高越優先)
        """
        # 保留率越低，優先級越高
        retention_score = (1.0 - retention) * 100
        
        # 越緊急，優先級越高
        urgency_score = max(0, 24 - hours_until_due)
        
        return retention_score + urgency_score
    
    def _get_user_decay_coefficient(self, user_id: str) -> float:
        """獲取用戶的個體記憶衰減係數"""
        if user_id in self._calibrated_decay_coefficients:
            return self._calibrated_decay_coefficients[user_id]
        
        # 默認值：根據 Ebbinghaus 研究，平均 S ≈ 2-3 天
        return 2.5
    
    def _adjust_decay_coefficient(self, user_id: str, 
                                  days_elapsed: float, quality_score: int) -> None:
        """
        根據復習表現調整用戶的衰減係數
        
        Args:
            user_id: 用戶 ID
            days_elapsed: 經過的天數
            quality_score: 質量評分
        """
        current_S = self._get_user_decay_coefficient(user_id)
        
        # 如果質量低，說明遺忘快，需要減小 S
        # 如果質量高，說明遺忘慢，可以增大 S
        if quality_score < 3:
            # 遺忘快：減小 S
            adjustment = 0.9
        elif quality_score >= 4:
            # 記憶好：增大 S
            adjustment = 1.1
        else:
            adjustment = 1.0
        
        new_S = current_S * adjustment
        new_S = max(0.5, min(10.0, new_S))  # 限制範圍
        
        self._calibrated_decay_coefficients[user_id] = new_S
    
    def get_forgetting_curve(self, user_id: str, item_id: str) -> Optional[ForgettingCurve]:
        """獲取遺忘曲線記錄"""
        key = (user_id, item_id)
        return self._forgetting_curves.get(key)
    
    def calibrate_decay_coefficient(self, user_id: str, 
                                   review_history: List[Tuple[float, int]]) -> float:
        """
        根據歷史復習數據校準用戶的衰減係數
        
        Args:
            user_id: 用戶 ID
            review_history: [(days_elapsed, quality_score), ...]
        
        Returns:
            float: 校準後的衰減係數
        """
        if len(review_history) < 5:
            # 數據不足，使用默認值
            return self._get_user_decay_coefficient(user_id)
        
        # 使用最小二乘法擬合 S 參數
        # R = e^(-t/S)，假設質量評分與保留率線性相關：R ≈ quality/5
        
        total_error = 0.0
        best_S = 2.5
        
        for S_test in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]:
            error = 0.0
            for days, quality in review_history:
                predicted_R = EbbinghausModel.retention_rate(days, S_test)
                actual_R = quality / 5.0
                error += (predicted_R - actual_R) ** 2
            
            if error < total_error or best_S == 2.5:
                total_error = error
                best_S = S_test
        
        self._calibrated_decay_coefficients[user_id] = best_S
        return best_S
    
    def get_review_statistics(self, user_id: str) -> Dict:
        """
        獲取用戶復習統計
        
        Args:
            user_id: 用戶 ID
        
        Returns:
            Dict: 統計數據
        """
        total_items = 0
        total_reviews = 0
        avg_retention = 0.0
        due_count = 0
        
        for (uid, item_id), curve in self._forgetting_curves.items():
            if uid != user_id:
                continue
            
            total_items += 1
            total_reviews += len(curve.reviews)
            avg_retention += self._calculate_current_retention(curve)
            
            if curve.next_review <= datetime.now():
                due_count += 1
        
        if total_items > 0:
            avg_retention /= total_items
        
        return {
            "total_items": total_items,
            "total_reviews": total_reviews,
            "avg_retention_rate": round(avg_retention, 3),
            "due_items": due_count,
            "calibrated_decay_coefficient": self._get_user_decay_coefficient(user_id)
        }


# 全局服務實例
_service_instance: Optional[ForgettingCurveService] = None


def get_service() -> ForgettingCurveService:
    """獲取遺忘曲線服務單例"""
    global _service_instance
    if _service_instance is None:
        _service_instance = ForgettingCurveService()
    return _service_instance


if __name__ == "__main__":
    # 測試示例
    service = ForgettingCurveService()
    
    # 1. 學習新知識點
    print("=== 學習新知識點 ===")
    curve = service.learn_item("user_001", "item_001", quality_score=5)
    print(f"學習時間：{curve.learned_at}")
    print(f"下次復習：{curve.next_review}")
    print(f"初始間隔：{curve.interval_days} 天")
    
    # 2. 模擬復習
    print("\n=== 模擬復習 ===")
    for i in range(5):
        # 模擬時間流逝
        import time
        time.sleep(0.1)  # 僅用於演示
        
        quality = 4 if i < 4 else 2  # 最後一次遺忘
        curve = service.review_item("user_001", "item_001", quality_score=quality)
        print(f"復習 {i+1}: 質量={quality}, 下次間隔={curve.interval_days:.1f}天, EF={curve.ease_factor:.2f}")
    
    # 3. 獲取待復習項目
    print("\n=== 待復習項目 ===")
    due_items = service.get_due_items("user_001")
    print(f"待復習：{len(due_items)} 項")
    
    # 4. 獲取統計
    print("\n=== 復習統計 ===")
    stats = service.get_review_statistics("user_001")
    print(f"總知識點：{stats['total_items']}")
    print(f"總復習次數：{stats['total_reviews']}")
    print(f"平均保留率：{stats['avg_retention_rate']:.1%}")
    
    # 5. Ebbinghaus 模型測試
    print("\n=== Ebbinghaus 模型測試 ===")
    for t in [1, 3, 7, 14, 30]:
        R = EbbinghausModel.retention_rate(t, S=2.5)
        print(f"  {t}天後保留率：{R:.1%}")
