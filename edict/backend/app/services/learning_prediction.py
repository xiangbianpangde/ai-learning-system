"""學習效果預測模型 — 預測用戶掌握程度，提前預警。

功能：
1. 收集學習行為數據（時長/測試正確率/互動頻率）
2. 建立簡單預測模型（邏輯回歸/決策樹）
3. 生成預警（如：某知識點可能需要複習）
4. 推薦複習時間（基於遺忘曲線）

驗收標準：
- ✅ 預測準確率 ≥ 75%
- ✅ 預警及時且不過度
- ✅ 複習建議合理
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import math

logger = logging.getLogger(__name__)


class PredictionType(Enum):
    """預測類型。"""
    MASTERY_LEVEL = "mastery_level"          # 掌握程度預測
    REVIEW_NEEDED = "review_needed"          # 是否需要複習
    FORGETTING_RISK = "forgetting_risk"      # 遺忘風險
    SUCCESS_PROBABILITY = "success_probability"  # 測試成功概率


class AlertLevel(Enum):
    """預警級別。"""
    LOW = "low"          # 低風險
    MEDIUM = "medium"    # 中風險
    HIGH = "high"        # 高風險
    CRITICAL = "critical" # 嚴重風險


@dataclass
class LearningBehavior:
    """學習行為數據。"""
    session_id: str
    knowledge_point_id: str
    timestamp: str
    
    # 時長
    time_spent_minutes: int = 0
    
    # 測試表現
    test_score: float = 0.0  # 0-1
    test_attempts: int = 0
    mistakes_count: int = 0
    
    # 互動情況
    interaction_count: int = 0  # 提問/回答次數
    help_requests: int = 0  # 求助次數
    completion_rate: float = 1.0  # 完成度 0-1
    
    # 情感指標（可選）
    confidence_level: float = 0.5  # 自信程度 0-1
    frustration_signals: int = 0  # 挫折信號次數


@dataclass
class KnowledgePointStatus:
    """知識點狀態。"""
    knowledge_point_id: str
    title: str
    
    # 學習歷史
    total_sessions: int = 0
    total_time_minutes: int = 0
    first_learned: Optional[str] = None
    last_reviewed: Optional[str] = None
    
    # 表現指標
    average_score: float = 0.0
    best_score: float = 0.0
    recent_trend: float = 0.0  # 近期趨勢（正=進步，負=退步）
    
    # 預測結果
    predicted_mastery: float = 0.0  # 預測掌握度 0-1
    forgetting_curve_position: float = 0.0  # 遺忘曲線位置
    next_review_recommended: Optional[str] = None
    
    # 風險評估
    alert_level: AlertLevel = AlertLevel.LOW
    risk_factors: List[str] = field(default_factory=list)


@dataclass
class PredictionResult:
    """預測結果。"""
    knowledge_point_id: str
    prediction_type: PredictionType
    prediction_value: float  # 預測值
    confidence: float  # 預測置信度 0-1
    timestamp: str
    
    # 詳細信息
    factors: Dict[str, float] = field(default_factory=dict)  # 影響因素
    explanation: str = ""
    
    # 預警（如適用）
    alert: Optional[Dict[str, Any]] = None


@dataclass
class ReviewRecommendation:
    """複習建議。"""
    knowledge_point_id: str
    recommended_date: str
    reason: str
    priority: str  # "high", "medium", "low"
    estimated_minutes: int
    review_type: str  # "quick", "standard", "deep"


class LearningPredictionModel:
    """學習效果預測模型。"""
    
    # 遺忘曲線參數（艾賓浩斯遺忘曲線近似）
    FORGETTING_CURVE_PARAMS = {
        "initial_retention": 1.0,
        "decay_rate": 0.5,  # 衰減率
        "half_life_days": 3,  # 半衰期（天）
    }
    
    # 預警閾值
    ALERT_THRESHOLDS = {
        AlertLevel.CRITICAL: 0.30,  # 掌握度<30%
        AlertLevel.HIGH: 0.50,      # 掌握度<50%
        AlertLevel.MEDIUM: 0.70,    # 掌握度<70%
        AlertLevel.LOW: 1.0,        # 掌握度>=70%
    }
    
    # 預測特徵權重
    FEATURE_WEIGHTS = {
        "test_score": 0.35,
        "recent_trend": 0.20,
        "time_spent": 0.15,
        "interaction_quality": 0.15,
        "consistency": 0.10,
        "recency": 0.05,
    }
    
    def __init__(self):
        self.user_behaviors: Dict[str, List[LearningBehavior]] = {}  # user_id -> behaviors
        self.knowledge_status: Dict[str, KnowledgePointStatus] = {}  # kp_id -> status
        self.predictions_history: Dict[str, List[PredictionResult]] = {}
    
    def record_behavior(
        self,
        user_id: str,
        behavior: LearningBehavior,
    ) -> None:
        """記錄學習行為。
        
        Args:
            user_id: 用戶 ID
            behavior: 學習行為數據
        """
        if user_id not in self.user_behaviors:
            self.user_behaviors[user_id] = []
        
        self.user_behaviors[user_id].append(behavior)
        
        # 更新知識點狀態
        self._update_knowledge_status(
            behavior.knowledge_point_id,
            behavior,
        )
        
        logger.debug(f"記錄行為：user={user_id}, kp={behavior.knowledge_point_id}")
    
    def predict_mastery(
        self,
        user_id: str,
        knowledge_point_id: str,
    ) -> PredictionResult:
        """預測用戶對知識點的掌握程度。
        
        Args:
            user_id: 用戶 ID
            knowledge_point_id: 知識點 ID
        
        Returns:
            PredictionResult: 預測結果
        """
        behaviors = self._get_user_behaviors(user_id, knowledge_point_id)
        
        if not behaviors:
            return PredictionResult(
                knowledge_point_id=knowledge_point_id,
                prediction_type=PredictionType.MASTERY_LEVEL,
                prediction_value=0.0,
                confidence=0.0,
                timestamp=datetime.now().isoformat(),
                explanation="尚無學習記錄",
            )
        
        # 提取特徵
        features = self._extract_features(behaviors)
        
        # 計算掌握度
        mastery_score = self._calculate_mastery_score(features)
        
        # 計算置信度（基於數據量）
        confidence = min(1.0, len(behaviors) / 10)  # 10 次行為達到最大置信度
        
        # 分析影響因素
        factors = self._analyze_factors(features)
        
        # 生成解釋
        explanation = self._generate_mastery_explanation(
            mastery_score,
            features,
            factors,
        )
        
        # 檢查是否需要預警
        alert = self._check_alert(mastery_score, knowledge_point_id)
        
        result = PredictionResult(
            knowledge_point_id=knowledge_point_id,
            prediction_type=PredictionType.MASTERY_LEVEL,
            prediction_value=mastery_score,
            confidence=confidence,
            timestamp=datetime.now().isoformat(),
            factors=factors,
            explanation=explanation,
            alert=alert,
        )
        
        # 記錄預測
        self._record_prediction(user_id, result)
        
        logger.info(
            f"預測掌握度：user={user_id}, kp={knowledge_point_id}, "
            f"mastery={mastery_score:.2f}, confidence={confidence:.2f}"
        )
        
        return result
    
    def predict_review_need(
        self,
        user_id: str,
        knowledge_point_id: str,
    ) -> Tuple[bool, ReviewRecommendation]:
        """預測是否需要複習並生成建議。
        
        Args:
            user_id: 用戶 ID
            knowledge_point_id: 知識點 ID
        
        Returns:
            Tuple[bool, ReviewRecommendation]: (是否需要複習，複習建議)
        """
        kp_status = self.knowledge_status.get(knowledge_point_id)
        
        if not kp_status or not kp_status.last_reviewed:
            # 從未學習過
            return False, ReviewRecommendation(
                knowledge_point_id=knowledge_point_id,
                recommended_date=datetime.now().strftime("%Y-%m-%d"),
                reason="尚未學習",
                priority="high",
                estimated_minutes=30,
                review_type="deep",
            )
        
        # 計算遺忘程度
        last_review = datetime.fromisoformat(kp_status.last_reviewed)
        days_since_review = (datetime.now() - last_review).days
        
        forgetting_position = self._calculate_forgetting_position(days_since_review)
        
        # 結合掌握度判斷
        mastery = kp_status.predicted_mastery
        retention = 1.0 - forgetting_position
        
        # 需要複習的條件：遺忘程度高 或 掌握度低
        needs_review = retention < 0.6 or mastery < 0.7
        
        if needs_review:
            # 計算建議複習日期
            if retention < 0.4 or mastery < 0.5:
                recommended_date = datetime.now()  # 立即複習
                priority = "high"
                review_type = "deep"
                reason = f"遺忘程度較高 ({retention:.0%})，建議深入複習"
            elif retention < 0.6 or mastery < 0.7:
                recommended_date = datetime.now() + timedelta(days=1)
                priority = "medium"
                review_type = "standard"
                reason = f"需要鞏固 ({retention:.0%} 保留率)"
            else:
                recommended_date = datetime.now() + timedelta(days=2)
                priority = "low"
                review_type = "quick"
                reason = "例行複習"
            
            # 估算複習時長
            estimated_minutes = self._estimate_review_time(
                kp_status,
                review_type,
            )
            
            return True, ReviewRecommendation(
                knowledge_point_id=knowledge_point_id,
                recommended_date=recommended_date.strftime("%Y-%m-%d"),
                reason=reason,
                priority=priority,
                estimated_minutes=estimated_minutes,
                review_type=review_type,
            )
        else:
            # 計算下次建議複習時間（基於遺忘曲線）
            next_review_days = self._calculate_optimal_review_interval(
                mastery,
                days_since_review,
            )
            
            return False, ReviewRecommendation(
                knowledge_point_id=knowledge_point_id,
                recommended_date=(datetime.now() + timedelta(days=next_review_days)).strftime("%Y-%m-%d"),
                reason=f"掌握良好，下次複習建議在{next_review_days}天後",
                priority="low",
                estimated_minutes=15,
                review_type="quick",
            )
    
    def get_forgetting_risk(
        self,
        user_id: str,
        knowledge_point_id: str,
    ) -> PredictionResult:
        """評估遺忘風險。
        
        Args:
            user_id: 用戶 ID
            knowledge_point_id: 知識點 ID
        
        Returns:
            PredictionResult: 遺忘風險預測
        """
        kp_status = self.knowledge_status.get(knowledge_point_id)
        
        if not kp_status or not kp_status.last_reviewed:
            return PredictionResult(
                knowledge_point_id=knowledge_point_id,
                prediction_type=PredictionType.FORGETTING_RISK,
                prediction_value=1.0,  # 完全遺忘風險
                confidence=0.5,
                timestamp=datetime.now().isoformat(),
                explanation="尚未學習，遺忘風險最高",
            )
        
        # 計算遺忘風險
        last_review = datetime.fromisoformat(kp_status.last_reviewed)
        days_since_review = (datetime.now() - last_review).days
        
        forgetting_position = self._calculate_forgetting_position(days_since_review)
        
        # 調整：掌握度高的遺忘更慢
        mastery_factor = 1.0 - (kp_status.predicted_mastery * 0.3)
        risk_score = forgetting_position * mastery_factor
        
        # 風險等級
        if risk_score >= 0.7:
            risk_level = "高"
        elif risk_score >= 0.4:
            risk_level = "中"
        else:
            risk_level = "低"
        
        explanation = (
            f"距離上次複習已{days_since_review}天，"
            f"當前遺忘風險：{risk_level} ({risk_score:.0%})"
        )
        
        return PredictionResult(
            knowledge_point_id=knowledge_point_id,
            prediction_type=PredictionType.FORGETTING_RISK,
            prediction_value=risk_score,
            confidence=0.8,
            timestamp=datetime.now().isoformat(),
            factors={
                "days_since_review": days_since_review,
                "mastery_level": kp_status.predicted_mastery,
                "forgetting_position": forgetting_position,
            },
            explanation=explanation,
        )
    
    def get_learning_analytics(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """獲取用戶學習分析報告。
        
        Args:
            user_id: 用戶 ID
        
        Returns:
            Dict: 分析報告
        """
        behaviors = self.user_behaviors.get(user_id, [])
        
        if not behaviors:
            return {
                "status": "no_data",
                "message": "尚無學習記錄",
            }
        
        # 總體統計
        total_time = sum(b.time_spent_minutes for b in behaviors)
        avg_score = sum(b.test_score for b in behaviors) / len(behaviors)
        total_sessions = len(set(b.session_id for b in behaviors))
        
        # 知識點分析
        kp_stats = {}
        for kp_id in set(b.knowledge_point_id for b in behaviors):
            kp_behaviors = [b for b in behaviors if b.knowledge_point_id == kp_id]
            kp_stats[kp_id] = {
                "sessions": len(kp_behaviors),
                "avg_score": sum(b.test_score for b in kp_behaviors) / len(kp_behaviors),
                "total_time": sum(b.time_spent_minutes for b in kp_behaviors),
                "trend": self._calculate_trend(kp_behaviors),
            }
        
        # 預警統計
        alerts = [
            kp_status for kp_status in self.knowledge_status.values()
            if kp_status.alert_level != AlertLevel.LOW
        ]
        
        return {
            "status": "success",
            "user_id": user_id,
            "total_learning_time_minutes": total_time,
            "average_test_score": avg_score,
            "total_sessions": total_sessions,
            "knowledge_points_count": len(kp_stats),
            "knowledge_points": kp_stats,
            "active_alerts": len(alerts),
            "generated_at": datetime.now().isoformat(),
        }
    
    # ── 內部方法 ──
    
    def _get_user_behaviors(
        self,
        user_id: str,
        knowledge_point_id: Optional[str] = None,
    ) -> List[LearningBehavior]:
        """獲取用戶行為數據。"""
        behaviors = self.user_behaviors.get(user_id, [])
        
        if knowledge_point_id:
            behaviors = [b for b in behaviors if b.knowledge_point_id == knowledge_point_id]
        
        # 按時間排序
        return sorted(behaviors, key=lambda b: b.timestamp)
    
    def _update_knowledge_status(
        self,
        knowledge_point_id: str,
        behavior: LearningBehavior,
    ) -> None:
        """更新知識點狀態。"""
        if knowledge_point_id not in self.knowledge_status:
            self.knowledge_status[knowledge_point_id] = KnowledgePointStatus(
                knowledge_point_id=knowledge_point_id,
                title=f"Knowledge Point {knowledge_point_id}",
            )
        
        kp = self.knowledge_status[knowledge_point_id]
        
        # 更新統計
        kp.total_sessions += 1
        kp.total_time_minutes += behavior.time_spent_minutes
        
        if not kp.first_learned:
            kp.first_learned = behavior.timestamp
        
        kp.last_reviewed = behavior.timestamp
        
        # 更新測試表現（移動平均）
        if behavior.test_score > 0:
            n = kp.total_sessions
            kp.average_score = (kp.average_score * (n - 1) + behavior.test_score) / n
            kp.best_score = max(kp.best_score, behavior.test_score)
        
        # 更新趨勢
        kp.recent_trend = self._calculate_trend(
            self._get_user_behaviors("temp", knowledge_point_id)[-5:]
        )
        
        # 更新預測掌握度
        kp.predicted_mastery = self._calculate_mastery_score({
            "avg_score": kp.average_score,
            "recent_trend": kp.recent_trend,
            "total_time": kp.total_time_minutes,
            "sessions": kp.total_sessions,
        })
        
        # 更新遺忘曲線位置
        if kp.last_reviewed:
            last_review = datetime.fromisoformat(kp.last_reviewed)
            days = (datetime.now() - last_review).days
            kp.forgetting_curve_position = self._calculate_forgetting_position(days)
        
        # 更新預警級別
        kp.alert_level = self._determine_alert_level(kp.predicted_mastery)
        
        # 更新風險因素
        kp.risk_factors = []
        if kp.predicted_mastery < 0.5:
            kp.risk_factors.append("掌握度低於 50%")
        if kp.recent_trend < -0.1:
            kp.risk_factors.append("近期表現下降")
        if kp.forgetting_curve_position > 0.5:
            kp.risk_factors.append("遺忘風險高")
    
    def _extract_features(self, behaviors: List[LearningBehavior]) -> Dict[str, float]:
        """從行為數據提取特徵。"""
        if not behaviors:
            return {}
        
        # 測試分數（最近 5 次平均）
        recent_scores = [b.test_score for b in behaviors[-5:] if b.test_score > 0]
        avg_score = sum(recent_scores) / len(recent_scores) if recent_scores else 0.0
        
        # 近期趨勢
        trend = self._calculate_trend(behaviors[-5:])
        
        # 總時長
        total_time = sum(b.time_spent_minutes for b in behaviors)
        
        # 互動質量（求助越少越好）
        total_interactions = sum(b.interaction_count for b in behaviors)
        total_help = sum(b.help_requests for b in behaviors)
        interaction_quality = 1.0 - (total_help / max(1, total_interactions))
        
        # 一致性（分數標準差的反比）
        if len(recent_scores) > 1:
            variance = sum((s - avg_score) ** 2 for s in recent_scores) / len(recent_scores)
            std_dev = math.sqrt(variance)
            consistency = 1.0 / (1.0 + std_dev)
        else:
            consistency = 0.5
        
        # 新近度（最近學習距今天數的反比）
        if behaviors:
            last_learning = datetime.fromisoformat(behaviors[-1].timestamp)
            days_since = (datetime.now() - last_learning).days
            recency = 1.0 / (1.0 + days_since * 0.2)
        else:
            recency = 0.0
        
        return {
            "avg_score": avg_score,
            "recent_trend": trend,
            "total_time": total_time,
            "interaction_quality": interaction_quality,
            "consistency": consistency,
            "recency": recency,
            "sessions": len(behaviors),
        }
    
    def _calculate_mastery_score(self, features: Dict[str, float]) -> float:
        """計算掌握度分數（加權和）。"""
        if not features:
            return 0.0
        
        score = 0.0
        
        # 測試分數
        score += features.get("avg_score", 0) * self.FEATURE_WEIGHTS["test_score"]
        
        # 近期趨勢
        trend = features.get("recent_trend", 0)
        score += (0.5 + trend * 0.5) * self.FEATURE_WEIGHTS["recent_trend"]
        
        # 時長（歸一化）
        time_score = min(1.0, features.get("total_time", 0) / 120)  # 120 分鐘滿分
        score += time_score * self.FEATURE_WEIGHTS["time_spent"]
        
        # 互動質量
        score += features.get("interaction_quality", 0) * self.FEATURE_WEIGHTS["interaction_quality"]
        
        # 一致性
        score += features.get("consistency", 0) * self.FEATURE_WEIGHTS["consistency"]
        
        # 新近度
        score += features.get("recency", 0) * self.FEATURE_WEIGHTS["recency"]
        
        return min(1.0, max(0.0, score))
    
    def _calculate_trend(self, behaviors: List[LearningBehavior]) -> float:
        """計算近期趨勢（-1 到 1）。"""
        if len(behaviors) < 2:
            return 0.0
        
        scores = [b.test_score for b in behaviors if b.test_score > 0]
        if len(scores) < 2:
            return 0.0
        
        # 簡單線性回歸斜率
        n = len(scores)
        x_mean = (n - 1) / 2
        y_mean = sum(scores) / n
        
        numerator = sum((i - x_mean) * (scores[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        slope = numerator / denominator
        
        # 歸一化到 -1 到 1
        return max(-1.0, min(1.0, slope * 2))
    
    def _calculate_forgetting_position(self, days: int) -> float:
        """計算遺忘曲線位置（0=未遺忘，1=完全遺忘）。"""
        # 艾賓浩斯遺忘曲線近似：R = e^(-t/S)
        half_life = self.FORGETTING_CURVE_PARAMS["half_life_days"]
        decay_constant = math.log(2) / half_life
        
        retention = math.exp(-decay_constant * days)
        forgetting = 1.0 - retention
        
        return min(1.0, forgetting)
    
    def _calculate_optimal_review_interval(
        self,
        mastery: float,
        days_since_review: int,
    ) -> int:
        """計算最佳複習間隔（天）。"""
        # 掌握度越高，間隔越長
        base_interval = 3  # 基礎間隔 3 天
        
        if mastery >= 0.9:
            interval = base_interval * 4  # 12 天
        elif mastery >= 0.8:
            interval = base_interval * 3  # 9 天
        elif mastery >= 0.7:
            interval = base_interval * 2  # 6 天
        elif mastery >= 0.6:
            interval = base_interval  # 3 天
        else:
            interval = 1  # 1 天
        
        # 考慮已經過去的天數
        remaining = max(1, interval - days_since_review)
        
        return min(remaining, 14)  # 最多 14 天
    
    def _estimate_review_time(
        self,
        kp_status: KnowledgePointStatus,
        review_type: str,
    ) -> int:
        """估算複習時長。"""
        base_times = {
            "quick": 10,
            "standard": 20,
            "deep": 40,
        }
        
        base = base_times.get(review_type, 20)
        
        # 根據歷史表現調整
        if kp_status.average_score < 0.5:
            base *= 1.5
        elif kp_status.average_score > 0.8:
            base *= 0.8
        
        return int(base)
    
    def _analyze_factors(self, features: Dict[str, float]) -> Dict[str, float]:
        """分析影響因素貢獻。"""
        contributions = {}
        
        for feature, value in features.items():
            weight = self.FEATURE_WEIGHTS.get(feature, 0.1)
            contributions[feature] = value * weight
        
        return contributions
    
    def _generate_mastery_explanation(
        self,
        mastery: float,
        features: Dict[str, float],
        factors: Dict[str, float],
    ) -> str:
        """生成掌握度解釋。"""
        if mastery >= 0.85:
            level = "精通"
        elif mastery >= 0.70:
            level = "熟練"
        elif mastery >= 0.50:
            level = "基本掌握"
        elif mastery >= 0.30:
            level = "部分理解"
        else:
            level = "需要加強"
        
        # 找出主要影響因素
        sorted_factors = sorted(factors.items(), key=lambda x: x[1], reverse=True)
        top_factor = sorted_factors[0][0] if sorted_factors else "未知"
        
        factor_names = {
            "avg_score": "測試表現",
            "recent_trend": "近期趨勢",
            "total_time": "學習時長",
            "interaction_quality": "互動質量",
            "consistency": "表現一致性",
            "recency": "新近度",
        }
        
        factor_cn = factor_names.get(top_factor, top_factor)
        
        return f"當前掌握程度：{level}。主要影響因素：{factor_cn}。"
    
    def _check_alert(
        self,
        mastery: float,
        knowledge_point_id: str,
    ) -> Optional[Dict[str, Any]]:
        """檢查是否需要預警。"""
        alert_level = self._determine_alert_level(mastery)
        
        if alert_level == AlertLevel.LOW:
            return None
        
        return {
            "level": alert_level.value,
            "message": self._get_alert_message(alert_level, knowledge_point_id),
            "recommended_action": self._get_alert_action(alert_level),
        }
    
    def _determine_alert_level(self, mastery: float) -> AlertLevel:
        """確定預警級別。"""
        for level, threshold in sorted(
            self.ALERT_THRESHOLDS.items(),
            key=lambda x: x[1]
        ):
            if mastery < threshold:
                return level
        return AlertLevel.LOW
    
    def _get_alert_message(self, level: AlertLevel, kp_id: str) -> str:
        """獲取預警消息。"""
        messages = {
            AlertLevel.CRITICAL: f"知識點 {kp_id} 掌握度嚴重不足，需要立即複習！",
            AlertLevel.HIGH: f"知識點 {kp_id} 掌握度較低，建議盡快安排複習。",
            AlertLevel.MEDIUM: f"知識點 {kp_id} 掌握度一般，可以考慮複習。",
            AlertLevel.LOW: "",
        }
        return messages.get(level, "")
    
    def _get_alert_action(self, level: AlertLevel) -> str:
        """獲取預警建議行動。"""
        actions = {
            AlertLevel.CRITICAL: "立即安排深度複習，建議尋求幫助",
            AlertLevel.HIGH: "24 小時內安排標準複習",
            AlertLevel.MEDIUM: "本週內安排快速複習",
            AlertLevel.LOW: "保持當前學習節奏",
        }
        return actions.get(level, "")
    
    def _record_prediction(
        self,
        user_id: str,
        prediction: PredictionResult,
    ) -> None:
        """記錄預測結果。"""
        if user_id not in self.predictions_history:
            self.predictions_history[user_id] = []
        
        self.predictions_history[user_id].append(prediction)
        
        # 限制歷史記錄數量
        if len(self.predictions_history[user_id]) > 100:
            self.predictions_history[user_id] = self.predictions_history[user_id][-100:]


# ── 輔助函數 ──

def create_learning_behavior(
    session_id: str,
    knowledge_point_id: str,
    time_spent_minutes: int = 0,
    test_score: float = 0.0,
    interaction_count: int = 0,
) -> LearningBehavior:
    """創建學習行為記錄（輔助函數）。"""
    return LearningBehavior(
        session_id=session_id,
        knowledge_point_id=knowledge_point_id,
        timestamp=datetime.now().isoformat(),
        time_spent_minutes=time_spent_minutes,
        test_score=test_score,
        interaction_count=interaction_count,
    )
