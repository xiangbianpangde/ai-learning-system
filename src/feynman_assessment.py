"""費曼學習法檢測 — 讓用戶解釋概念，AI 評估理解程度。

功能：
1. 用戶輸入語義分析
2. 關鍵概念覆蓋率檢測
3. 邏輯連貫性評估
4. 知識盲點識別與反饋
5. 引導式追問（蘇格拉底式對話）

核心邏輯：
    用戶嘗試解釋 → AI 分析完整性/準確性 → 發現知識盲點 → 針對性補充

驗收標準：
- ✅ 關鍵概念覆蓋率檢測準確 ≥ 85%
- ✅ 知識盲點識別準確 ≥ 80%
- ✅ 引導式追問自然流暢
- ✅ 用戶反饋評分 ≥ 4/5
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple
import re
from datetime import datetime

logger = logging.getLogger(__name__)


class AssessmentDimension(Enum):
    """評估維度。"""
    COMPLETENESS = "completeness"      # 完整性
    ACCURACY = "accuracy"              # 準確性
    COHERENCE = "coherence"            # 連貫性
    DEPTH = "depth"                    # 深度
    CLARITY = "clarity"                # 清晰度


class BlindSpotType(Enum):
    """知識盲點類型。"""
    MISSING_CONCEPT = "missing_concept"       # 缺少關鍵概念
    MISUNDERSTANDING = "misunderstanding"     # 概念誤解
    LOGIC_GAP = "logic_gap"                   # 邏輯斷層
    OVERSIMPLIFICATION = "oversimplification" # 過度簡化
    CONFUSION = "confusion"                   # 概念混淆


@dataclass
class ConceptCoverage:
    """概念覆蓋率分析結果。"""
    total_concepts: int
    covered_concepts: int
    missing_concepts: List[str]
    coverage_rate: float  # 0.0 - 1.0


@dataclass
class BlindSpot:
    """知識盲點。"""
    blind_spot_type: BlindSpotType
    concept: str
    description: str
    severity: str  # "high", "medium", "low"
    evidence: str  # 用戶輸入中的證據
    suggestion: str  # 改進建議


@dataclass
class AssessmentResult:
    """費曼評估結果。"""
    session_id: str
    concept_id: str
    user_explanation: str
    timestamp: str
    
    # 各維度評分 (0.0 - 1.0)
    scores: Dict[AssessmentDimension, float]
    overall_score: float
    
    # 分析結果
    concept_coverage: ConceptCoverage
    blind_spots: List[BlindSpot]
    
    # 反饋
    feedback: str
    follow_up_questions: List[str]
    recommended_actions: List[str]


@dataclass
class FeynmanSession:
    """費曼學習會話。"""
    session_id: str
    concept_id: str
    concept_title: str
    concept_definition: str
    key_concepts: List[str]  # 關鍵概念列表
    assessments: List[AssessmentResult] = field(default_factory=list)
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    improvement_trend: List[float] = field(default_factory=list)


class FeynmanAssessmentEngine:
    """費曼學習法檢測引擎。"""
    
    # 邏輯連接詞（用於連貫性分析）
    LOGIC_CONNECTORS = {
        "cause": ["因為", "由於", "because", "since", "as"],
        "effect": ["所以", "因此", "於是", "therefore", "thus", "consequently"],
        "contrast": ["但是", "然而", "不過", "but", "however", "although"],
        "sequence": ["首先", "然後", "接著", "最後", "first", "then", "next", "finally"],
        "condition": ["如果", "假如", "只要", "if", "when", "unless"],
        "example": ["例如", "比如", "譬如", "for example", "such as"],
    }
    
    # 模糊表達（可能表示理解不清晰）
    VAGUE_EXPRESSIONS = [
        "好像", "可能", "也許", "大概", "差不多",
        "maybe", "perhaps", "kind of", "sort of", "i think",
        "應該", "應該吧", "我不確定", "i'm not sure"
    ]
    
    # 評估閾值
    HIGH_QUALITY_THRESHOLD = 0.85
    MEDIUM_QUALITY_THRESHOLD = 0.60
    
    def __init__(self):
        self.sessions: Dict[str, FeynmanSession] = {}
    
    def create_session(
        self,
        session_id: str,
        concept_id: str,
        concept_title: str,
        concept_definition: str,
        key_concepts: List[str],
    ) -> FeynmanSession:
        """創建費曼學習會話。
        
        Args:
            session_id: 會話 ID
            concept_id: 概念 ID
            concept_title: 概念標題
            concept_definition: 概念定義（標準答案）
            key_concepts: 關鍵概念列表
        
        Returns:
            FeynmanSession: 創建的會話
        """
        session = FeynmanSession(
            session_id=session_id,
            concept_id=concept_id,
            concept_title=concept_title,
            concept_definition=concept_definition,
            key_concepts=key_concepts,
        )
        
        self.sessions[session_id] = session
        logger.info(f"創建費曼會話 {session_id}: {concept_title}")
        return session
    
    def assess_explanation(
        self,
        session_id: str,
        user_explanation: str,
    ) -> AssessmentResult:
        """評估用戶的解釋。
        
        Args:
            session_id: 會話 ID
            user_explanation: 用戶的解釋文本
        
        Returns:
            AssessmentResult: 評估結果
        """
        session = self._get_session(session_id)
        
        # 1. 概念覆蓋率分析
        concept_coverage = self._analyze_concept_coverage(
            session.key_concepts,
            user_explanation,
        )
        
        # 2. 各維度評分
        scores = {
            AssessmentDimension.COMPLETENESS: self._score_completeness(concept_coverage),
            AssessmentDimension.ACCURACY: self._score_accuracy(
                session.concept_definition,
                user_explanation,
            ),
            AssessmentDimension.COHERENCE: self._score_coherence(user_explanation),
            AssessmentDimension.DEPTH: self._score_depth(user_explanation),
            AssessmentDimension.CLARITY: self._score_clarity(user_explanation),
        }
        
        # 3. 計算總分（加權平均）
        weights = {
            AssessmentDimension.COMPLETENESS: 0.30,
            AssessmentDimension.ACCURACY: 0.30,
            AssessmentDimension.COHERENCE: 0.15,
            AssessmentDimension.DEPTH: 0.15,
            AssessmentDimension.CLARITY: 0.10,
        }
        overall_score = sum(scores[dim] * weights[dim] for dim in scores)
        
        # 4. 識別知識盲點
        blind_spots = self._identify_blind_spots(
            session.key_concepts,
            session.concept_definition,
            user_explanation,
            concept_coverage,
        )
        
        # 5. 生成反饋
        feedback = self._generate_feedback(
            scores,
            overall_score,
            blind_spots,
        )
        
        # 6. 生成引導式追問
        follow_up_questions = self._generate_follow_up_questions(
            session.concept_title,
            blind_spots,
            scores,
        )
        
        # 7. 推薦行動
        recommended_actions = self._generate_recommendations(
            overall_score,
            blind_spots,
        )
        
        # 創建評估結果
        result = AssessmentResult(
            session_id=session_id,
            concept_id=session.concept_id,
            user_explanation=user_explanation,
            timestamp=datetime.now().isoformat(),
            scores=scores,
            overall_score=overall_score,
            concept_coverage=concept_coverage,
            blind_spots=blind_spots,
            feedback=feedback,
            follow_up_questions=follow_up_questions,
            recommended_actions=recommended_actions,
        )
        
        # 記錄到會話
        session.assessments.append(result)
        session.improvement_trend.append(overall_score)
        session.conversation_history.append({
            "role": "user",
            "content": user_explanation,
            "timestamp": result.timestamp,
        })
        session.conversation_history.append({
            "role": "assistant",
            "content": feedback,
            "timestamp": result.timestamp,
        })
        
        logger.info(
            f"費曼評估 {session_id}: overall={overall_score:.2f}, "
            f"coverage={concept_coverage.coverage_rate:.2f}, "
            f"blind_spots={len(blind_spots)}"
        )
        
        return result
    
    def get_socratic_dialogue(
        self,
        session_id: str,
        assessment_result: AssessmentResult,
    ) -> List[Dict[str, str]]:
        """生成蘇格拉底式對話（引導式追問）。
        
        Args:
            session_id: 會話 ID
            assessment_result: 評估結果
        
        Returns:
            List[Dict]: 對話序列
        """
        session = self._get_session(session_id)
        
        dialogue = []
        
        # 根據盲點生成針對性追問
        for i, blind_spot in enumerate(assessment_result.blind_spots[:3]):  # 最多 3 個
            question = self._craft_socratic_question(
                session.concept_title,
                blind_spot,
            )
            dialogue.append({
                "step": i + 1,
                "type": "question",
                "content": question,
                "focus": blind_spot.concept,
                "hint": blind_spot.suggestion,
            })
        
        return dialogue
    
    def get_improvement_analysis(self, session_id: str) -> Dict[str, Any]:
        """獲取進步趨勢分析。
        
        Args:
            session_id: 會話 ID
        
        Returns:
            Dict: 分析報告
        """
        session = self._get_session(session_id)
        
        if len(session.improvement_trend) < 2:
            return {
                "trend": "insufficient_data",
                "message": "需要至少兩次評估才能分析進步趨勢",
            }
        
        trend = session.improvement_trend
        improvement = trend[-1] - trend[0]
        avg_score = sum(trend) / len(trend)
        
        # 判斷趨勢
        if improvement > 0.15:
            trend_type = "significant_improvement"
            message = "進步顯著！繼續保持！"
        elif improvement > 0.05:
            trend_type = "moderate_improvement"
            message = "有穩定進步，繼續努力！"
        elif improvement > 0:
            trend_type = "slight_improvement"
            message = "略有進步，可以加強練習。"
        elif improvement > -0.05:
            trend_type = "stable"
            message = "表現穩定，嘗試挑戰更難的解釋。"
        else:
            trend_type = "needs_attention"
            message = "可能需要重新複習基礎概念。"
        
        return {
            "trend": trend_type,
            "message": message,
            "initial_score": trend[0],
            "latest_score": trend[-1],
            "improvement": improvement,
            "average_score": avg_score,
            "total_attempts": len(trend),
        }
    
    # ── 內部方法 ──
    
    def _get_session(self, session_id: str) -> FeynmanSession:
        if session_id not in self.sessions:
            raise ValueError(f"會話不存在：{session_id}")
        return self.sessions[session_id]
    
    def _analyze_concept_coverage(
        self,
        key_concepts: List[str],
        user_explanation: str,
    ) -> ConceptCoverage:
        """分析概念覆蓋率。"""
        text_lower = user_explanation.lower()
        
        covered = []
        missing = []
        
        for concept in key_concepts:
            # 檢查概念及其同義詞
            if self._concept_in_text(concept, text_lower):
                covered.append(concept)
            else:
                missing.append(concept)
        
        coverage_rate = len(covered) / len(key_concepts) if key_concepts else 0.0
        
        return ConceptCoverage(
            total_concepts=len(key_concepts),
            covered_concepts=len(covered),
            missing_concepts=missing,
            coverage_rate=coverage_rate,
        )
    
    def _concept_in_text(self, concept: str, text: str) -> bool:
        """檢查概念是否在文本中（支持變體匹配）。"""
        concept_lower = concept.lower()
        
        # 直接匹配
        if concept_lower in text:
            return True
        
        # 部分匹配（對於長概念）
        if len(concept) > 4:
            words = concept_lower.split()
            if len(words) > 1:
                # 檢查關鍵詞是否都出現
                return all(word in text for word in words if len(word) > 2)
        
        return False
    
    def _score_completeness(self, coverage: ConceptCoverage) -> float:
        """完整性評分。"""
        return coverage.coverage_rate
    
    def _score_accuracy(
        self,
        reference: str,
        user_explanation: str,
    ) -> float:
        """準確性評分（與參考定義的相似度）。"""
        # 簡單實現：關鍵詞重疊率
        ref_words = set(self._tokenize(reference))
        user_words = set(self._tokenize(user_explanation))
        
        if not ref_words:
            return 0.5
        
        intersection = ref_words & user_words
        # Jaccard 相似度
        similarity = len(intersection) / len(ref_words | user_words)
        
        return min(1.0, similarity * 2)  # 放大一點
    
    def _score_coherence(self, text: str) -> float:
        """連貫性評分。"""
        # 計算連接詞使用
        connector_count = 0
        for category, connectors in self.LOGIC_CONNECTORS.items():
            for connector in connectors:
                if connector in text.lower():
                    connector_count += 1
        
        # 句子數量
        sentences = len(re.split(r'[。！？.!?]', text))
        
        if sentences == 0:
            return 0.3
        
        # 連接詞密度
        density = connector_count / sentences
        
        # 最佳密度 0.3-0.6
        if 0.3 <= density <= 0.6:
            return 0.95
        elif 0.2 <= density < 0.3 or 0.6 < density <= 0.8:
            return 0.75
        elif density < 0.2:
            return 0.5  # 連接詞太少
        else:
            return 0.6  # 連接詞太多
    
    def _score_depth(self, text: str) -> float:
        """深度評分。"""
        depth_indicators = [
            "本質", "核心", "原理", "機制", "deep", "essence", "fundamental",
            "因為", "所以", "導致", "cause", "effect", "result",
            "不僅", "而且", "除了", "not only", "but also",
        ]
        
        text_lower = text.lower()
        count = sum(1 for indicator in depth_indicators if indicator in text_lower)
        
        # 歸一化
        return min(1.0, count / 5)
    
    def _score_clarity(self, text: str) -> float:
        """清晰度評分。"""
        text_lower = text.lower()
        
        # 模糊表達扣分
        vague_count = sum(1 for expr in self.VAGUE_EXPRESSIONS if expr in text_lower)
        
        # 句子平均長度（太長或太短都不好）
        sentences = [s.strip() for s in re.split(r'[。！？.!?]', text) if s.strip()]
        if sentences:
            avg_length = sum(len(s) for s in sentences) / len(sentences)
            if 15 <= avg_length <= 50:
                length_penalty = 0
            elif 10 <= avg_length < 15 or 50 < avg_length <= 70:
                length_penalty = 0.1
            else:
                length_penalty = 0.2
        else:
            length_penalty = 0.2
        
        # 模糊表達扣分
        vague_penalty = min(0.3, vague_count * 0.05)
        
        return max(0.3, 1.0 - vague_penalty - length_penalty)
    
    def _tokenize(self, text: str) -> List[str]:
        """簡單分詞。"""
        # 中文：提取 2 字以上詞語
        chinese_words = re.findall(r'[\u4e00-\u9fa5]{2,}', text)
        # 英文：提取單詞
        english_words = re.findall(r'[a-zA-Z]{3,}', text)
        return chinese_words + english_words
    
    def _identify_blind_spots(
        self,
        key_concepts: List[str],
        reference: str,
        user_explanation: str,
        coverage: ConceptCoverage,
    ) -> List[BlindSpot]:
        """識別知識盲點。"""
        blind_spots = []
        
        # 1. 缺失概念
        for concept in coverage.missing_concepts:
            blind_spots.append(BlindSpot(
                blind_spot_type=BlindSpotType.MISSING_CONCEPT,
                concept=concept,
                description=f"未提及關鍵概念「{concept}」",
                severity="high" if len(concept) > 4 else "medium",
                evidence="解釋中未包含此概念",
                suggestion=f"嘗試解釋「{concept}」是什麼，以及它與其他概念的關係",
            ))
        
        # 2. 模糊表達（可能表示誤解）
        text_lower = user_explanation.lower()
        for expr in self.VAGUE_EXPRESSIONS:
            if expr in text_lower:
                blind_spots.append(BlindSpot(
                    blind_spot_type=BlindSpotType.CONFUSION,
                    concept=expr,
                    description="使用了不確定的表達",
                    severity="low",
                    evidence=f"文本中包含「{expr}」",
                    suggestion="嘗試更確定的表達，如果不确定，可以明確指出哪裡不清楚",
                ))
                break  # 只記錄一次
        
        # 3. 邏輯斷層（檢查是否有因果關係但缺少連接詞）
        if self._has_logic_gap(reference, user_explanation):
            blind_spots.append(BlindSpot(
                blind_spot_type=BlindSpotType.LOGIC_GAP,
                concept="邏輯連接",
                description="解釋中可能存在邏輯斷層",
                severity="medium",
                evidence="缺少必要的因果連接詞",
                suggestion="使用「因為...所以...」、「由於...因此...」等連接詞來明確邏輯關係",
            ))
        
        # 4. 過度簡化（檢查是否太短或太簡單）
        if len(user_explanation) < len(reference) * 0.3:
            blind_spots.append(BlindSpot(
                blind_spot_type=BlindSpotType.OVERSIMPLIFICATION,
                concept="內容完整性",
                description="解釋可能過於簡化",
                severity="medium",
                evidence=f"解釋長度僅為參考的{len(user_explanation)/len(reference)*100:.0f}%",
                suggestion="嘗試提供更多細節和例子來豐富解釋",
            ))
        
        return blind_spots
    
    def _has_logic_gap(self, reference: str, user_explanation: str) -> bool:
        """檢查是否存在邏輯斷層。"""
        # 簡單實現：如果參考文本有因果關係但用戶解釋沒有
        has_cause_in_ref = any(
            connector in reference.lower()
            for connectors in self.LOGIC_CONNECTORS.values()
            for connector in connectors
        )
        has_cause_in_user = any(
            connector in user_explanation.lower()
            for connectors in self.LOGIC_CONNECTORS.values()
            for connector in connectors
        )
        
        return has_cause_in_ref and not has_cause_in_user
    
    def _generate_feedback(
        self,
        scores: Dict[AssessmentDimension, float],
        overall_score: float,
        blind_spots: List[BlindSpot],
    ) -> str:
        """生成反饋。"""
        # 總體評價
        if overall_score >= self.HIGH_QUALITY_THRESHOLD:
            overall_comment = "非常出色！你的解釋完整且準確。"
        elif overall_score >= self.MEDIUM_QUALITY_THRESHOLD:
            overall_comment = "不錯！你已經掌握了主要概念，還有一些細節可以完善。"
        else:
            overall_comment = "需要加強練習。讓我們一起找出可以改進的地方。"
        
        # 維度分析
        dimension_feedback = []
        for dim, score in scores.items():
            if score >= 0.8:
                feedback = f"{dim.value}: 優秀 ({score:.2f})"
            elif score >= 0.6:
                feedback = f"{dim.value}: 良好 ({score:.2f})"
            else:
                feedback = f"{dim.value}: 需要改進 ({score:.2f})"
            dimension_feedback.append(feedback)
        
        # 盲點提示
        if blind_spots:
            blind_spot_summary = f"\n\n發現 {len(blind_spots)} 個知識盲點："
            for i, spot in enumerate(blind_spots[:3], 1):
                blind_spot_summary += f"\n{i}. {spot.description}"
        else:
            blind_spot_summary = "\n\n未發現明顯知識盲點。"
        
        return f"{overall_comment}\n\n{' | '.join(dimension_feedback)}{blind_spot_summary}"
    
    def _generate_follow_up_questions(
        self,
        concept_title: str,
        blind_spots: List[BlindSpot],
        scores: Dict[AssessmentDimension, float],
    ) -> List[str]:
        """生成引導式追問。"""
        questions = []
        
        # 根據盲點生成問題
        for spot in blind_spots[:2]:
            if spot.blind_spot_type == BlindSpotType.MISSING_CONCEPT:
                questions.append(f"你能解釋一下「{spot.concept}」在這個概念中的作用嗎？")
            elif spot.blind_spot_type == BlindSpotType.LOGIC_GAP:
                questions.append("這個過程的因果關係是什麼？為什麼會這樣？")
            elif spot.blind_spot_type == BlindSpotType.OVERSIMPLIFICATION:
                questions.append("能舉一個具體的例子來說明嗎？")
        
        # 根據低分維度生成問題
        if scores.get(AssessmentDimension.DEPTH, 0) < 0.6:
            questions.append(f"這個概念的本質是什麼？它為什麼重要？")
        
        if scores.get(AssessmentDimension.ACCURACY, 0) < 0.6:
            questions.append(f"你能用更精確的語言重新描述{concept_title}嗎？")
        
        return questions[:5]  # 最多 5 個問題
    
    def _generate_recommendations(
        self,
        overall_score: float,
        blind_spots: List[BlindSpot],
    ) -> List[str]:
        """生成推薦行動。"""
        recommendations = []
        
        if overall_score < self.MEDIUM_QUALITY_THRESHOLD:
            recommendations.append("重新學習基礎概念")
            recommendations.append("閱讀教材中的定義和例子")
        
        if any(s.blind_spot_type == BlindSpotType.MISSING_CONCEPT for s in blind_spots):
            recommendations.append("重點複習缺失的關鍵概念")
        
        if any(s.blind_spot_type == BlindSpotType.LOGIC_GAP for s in blind_spots):
            recommendations.append("練習用「因為...所以...」的結構解釋概念")
        
        if overall_score >= self.HIGH_QUALITY_THRESHOLD:
            recommendations.append("嘗試向他人解釋這個概念")
            recommendations.append("挑戰相關的進階問題")
        
        return recommendations[:5]
    
    def _craft_socratic_question(
        self,
        concept_title: str,
        blind_spot: BlindSpot,
    ) -> str:
        """製作蘇格拉底式問題。"""
        templates = {
            BlindSpotType.MISSING_CONCEPT: [
                f"你提到了{concept_title}，但似乎沒有談到「{blind_spot.concept}」。"
                f"你認為它在這個概念中扮演什麼角色？",
                f"如果缺少「{blind_spot.concept}」，{concept_title}還成立嗎？為什麼？",
            ],
            BlindSpotType.MISUNDERSTANDING: [
                f"你說「{blind_spot.evidence}」，這個理解可能有點偏差。"
                f"讓我們想想：{blind_spot.suggestion}",
            ],
            BlindSpotType.LOGIC_GAP: [
                f"你描述了現象，但原因是什麼呢？為什麼會這樣？",
                f"如果 A 導致 B，那麼中間的機制是什麼？",
            ],
            BlindSpotType.OVERSIMPLIFICATION: [
                f"這個解釋很簡潔，但能舉一個具體的例子嗎？",
                f"在什麼情況下這個結論可能不成立？",
            ],
            BlindSpotType.CONFUSION: [
                f"你說「{blind_spot.evidence}」，是什麼讓你不太確定？",
                f"哪一部分最讓你困惑？我們可以重點討論。",
            ],
        }
        
        import random
        options = templates.get(blind_spot.blind_spot_type, ["你能進一步解釋嗎？"])
        return random.choice(options)


# ── 輔助函數 ──

def create_feynman_session(
    session_id: str,
    concept_id: str,
    concept_title: str,
    concept_definition: str,
    key_concepts: List[str],
) -> FeynmanSession:
    """創建費曼學習會話（輔助函數）。"""
    engine = FeynmanAssessmentEngine()
    return engine.create_session(
        session_id=session_id,
        concept_id=concept_id,
        concept_title=concept_title,
        concept_definition=concept_definition,
        key_concepts=key_concepts,
    )
