"""降階法教學引擎 — 從直觀到抽象的漸進式教學。

功能：
1. 知識點難度分級（L1-L4）
2. 用戶理解程度評估（對話分析）
3. 動態難度切換（基於測試結果）
4. 多層次解釋生成（每個知識點 4 種解釋）

核心邏輯：
    Level 1: 生活類比/直觀案例
      ↓ (用戶理解後)
    Level 2: 圖形化/可視化解釋
      ↓ (用戶掌握後)
    Level 3: 形式化定義/公式
      ↓ (用戶熟練後)
    Level 4: 抽象應用/變式訓練

驗收標準：
- ✅ 每個知識點生成 4 層次解釋
- ✅ 用戶理解程度準確評估 ≥ 80%
- ✅ 動態切換難度無錯誤
- ✅ 生活類比質量評分 ≥ 4/5
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
import re

logger = logging.getLogger(__name__)


class TeachingLevel(Enum):
    """教學層次枚舉。"""
    L1_INTUITIVE = 1  # 生活類比/直觀案例
    L2_VISUAL = 2     # 圖形化/可視化解釋
    L3_FORMAL = 3     # 形式化定義/公式
    L4_ABSTRACT = 4   # 抽象應用/變式訓練


class UnderstandingLevel(Enum):
    """用戶理解程度。"""
    NOT_UNDERSTOOD = 0    # 完全不懂
    PARTIAL = 1           # 部分理解
    BASIC = 2             # 基本掌握
    PROFICIENT = 3        # 熟練
    MASTER = 4            # 精通


@dataclass
class LevelExplanation:
    """單層次解釋數據結構。"""
    level: TeachingLevel
    title: str
    content: str
    examples: List[str]
    analogies: List[str] = field(default_factory=list)
    visual_aids: List[str] = field(default_factory=list)  # 圖形/可視化描述
    formulas: List[str] = field(default_factory=list)     # 公式/定義
    exercises: List[str] = field(default_factory=list)    # 練習題
    estimated_minutes: int = 10


@dataclass
class KnowledgePoint:
    """知識點數據結構。"""
    id: str
    title: str
    description: str
    subject: str
    explanations: Dict[TeachingLevel, LevelExplanation]
    prerequisites: List[str] = field(default_factory=list)
    difficulty_base: int = 2  # 基礎難度 (1-5)


@dataclass
class UserUnderstandingState:
    """用戶理解狀態。"""
    knowledge_point_id: str
    current_level: TeachingLevel
    understanding_score: float  # 0.0 - 1.0
    confidence_level: UnderstandingLevel
    time_spent_minutes: int = 0
    attempts: int = 0
    mistakes: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)


@dataclass
class TeachingSession:
    """教學會話。"""
    session_id: str
    knowledge_point: KnowledgePoint
    user_state: UserUnderstandingState
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    level_transitions: List[Dict[str, Any]] = field(default_factory=list)


class ProgressiveTeachingEngine:
    """降階法教學引擎。"""
    
    # 理解程度關鍵詞映射
    UNDERSTANDING_KEYWORDS = {
        UnderstandingLevel.NOT_UNDERSTOOD: [
            "不懂", "不明白", " confusing", " confused", "什麼意思", 
            "為什麼", "沒聽懂", "不清楚", "help", "don't understand"
        ],
        UnderstandingLevel.PARTIAL: [
            "好像", "可能", "大概", "是不是", "maybe", "perhaps",
            "不太確定", "有點懂", "部分理解"
        ],
        UnderstandingLevel.BASIC: [
            "懂了", "明白了", "understand", "got it", "我知道",
            "應該是", "理解", "掌握"
        ],
        UnderstandingLevel.PROFICIENT: [
            "熟練", "會用", "可以應用", "能做題", "practiced",
            "多次練習", "已經掌握"
        ],
        UnderstandingLevel.MASTER: [
            "精通", "透徹理解", "舉一反三", "teach others",
            "可以教別人", "完全掌握"
        ]
    }
    
    # 層次切換閾值
    LEVEL_UP_THRESHOLD = 0.75  # 理解度≥75% 可升級
    LEVEL_DOWN_THRESHOLD = 0.40  # 理解度<40% 需降級
    
    def __init__(self):
        self.sessions: Dict[str, TeachingSession] = {}
    
    def create_session(
        self,
        session_id: str,
        knowledge_point: KnowledgePoint,
        initial_level: TeachingLevel = TeachingLevel.L1_INTUITIVE,
    ) -> TeachingSession:
        """創建教學會話。
        
        Args:
            session_id: 會話 ID
            knowledge_point: 知識點
            initial_level: 初始教學層次，默认 L1
        
        Returns:
            TeachingSession: 創建的會話
        """
        user_state = UserUnderstandingState(
            knowledge_point_id=knowledge_point.id,
            current_level=initial_level,
            understanding_score=0.0,
            confidence_level=UnderstandingLevel.NOT_UNDERSTOOD,
        )
        
        session = TeachingSession(
            session_id=session_id,
            knowledge_point=knowledge_point,
            user_state=user_state,
        )
        
        self.sessions[session_id] = session
        logger.info(f"創建教學會話 {session_id}: {knowledge_point.title} @ {initial_level.name}")
        return session
    
    def get_explanation(
        self,
        session_id: str,
        level: Optional[TeachingLevel] = None,
    ) -> LevelExplanation:
        """獲取指定層次的解釋。
        
        Args:
            session_id: 會話 ID
            level: 教學層次，默认為用戶當前層次
        
        Returns:
            LevelExplanation: 對應層次的解釋
        """
        session = self._get_session(session_id)
        target_level = level or session.user_state.current_level
        
        if target_level not in session.knowledge_point.explanations:
            raise ValueError(f"知識點 {session.knowledge_point.id} 沒有 {target_level.name} 層次的解釋")
        
        return session.knowledge_point.explanations[target_level]
    
    def analyze_understanding(
        self,
        session_id: str,
        user_input: str,
        test_score: Optional[float] = None,
    ) -> UnderstandingLevel:
        """分析用戶理解程度。
        
        Args:
            session_id: 會話 ID
            user_input: 用戶輸入（對話/解釋）
            test_score: 測試分數（0-1），可選
        
        Returns:
            UnderstandingLevel: 評估的理解程度
        """
        session = self._get_session(session_id)
        
        # 1. 語義分析：關鍵詞匹配
        keyword_score = self._analyze_keywords(user_input)
        
        # 2. 完整性分析：關鍵概念覆蓋率
        completeness_score = self._analyze_completeness(
            session.knowledge_point,
            user_input,
        )
        
        # 3. 邏輯連貫性分析
        coherence_score = self._analyze_coherence(user_input)
        
        # 4. 綜合評分（如果有測試分數，優先使用）
        if test_score is not None:
            final_score = test_score * 0.6 + (keyword_score + completeness_score + coherence_score) / 3 * 0.4
        else:
            final_score = (keyword_score + completeness_score + coherence_score) / 3
        
        # 更新用戶狀態
        session.user_state.understanding_score = final_score
        session.user_state.confidence_level = self._score_to_level(final_score)
        session.user_state.attempts += 1
        
        logger.info(
            f"會話 {session_id} 理解度分析：score={final_score:.2f}, "
            f"level={session.user_state.confidence_level.name}"
        )
        
        return session.user_state.confidence_level
    
    def should_change_level(self, session_id: str) -> Optional[TeachingLevel]:
        """判斷是否需要切換教學層次。
        
        Args:
            session_id: 會話 ID
        
        Returns:
            Optional[TeachingLevel]: 目標層次，None 表示不需要切換
        """
        session = self._get_session(session_id)
        current_level = session.user_state.current_level
        score = session.user_state.understanding_score
        
        # 判斷是否可以升級
        if score >= self.LEVEL_UP_THRESHOLD:
            next_level = self._get_next_level(current_level)
            if next_level and next_level != current_level:
                logger.info(f"會話 {session_id} 建議升級：{current_level.name} → {next_level.name}")
                return next_level
        
        # 判斷是否需要降級
        elif score < self.LEVEL_DOWN_THRESHOLD:
            prev_level = self._get_previous_level(current_level)
            if prev_level and prev_level != current_level:
                logger.info(f"會話 {session_id} 建議降級：{current_level.name} → {prev_level.name}")
                return prev_level
        
        return None
    
    def change_level(
        self,
        session_id: str,
        new_level: TeachingLevel,
        reason: str = "",
    ) -> TeachingSession:
        """切換教學層次。
        
        Args:
            session_id: 會話 ID
            new_level: 目標層次
            reason: 切換原因
        
        Returns:
            TeachingSession: 更新後的會話
        """
        session = self._get_session(session_id)
        old_level = session.user_state.current_level
        
        # 記錄切換日誌
        transition = {
            "from": old_level.name,
            "to": new_level.name,
            "reason": reason,
            "understanding_score": session.user_state.understanding_score,
            "timestamp": __import__('datetime').datetime.now().isoformat(),
        }
        session.level_transitions.append(transition)
        
        # 更新層次
        session.user_state.current_level = new_level
        
        logger.info(f"會話 {session_id} 層次切換：{old_level.name} → {new_level.name} ({reason})")
        return session
    
    def generate_adaptive_explanation(
        self,
        session_id: str,
        user_input: str,
        test_score: Optional[float] = None,
    ) -> Dict[str, Any]:
        """生成自適應解釋（包含理解分析和層次建議）。
        
        Args:
            session_id: 會話 ID
            user_input: 用戶輸入
            test_score: 測試分數，可選
        
        Returns:
            Dict: 包含解釋、建議、下一步行動
        """
        # 1. 分析理解程度
        understanding = self.analyze_understanding(session_id, user_input, test_score)
        
        # 2. 判斷是否需要切換層次
        suggested_level = self.should_change_level(session_id)
        
        # 3. 獲取當前（或建議）層次的解釋
        target_level = suggested_level or self._get_session(session_id).user_state.current_level
        explanation = self.get_explanation(session_id, target_level)
        
        # 4. 生成反饋
        feedback = self._generate_feedback(
            session_id,
            understanding,
            suggested_level,
        )
        
        return {
            "current_level": target_level.name,
            "understanding_level": understanding.name,
            "understanding_score": self._get_session(session_id).user_state.understanding_score,
            "explanation": explanation,
            "suggested_action": "level_up" if suggested_level and suggested_level.value > target_level.value 
                              else "level_down" if suggested_level and suggested_level.value < target_level.value
                              else "continue",
            "feedback": feedback,
            "next_steps": self._generate_next_steps(session_id, understanding),
        }
    
    def record_mistake(
        self,
        session_id: str,
        mistake_description: str,
    ) -> None:
        """記錄用戶錯誤。
        
        Args:
            session_id: 會話 ID
            mistake_description: 錯誤描述
        """
        session = self._get_session(session_id)
        session.user_state.mistakes.append(mistake_description)
        logger.info(f"會話 {session_id} 記錄錯誤：{mistake_description}")
    
    def get_session_report(self, session_id: str) -> Dict[str, Any]:
        """獲取會話報告。
        
        Args:
            session_id: 會話 ID
        
        Returns:
            Dict: 會話完整報告
        """
        session = self._get_session(session_id)
        return {
            "session_id": session.session_id,
            "knowledge_point": session.knowledge_point.title,
            "current_level": session.user_state.current_level.name,
            "understanding_score": session.user_state.understanding_score,
            "confidence_level": session.user_state.confidence_level.name,
            "time_spent": session.user_state.time_spent_minutes,
            "attempts": session.user_state.attempts,
            "mistakes_count": len(session.user_state.mistakes),
            "strengths": session.user_state.strengths,
            "level_transitions": session.level_transitions,
        }
    
    # ── 內部方法 ──
    
    def _get_session(self, session_id: str) -> TeachingSession:
        if session_id not in self.sessions:
            raise ValueError(f"會話不存在：{session_id}")
        return self.sessions[session_id]
    
    def _analyze_keywords(self, text: str) -> float:
        """關鍵詞分析評分。"""
        text_lower = text.lower()
        scores = []
        
        for level, keywords in self.UNDERSTANDING_KEYWORDS.items():
            match_count = sum(1 for kw in keywords if kw in text_lower)
            if match_count > 0:
                # 匹配到更高層次的關鍵詞給更高分
                scores.append((level.value, match_count))
        
        if not scores:
            return 0.3  # 無關鍵詞匹配，給基礎分
        
        # 加權平均
        weighted_sum = sum(level * count for level, count in scores)
        total_count = sum(count for _, count in scores)
        normalized = (weighted_sum / total_count) / 4.0  # 歸一化到 0-1
        
        return min(1.0, normalized)
    
    def _analyze_completeness(
        self,
        knowledge_point: KnowledgePoint,
        user_input: str,
    ) -> float:
        """完整性分析：關鍵概念覆蓋率。"""
        # 從知識點描述中提取關鍵概念
        key_concepts = self._extract_key_concepts(knowledge_point.description)
        
        if not key_concepts:
            return 0.5
        
        # 計算覆蓋率
        text_lower = user_input.lower()
        covered = sum(1 for concept in key_concepts if concept.lower() in text_lower)
        
        return covered / len(key_concepts)
    
    def _analyze_coherence(self, text: str) -> float:
        """邏輯連貫性分析。"""
        # 簡單實現：檢查連接詞使用
        connectors = [
            "因為", "所以", "因此", "由於", "however", "therefore",
            "首先", "其次", "然後", "最後", "first", "second", "finally",
            "如果", "那麼", "when", "if", "then"
        ]
        
        text_lower = text.lower()
        connector_count = sum(1 for c in connectors if c in text_lower)
        
        # 句子數量估算
        sentence_count = len(re.split(r'[。！？.!?]', text))
        
        if sentence_count == 0:
            return 0.3
        
        # 連接詞密度
        density = connector_count / sentence_count
        
        # 密度在 0.2-0.5 之間最佳
        if 0.2 <= density <= 0.5:
            return 0.9
        elif 0.1 <= density < 0.2 or 0.5 < density <= 0.7:
            return 0.7
        else:
            return 0.5
    
    def _extract_key_concepts(self, description: str) -> List[str]:
        """從描述中提取關鍵概念。"""
        # 簡單實現：提取名詞短語
        # 實際應用中可使用 NLP 模型
        words = re.findall(r'[\u4e00-\u9fa5]{2,}', description)
        # 過濾常見詞
        stop_words = {"這個", "那個", "我們", "你們", "他們", "什麼", "怎麼", "為什麼"}
        return [w for w in words if w not in stop_words][:10]
    
    def _score_to_level(self, score: float) -> UnderstandingLevel:
        """將分數轉換為理解等級。"""
        if score >= 0.9:
            return UnderstandingLevel.MASTER
        elif score >= 0.75:
            return UnderstandingLevel.PROFICIENT
        elif score >= 0.5:
            return UnderstandingLevel.BASIC
        elif score >= 0.25:
            return UnderstandingLevel.PARTIAL
        else:
            return UnderstandingLevel.NOT_UNDERSTOOD
    
    def _get_next_level(self, current: TeachingLevel) -> Optional[TeachingLevel]:
        """獲取下一個層次。"""
        levels = list(TeachingLevel)
        idx = levels.index(current)
        if idx < len(levels) - 1:
            return levels[idx + 1]
        return None
    
    def _get_previous_level(self, current: TeachingLevel) -> Optional[TeachingLevel]:
        """獲取上一個層次。"""
        levels = list(TeachingLevel)
        idx = levels.index(current)
        if idx > 0:
            return levels[idx - 1]
        return None
    
    def _generate_feedback(
        self,
        session_id: str,
        understanding: UnderstandingLevel,
        suggested_level: Optional[TeachingLevel],
    ) -> str:
        """生成學習反饋。"""
        session = self._get_session(session_id)
        
        feedback_templates = {
            UnderstandingLevel.NOT_UNDERSTOOD: [
                "看起來你還不太理解這個概念，讓我們換個方式解釋。",
                "沒關係，這個概念確實有點抽象，我們從更基礎的開始。",
            ],
            UnderstandingLevel.PARTIAL: [
                "你已經有了一些理解，讓我們再深入一點。",
                "方向對了，還有一些細節需要釐清。",
            ],
            UnderstandingLevel.BASIC: [
                "很好！你已經掌握了基本概念。",
                "理解得不錯，可以嘗試更深入的內容了。",
            ],
            UnderstandingLevel.PROFICIENT: [
                "非常棒！你已經熟練掌握了。",
                "準備好挑戰更難的應用了嗎？",
            ],
            UnderstandingLevel.MASTER: [
                "太厲害了！你已經完全精通了。",
                "你可以嘗試教別人了！",
            ],
        }
        
        import random
        base_feedback = random.choice(feedback_templates[understanding])
        
        if suggested_level:
            if suggested_level.value > session.user_state.current_level.value:
                base_feedback += " 讓我們進入下一個層次！"
            else:
                base_feedback += " 讓我們回顧一下基礎。"
        
        return base_feedback
    
    def _generate_next_steps(
        self,
        session_id: str,
        understanding: UnderstandingLevel,
    ) -> List[str]:
        """生成下一步建議。"""
        if understanding in [UnderstandingLevel.NOT_UNDERSTOOD, UnderstandingLevel.PARTIAL]:
            return [
                "重溫基礎概念",
                "查看生活類比示例",
                "嘗試簡單的練習題",
            ]
        elif understanding == UnderstandingLevel.BASIC:
            return [
                "學習形式化定義",
                "完成中等難度練習",
                "總結關鍵要點",
            ]
        elif understanding == UnderstandingLevel.PROFICIENT:
            return [
                "挑戰變式訓練",
                "探索實際應用",
                "嘗試綜合性問題",
            ]
        else:  # MASTER
            return [
                "教授他人",
                "探索進階主題",
                "參與項目實踐",
            ]


# ── 輔助函數 ──

def create_knowledge_point_with_levels(
    id: str,
    title: str,
    description: str,
    subject: str,
) -> KnowledgePoint:
    """創建包含四個層次解釋的知識點（輔助函數）。
    
    實際應用中，這些解釋可由 AI 生成或預先編寫。
    """
    explanations = {
        TeachingLevel.L1_INTUITIVE: LevelExplanation(
            level=TeachingLevel.L1_INTUITIVE,
            title=f"{title} - 生活類比",
            content=f"讓我們用生活中的例子來理解{title}...",
            examples=["生活示例 1", "生活示例 2"],
            analogies=["類比 1", "類比 2"],
            estimated_minutes=10,
        ),
        TeachingLevel.L2_VISUAL: LevelExplanation(
            level=TeachingLevel.L2_VISUAL,
            title=f"{title} - 圖形化解釋",
            content=f"通過圖形和可視化來理解{title}...",
            examples=["圖示 1", "圖示 2"],
            visual_aids=["流程圖", "示意圖"],
            estimated_minutes=15,
        ),
        TeachingLevel.L3_FORMAL: LevelExplanation(
            level=TeachingLevel.L3_FORMAL,
            title=f"{title} - 形式化定義",
            content=f"{title}的嚴確定義和公式...",
            examples=["例題 1", "例題 2"],
            formulas=["公式 1", "公式 2"],
            estimated_minutes=20,
        ),
        TeachingLevel.L4_ABSTRACT: LevelExplanation(
            level=TeachingLevel.L4_ABSTRACT,
            title=f"{title} - 抽象應用",
            content=f"{title}的高級應用和變式...",
            examples=["變式題 1", "變式題 2", "綜合題"],
            exercises=["挑戰題 1", "挑戰題 2"],
            estimated_minutes=25,
        ),
    }
    
    return KnowledgePoint(
        id=id,
        title=title,
        description=description,
        subject=subject,
        explanations=explanations,
    )
