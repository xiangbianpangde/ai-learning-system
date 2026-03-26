"""
學習風格識別服務 (Learning Style Identification Service)

Phase 2 P0 功能 - Week 1
技術方案：VARK 問卷 (12 題) + 行為分析
驗收標準：識別準確率 ≥ 75%

功能：
1. VARK 問卷評估（12 題標準化評估）
2. 行為數據追蹤（內容類型點擊率、停留時長、互動深度）
3. 評分算法（問卷 60% + 行為 40% 加權）
4. 推薦引擎（根據主導風格推薦內容）
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json


class VARKStyle(Enum):
    """VARK 四種學習風格"""
    VISUAL = "V"  # 視覺型
    AUDITORY = "A"  # 聽覺型
    READ_WRITE = "R"  # 閱讀型
    KINESTHETIC = "K"  # 動手型


@dataclass
class LearningStyle:
    """用戶學習風格數據結構"""
    user_id: str
    v_score: float = 0.0  # Visual 0-100
    a_score: float = 0.0  # Auditory 0-100
    r_score: float = 0.0  # Read/Write 0-100
    k_score: float = 0.0  # Kinesthetic 0-100
    dominant_style: str = ""  # V/A/R/K
    confidence: float = 0.0  # 0-1
    questionnaire_completed: bool = False
    behavior_data_collected: bool = False
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "v_score": round(self.v_score, 2),
            "a_score": round(self.a_score, 2),
            "r_score": round(self.r_score, 2),
            "k_score": round(self.k_score, 2),
            "dominant_style": self.dominant_style,
            "confidence": round(self.confidence, 2),
            "questionnaire_completed": self.questionnaire_completed,
            "behavior_data_collected": self.behavior_data_collected,
            "last_updated": self.last_updated.isoformat()
        }


@dataclass
class BehaviorData:
    """用戶行為數據"""
    user_id: str
    visual_clicks: int = 0  # 視頻/圖表點擊次數
    auditory_clicks: int = 0  # 音頻點擊次數
    read_clicks: int = 0  # 文本點擊次數
    kinesthetic_clicks: int = 0  # 實踐/互動點擊次數
    visual_time: float = 0.0  # 視覺內容停留時長（秒）
    auditory_time: float = 0.0  # 聽覺內容停留時長（秒）
    read_time: float = 0.0  # 閱讀內容停留時長（秒）
    kinesthetic_time: float = 0.0  # 實踐內容停留時長（秒）
    visual_interactions: int = 0  # 視覺內容互動深度
    auditory_interactions: int = 0  # 聽覺內容互動深度
    read_interactions: int = 0  # 閱讀內容互動深度
    kinesthetic_interactions: int = 0  # 實踐內容互動深度
    
    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "clicks": {
                "visual": self.visual_clicks,
                "auditory": self.auditory_clicks,
                "read": self.read_clicks,
                "kinesthetic": self.kinesthetic_clicks
            },
            "time_spent": {
                "visual": round(self.visual_time, 2),
                "auditory": round(self.auditory_time, 2),
                "read": round(self.read_time, 2),
                "kinesthetic": round(self.kinesthetic_time, 2)
            },
            "interactions": {
                "visual": self.visual_interactions,
                "auditory": self.auditory_interactions,
                "read": self.read_interactions,
                "kinesthetic": self.kinesthetic_interactions
            }
        }


# VARK 問卷題目庫（12 題標準化評估）
VARK_QUESTIONS = [
    {
        "id": "q1",
        "content": "當你學習新知識時，你更喜歡：",
        "options": [
            {"text": "看圖表、圖像或視頻", "style": "V"},
            {"text": "聽講解或討論", "style": "A"},
            {"text": "閱讀文字說明", "style": "R"},
            {"text": "動手實踐或操作", "style": "K"}
        ]
    },
    {
        "id": "q2",
        "content": "你需要記住一個新概念時，你會：",
        "options": [
            {"text": "在腦海中想像它的圖像", "style": "V"},
            {"text": "反覆朗讀或聽錄音", "style": "A"},
            {"text": "寫下筆記或列表", "style": "R"},
            {"text": "通過實際應用來記憶", "style": "K"}
        ]
    },
    {
        "id": "q3",
        "content": "當你不理解某個說明時，你會：",
        "options": [
            {"text": "尋找示意圖或流程圖", "style": "V"},
            {"text": "請別人講解給你聽", "style": "A"},
            {"text": "閱讀更詳細的文字說明", "style": "R"},
            {"text": "自己動手試試看", "style": "K"}
        ]
    },
    {
        "id": "q4",
        "content": "你喜歡的學習材料形式是：",
        "options": [
            {"text": "視頻、動畫或圖表", "style": "V"},
            {"text": "播客、錄音或講座", "style": "A"},
            {"text": "文章、書籍或文檔", "style": "R"},
            {"text": "實驗、練習或項目", "style": "K"}
        ]
    },
    {
        "id": "q5",
        "content": "當你需要學習使用新軟件時，你會：",
        "options": [
            {"text": "看界面圖標和視覺提示", "style": "V"},
            {"text": "聽別人講解或看視頻教程", "style": "A"},
            {"text": "閱讀使用手冊或說明文檔", "style": "R"},
            {"text": "直接打開軟件嘗試操作", "style": "K"}
        ]
    },
    {
        "id": "q6",
        "content": "你認為最有效的複習方式是：",
        "options": [
            {"text": "看思維導圖或圖表總結", "style": "V"},
            {"text": "聽錄音或參與討論", "style": "A"},
            {"text": "重讀筆記或教材", "style": "R"},
            {"text": "做練習題或實踐項目", "style": "K"}
        ]
    },
    {
        "id": "q7",
        "content": "當你要向別人解釋一個概念時，你會：",
        "options": [
            {"text": "畫圖或用視覺輔助", "style": "V"},
            {"text": "口頭講解或討論", "style": "A"},
            {"text": "寫下詳細說明", "style": "R"},
            {"text": "示範操作過程", "style": "K"}
        ]
    },
    {
        "id": "q8",
        "content": "你喜歡的考試形式是：",
        "options": [
            {"text": "包含圖表、圖像的題目", "style": "V"},
            {"text": "口試或聽力測試", "style": "A"},
            {"text": "書面問答或論文", "style": "R"},
            {"text": "實踐操作或實驗考試", "style": "K"}
        ]
    },
    {
        "id": "q9",
        "content": "當你在閒暇時間學習時，你傾向於：",
        "options": [
            {"text": "看紀錄片或教學視頻", "style": "V"},
            {"text": "聽播客或有聲書", "style": "A"},
            {"text": "閱讀文章或書籍", "style": "R"},
            {"text": "做手工或實驗", "style": "K"}
        ]
    },
    {
        "id": "q10",
        "content": "你認為最能幫助你理解的輔助是：",
        "options": [
            {"text": "圖解、流程圖或視頻", "style": "V"},
            {"text": "講解、討論或音頻", "style": "A"},
            {"text": "文字說明、定義或列表", "style": "R"},
            {"text": "實例、練習或操作", "style": "K"}
        ]
    },
    {
        "id": "q11",
        "content": "當你要規劃一個項目時，你會：",
        "options": [
            {"text": "畫出流程圖或思維導圖", "style": "V"},
            {"text": "和別人討論想法", "style": "A"},
            {"text": "列出詳細的書面計劃", "style": "R"},
            {"text": "先開始做一部分試試", "style": "K"}
        ]
    },
    {
        "id": "q12",
        "content": "你認為最無聊的學習方式是：",
        "options": [
            {"text": "純文字講義沒有圖示", "style": "V"},
            {"text": "沒有講解只看書", "style": "A"},
            {"text": "只有視頻沒有文字總結", "style": "R"},
            {"text": "只聽不練的講座", "style": "K"}
        ]
    }
]


class LearningStyleService:
    """學習風格識別服務"""
    
    def __init__(self):
        # 模擬數據庫存儲
        self._user_styles: Dict[str, LearningStyle] = {}
        self._behavior_data: Dict[str, BehaviorData] = {}
        self._questionnaire_answers: Dict[str, List[Dict]] = {}
    
    def get_questionnaire(self) -> List[Dict]:
        """獲取 VARK 問卷題目"""
        return VARK_QUESTIONS
    
    def submit_questionnaire(self, user_id: str, answers: List[Dict]) -> LearningStyle:
        """
        提交問卷答案並計算學習風格
        
        Args:
            user_id: 用戶 ID
            answers: 答案列表 [{"question_id": "q1", "selected_option": 0}, ...]
        
        Returns:
            LearningStyle: 計算後的學習風格
        """
        if len(answers) != len(VARK_QUESTIONS):
            raise ValueError(f"問卷必須完成全部 {len(VARK_QUESTIONS)} 題")
        
        # 計算問卷得分
        style_scores = {"V": 0, "A": 0, "R": 0, "K": 0}
        
        for answer in answers:
            question_id = answer["question_id"]
            selected_option = answer["selected_option"]
            
            # 找到對應題目和選項
            question = next((q for q in VARK_QUESTIONS if q["id"] == question_id), None)
            if not question:
                raise ValueError(f"無效的題目 ID: {question_id}")
            
            if selected_option < 0 or selected_option >= len(question["options"]):
                raise ValueError(f"無效的選項索引：{selected_option}")
            
            selected_style = question["options"][selected_option]["style"]
            style_scores[selected_style] += 1
        
        # 轉換為 0-100 分數
        max_score = len(VARK_QUESTIONS)  # 12 題
        v_score = (style_scores["V"] / max_score) * 100
        a_score = (style_scores["A"] / max_score) * 100
        r_score = (style_scores["R"] / max_score) * 100
        k_score = (style_scores["K"] / max_score) * 100
        
        # 存儲答案
        self._questionnaire_answers[user_id] = answers
        
        # 創建或更新學習風格記錄
        if user_id not in self._user_styles:
            self._user_styles[user_id] = LearningStyle(user_id=user_id)
        
        style = self._user_styles[user_id]
        style.v_score = v_score
        style.a_score = a_score
        style.r_score = r_score
        style.k_score = k_score
        style.questionnaire_completed = True
        style.last_updated = datetime.now()
        
        # 更新主導風格和置信度
        self._update_dominant_style(style)
        
        return style
    
    def record_behavior(self, user_id: str, content_type: str, 
                       action: str, duration: float = 0.0) -> None:
        """
        記錄用戶行為數據
        
        Args:
            user_id: 用戶 ID
            content_type: 內容類型 (visual/auditory/read/kinesthetic)
            action: 行為類型 (click/time/interaction)
            duration: 持續時間（秒），用於 time 行為
        """
        if user_id not in self._behavior_data:
            self._behavior_data[user_id] = BehaviorData(user_id=user_id)
        
        behavior = self._behavior_data[user_id]
        
        if content_type == "visual":
            if action == "click":
                behavior.visual_clicks += 1
            elif action == "time":
                behavior.visual_time += duration
            elif action == "interaction":
                behavior.visual_interactions += 1
        elif content_type == "auditory":
            if action == "click":
                behavior.auditory_clicks += 1
            elif action == "time":
                behavior.auditory_time += duration
            elif action == "interaction":
                behavior.auditory_interactions += 1
        elif content_type == "read":
            if action == "click":
                behavior.read_clicks += 1
            elif action == "time":
                behavior.read_time += duration
            elif action == "interaction":
                behavior.read_interactions += 1
        elif content_type == "kinesthetic":
            if action == "click":
                behavior.kinesthetic_clicks += 1
            elif action == "time":
                behavior.kinesthetic_time += duration
            elif action == "interaction":
                behavior.kinesthetic_interactions += 1
    
    def calculate_behavior_scores(self, user_id: str) -> Dict[str, float]:
        """
        根據行為數據計算學習風格得分
        
        Returns:
            Dict[str, float]: {"V": score, "A": score, "R": score, "K": score}
        """
        if user_id not in self._behavior_data:
            return {"V": 25.0, "A": 25.0, "R": 25.0, "K": 25.0}
        
        behavior = self._behavior_data[user_id]
        
        # 計算每個維度的綜合得分（點擊 + 時長 + 互動）
        def calc_dimension_score(clicks: int, time: float, interactions: int) -> float:
            # 標準化：假設典型用戶每個維度約 10 次點擊、1000 秒時長、5 次互動
            click_score = min(clicks / 10, 1.0) * 40  # 40% 權重
            time_score = min(time / 1000, 1.0) * 40  # 40% 權重
            interaction_score = min(interactions / 5, 1.0) * 20  # 20% 權重
            return (click_score + time_score + interaction_score) * 100
        
        v_score = calc_dimension_score(
            behavior.visual_clicks, behavior.visual_time, behavior.visual_interactions
        )
        a_score = calc_dimension_score(
            behavior.auditory_clicks, behavior.auditory_time, behavior.auditory_interactions
        )
        r_score = calc_dimension_score(
            behavior.read_clicks, behavior.read_time, behavior.read_interactions
        )
        k_score = calc_dimension_score(
            behavior.kinesthetic_clicks, behavior.kinesthetic_time, behavior.kinesthetic_interactions
        )
        
        # 歸一化使總和為 100
        total = v_score + a_score + r_score + k_score
        if total > 0:
            v_score = (v_score / total) * 100
            a_score = (a_score / total) * 100
            r_score = (r_score / total) * 100
            k_score = (k_score / total) * 100
        
        return {"V": v_score, "A": a_score, "R": r_score, "K": k_score}
    
    def _update_dominant_style(self, style: LearningStyle) -> None:
        """更新主導風格和置信度"""
        scores = {
            "V": style.v_score,
            "A": style.a_score,
            "R": style.r_score,
            "K": style.k_score
        }
        
        # 找出最高分
        dominant = max(scores, key=scores.get)
        dominant_score = scores[dominant]
        
        style.dominant_style = dominant
        
        # 置信度計算：主導風格得分與第二高得分的差距
        sorted_scores = sorted(scores.values(), reverse=True)
        if len(sorted_scores) >= 2:
            gap = sorted_scores[0] - sorted_scores[1]
            # 差距越大置信度越高，最大為 1
            style.confidence = min(gap / 50, 1.0)
        else:
            style.confidence = 0.5
    
    def get_learning_style(self, user_id: str) -> Optional[LearningStyle]:
        """獲取用戶的學習風格"""
        return self._user_styles.get(user_id)
    
    def get_behavior_data(self, user_id: str) -> Optional[BehaviorData]:
        """獲取用戶的行為數據"""
        return self._behavior_data.get(user_id)
    
    def calculate_final_style(self, user_id: str) -> LearningStyle:
        """
        計算最終學習風格（問卷 60% + 行為 40%）
        
        Args:
            user_id: 用戶 ID
        
        Returns:
            LearningStyle: 最終學習風格
        """
        if user_id not in self._user_styles:
            raise ValueError(f"用戶 {user_id} 尚未完成問卷")
        
        style = self._user_styles[user_id]
        
        # 如果只有問卷數據，直接返回
        if user_id not in self._behavior_data:
            return style
        
        # 計算行為得分
        behavior_scores = self.calculate_behavior_scores(user_id)
        
        # 加權計算：問卷 60% + 行為 40%
        style.v_score = style.v_score * 0.6 + behavior_scores["V"] * 0.4
        style.a_score = style.a_score * 0.6 + behavior_scores["A"] * 0.4
        style.r_score = style.r_score * 0.6 + behavior_scores["R"] * 0.4
        style.k_score = style.k_score * 0.6 + behavior_scores["K"] * 0.4
        
        style.behavior_data_collected = True
        style.last_updated = datetime.now()
        
        # 重新計算主導風格和置信度
        self._update_dominant_style(style)
        
        return style
    
    def recommend_content(self, user_id: str, content_pool: List[Dict]) -> List[Dict]:
        """
        根據學習風格推薦內容
        
        Args:
            user_id: 用戶 ID
            content_pool: 內容池 [{"id": "1", "type": "video", "tags": [...]}, ...]
        
        Returns:
            List[Dict]: 推薦內容列表（按相關性排序）
        """
        if user_id not in self._user_styles:
            # 未識別風格，返回原始順序
            return content_pool
        
        style = self._user_styles[user_id]
        
        # 內容類型映射到 VARK 風格
        type_mapping = {
            "video": "V", "image": "V", "diagram": "V", "infographic": "V",
            "audio": "A", "podcast": "A", "lecture": "A", "discussion": "A",
            "text": "R", "article": "R", "book": "R", "document": "R",
            "practice": "K", "exercise": "K", "project": "K", "lab": "K", "interactive": "K"
        }
        
        # 風格得分映射
        style_scores = {
            "V": style.v_score,
            "A": style.a_score,
            "R": style.r_score,
            "K": style.k_score
        }
        
        # 計算每個內容的推薦分數
        scored_content = []
        for content in content_pool:
            content_type = content.get("type", "").lower()
            content_style = type_mapping.get(content_type, "R")  # 默認閱讀型
            
            # 基礎分數：匹配用戶主導風格
            base_score = style_scores.get(content_style, 25)
            
            # 標籤匹配加分
            tag_bonus = 0
            if "tags" in content and style.dominant_style:
                style_keywords = {
                    "V": ["visual", "圖", "視頻", "image", "chart"],
                    "A": ["audio", "聽", "聲音", "sound", "podcast"],
                    "R": ["text", "閱讀", "文字", "read", "article"],
                    "K": ["practice", "實踐", "操作", "hands-on", "exercise"]
                }
                keywords = style_keywords.get(style.dominant_style, [])
                for tag in content["tags"]:
                    if any(kw in tag.lower() for kw in keywords):
                        tag_bonus += 10
            
            final_score = base_score + tag_bonus
            scored_content.append({
                **content,
                "recommendation_score": round(final_score, 2),
                "matched_style": content_style
            })
        
        # 按分數降序排序
        scored_content.sort(key=lambda x: x["recommendation_score"], reverse=True)
        
        return scored_content


# 全局服務實例
_service_instance: Optional[LearningStyleService] = None


def get_service() -> LearningStyleService:
    """獲取學習風格服務單例"""
    global _service_instance
    if _service_instance is None:
        _service_instance = LearningStyleService()
    return _service_instance


if __name__ == "__main__":
    # 測試示例
    service = LearningStyleService()
    
    # 1. 獲取問卷
    print("=== VARK 問卷 ===")
    questions = service.get_questionnaire()
    print(f"共 {len(questions)} 題")
    
    # 2. 模擬提交問卷（假設用戶偏好視覺型）
    print("\n=== 提交問卷 ===")
    test_answers = [
        {"question_id": q["id"], "selected_option": 0}  # 都選第一個選項（V 風格）
        for q in questions
    ]
    
    style = service.submit_questionnaire("user_001", test_answers)
    print(f"主導風格：{style.dominant_style}")
    print(f"得分：V={style.v_score:.1f}, A={style.a_score:.1f}, R={style.r_score:.1f}, K={style.k_score:.1f}")
    print(f"置信度：{style.confidence:.2f}")
    
    # 3. 模擬行為數據
    print("\n=== 記錄行為 ===")
    service.record_behavior("user_001", "visual", "click")
    service.record_behavior("user_001", "visual", "time", 120.0)
    service.record_behavior("user_001", "visual", "interaction")
    service.record_behavior("user_001", "read", "click")
    
    # 4. 計算最終風格
    print("\n=== 最終風格（問卷 60% + 行為 40%）===")
    final_style = service.calculate_final_style("user_001")
    print(f"主導風格：{final_style.dominant_style}")
    print(f"得分：V={final_style.v_score:.1f}, A={final_style.a_score:.1f}, R={final_style.r_score:.1f}, K={final_style.k_score:.1f}")
    
    # 5. 內容推薦
    print("\n=== 內容推薦 ===")
    content_pool = [
        {"id": "1", "type": "video", "tags": ["tutorial", "visual"]},
        {"id": "2", "type": "article", "tags": ["theory", "text"]},
        {"id": "3", "type": "practice", "tags": ["exercise", "hands-on"]},
        {"id": "4", "type": "podcast", "tags": ["discussion", "audio"]},
    ]
    recommendations = service.recommend_content("user_001", content_pool)
    for rec in recommendations:
        print(f"  {rec['id']}: {rec['type']} (score={rec['recommendation_score']}, style={rec['matched_style']})")
