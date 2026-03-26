"""學習效果預測模型單元測試。

測試覆蓋：
1. 學習行為記錄
2. 掌握程度預測
3. 複習需求預測
4. 遺忘風險評估
5. 預警生成

驗收標準：
- ✅ 預測準確率 ≥ 75%
- ✅ 預警及時且不過度
- ✅ 複習建議合理
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'edict' / 'backend'))

from app.services.learning_prediction import (
    LearningPredictionModel,
    LearningBehavior,
    PredictionResult,
    PredictionType,
    AlertLevel,
    KnowledgePointStatus,
    ReviewRecommendation,
    create_learning_behavior,
)


class TestPredictionType:
    """預測類型枚舉測試。"""
    
    def test_prediction_type_values(self):
        """測試預測類型枚舉值。"""
        assert PredictionType.MASTERY_LEVEL.value == "mastery_level"
        assert PredictionType.REVIEW_NEEDED.value == "review_needed"
        assert PredictionType.FORGETTING_RISK.value == "forgetting_risk"
        assert PredictionType.SUCCESS_PROBABILITY.value == "success_probability"


class TestAlertLevel:
    """預警級別枚舉測試。"""
    
    def test_alert_level_values(self):
        """測試預警級別枚舉值。"""
        assert AlertLevel.LOW.value == "low"
        assert AlertLevel.MEDIUM.value == "medium"
        assert AlertLevel.HIGH.value == "high"
        assert AlertLevel.CRITICAL.value == "critical"


class TestLearningBehavior:
    """學習行為數據結構測試。"""
    
    def test_behavior_creation(self):
        """測試學習行為創建。"""
        behavior = LearningBehavior(
            session_id="session_001",
            knowledge_point_id="kp_001",
            timestamp=datetime.now().isoformat(),
            time_spent_minutes=30,
            test_score=0.85,
            interaction_count=5,
        )
        
        assert behavior.session_id == "session_001"
        assert behavior.knowledge_point_id == "kp_001"
        assert behavior.time_spent_minutes == 30
        assert behavior.test_score == 0.85


class TestLearningPredictionModel:
    """學習預測模型測試。"""
    
    def setup_method(self):
        """測試前設置。"""
        self.model = LearningPredictionModel()
        self.user_id = "user_test"
        self.kp_id = "kp_test"
    
    def test_record_behavior(self):
        """測試記錄學習行為。"""
        behavior = create_learning_behavior(
            session_id="session_001",
            knowledge_point_id=self.kp_id,
            time_spent_minutes=30,
            test_score=0.8,
        )
        
        self.model.record_behavior(self.user_id, behavior)
        
        assert self.user_id in self.model.user_behaviors
        assert len(self.model.user_behaviors[self.user_id]) == 1
        assert self.kp_id in self.model.knowledge_status
    
    def test_predict_mastery_no_data(self):
        """測試無數據時的掌握度預測。"""
        result = self.model.predict_mastery(
            user_id="user_new",
            knowledge_point_id="kp_new",
        )
        
        assert result.prediction_value == 0.0
        assert result.confidence == 0.0
        assert "尚無學習記錄" in result.explanation
    
    def test_predict_mastery_with_data(self):
        """測試有數據時的掌握度預測。"""
        # 記錄多次行為
        for i in range(5):
            behavior = create_learning_behavior(
                session_id=f"session_{i}",
                knowledge_point_id=self.kp_id,
                time_spent_minutes=30,
                test_score=0.8 + i * 0.04,  # 遞增分數
            )
            self.model.record_behavior(self.user_id, behavior)
        
        result = self.model.predict_mastery(self.user_id, self.kp_id)
        
        assert result.prediction_value > 0.5
        assert result.confidence > 0.3
        assert len(result.factors) > 0
    
    def test_predict_review_need_not_learned(self):
        """測試未學習知識點的複習預測。"""
        needs_review, recommendation = self.model.predict_review_need(
            user_id="user_new",
            knowledge_point_id="kp_new",
        )
        
        assert needs_review is False  # 未學習，不算是複習
        assert recommendation.priority == "high"
        assert recommendation.review_type == "deep"
    
    def test_predict_review_need_forgotten(self):
        """測試遺忘知識點的複習預測。"""
        # 記錄一個舊的學習行為
        old_time = (datetime.now() - timedelta(days=10)).isoformat()
        behavior = LearningBehavior(
            session_id="session_old",
            knowledge_point_id=self.kp_id,
            timestamp=old_time,
            time_spent_minutes=30,
            test_score=0.6,
        )
        self.model.record_behavior(self.user_id, behavior)
        
        needs_review, recommendation = self.model.predict_review_need(
            self.user_id,
            self.kp_id,
        )
        
        assert needs_review is True
        assert recommendation.priority in ["high", "medium"]
    
    def test_predict_review_need_well_mastered(self):
        """測試掌握良好的複習預測。"""
        # 記錄最近的優秀表現（多次以建立足夠的數據）
        recent_time = (datetime.now() - timedelta(days=1)).isoformat()
        for i in range(5):
            behavior = LearningBehavior(
                session_id=f"session_recent_{i}",
                knowledge_point_id=self.kp_id,
                timestamp=recent_time,
                time_spent_minutes=40,
                test_score=0.95,
            )
            self.model.record_behavior(self.user_id, behavior)
        
        needs_review, recommendation = self.model.predict_review_need(
            self.user_id,
            self.kp_id,
        )
        
        # 掌握良好，複習優先級應該較低
        # 由於剛學習 1 天，可能還需要確認是否要複習
        assert recommendation.priority in ["low", "medium"]
    
    def test_get_forgetting_risk(self):
        """測試遺忘風險評估。"""
        # 記錄舊的學習行為
        old_time = (datetime.now() - timedelta(days=7)).isoformat()
        behavior = LearningBehavior(
            session_id="session_old",
            knowledge_point_id=self.kp_id,
            timestamp=old_time,
            time_spent_minutes=30,
            test_score=0.7,
        )
        self.model.record_behavior(self.user_id, behavior)
        
        result = self.model.get_forgetting_risk(self.user_id, self.kp_id)
        
        assert result.prediction_type == PredictionType.FORGETTING_RISK
        assert result.prediction_value > 0.3  # 7 天應該有一定遺忘風險
        assert "天" in result.explanation
    
    def test_get_learning_analytics(self):
        """測試學習分析報告。"""
        # 記錄多個行為
        for i in range(10):
            behavior = create_learning_behavior(
                session_id=f"session_{i}",
                knowledge_point_id=f"kp_{i % 3}",  # 3 個知識點
                time_spent_minutes=30,
                test_score=0.7 + i * 0.02,
            )
            self.model.record_behavior(self.user_id, behavior)
        
        analytics = self.model.get_learning_analytics(self.user_id)
        
        assert analytics["status"] == "success"
        assert analytics["total_learning_time_minutes"] > 0
        assert analytics["knowledge_points_count"] == 3
        assert "generated_at" in analytics
    
    def test_alert_generation(self):
        """測試預警生成。"""
        # 記錄差的表現（多次低分）
        for i in range(5):
            behavior = create_learning_behavior(
                session_id=f"session_bad_{i}",
                knowledge_point_id=self.kp_id,
                time_spent_minutes=10,
                test_score=0.15,  # 非常低分
            )
            self.model.record_behavior(self.user_id, behavior)
        
        result = self.model.predict_mastery(self.user_id, self.kp_id)
        
        # 低分應該觸發預警
        assert result.alert is not None
        assert result.alert["level"] in ["medium", "high", "critical"]
        assert "recommended_action" in result.alert
    
    def test_no_alert_for_good_performance(self):
        """測試良好表現無預警。"""
        # 記錄好的表現
        for i in range(5):
            behavior = create_learning_behavior(
                session_id=f"session_good_{i}",
                knowledge_point_id=self.kp_id,
                time_spent_minutes=40,
                test_score=0.9,
            )
            self.model.record_behavior(self.user_id, behavior)
        
        result = self.model.predict_mastery(self.user_id, self.kp_id)
        
        # 良好表現應該無預警或只有低級別預警
        if result.alert:
            assert result.alert["level"] == "low"


class TestPredictionAccuracy:
    """預測準確率測試（驗收標準 ≥ 75%）。"""
    
    def setup_method(self):
        """測試前設置。"""
        self.model = LearningPredictionModel()
    
    def test_mastery_prediction_accuracy(self):
        """測試掌握度預測準確率。"""
        user_id = "user_accuracy"
        
        # 模擬不同掌握程度的用戶
        test_cases = [
            # (測試分數列表，預期掌握程度範圍)
            ([0.9, 0.9, 0.9, 0.9, 0.9], (0.7, 1.0)),  # 高掌握
            ([0.5, 0.5, 0.5, 0.5, 0.5], (0.3, 0.6)),  # 中掌握
            ([0.2, 0.2, 0.2, 0.2, 0.2], (0.0, 0.3)),  # 低掌握
            ([0.3, 0.5, 0.7, 0.8, 0.9], (0.5, 0.8)),  # 進步趨勢
            ([0.9, 0.8, 0.7, 0.5, 0.3], (0.3, 0.6)),  # 退步趨勢
        ]
        
        correct_count = 0
        
        for i, (scores, (expected_min, expected_max)) in enumerate(test_cases):
            kp_id = f"kp_accuracy_{i}"
            
            # 記錄行為
            for j, score in enumerate(scores):
                behavior = create_learning_behavior(
                    session_id=f"session_acc_{i}_{j}",
                    knowledge_point_id=kp_id,
                    time_spent_minutes=30,
                    test_score=score,
                )
                self.model.record_behavior(user_id, behavior)
            
            # 預測
            result = self.model.predict_mastery(user_id, kp_id)
            predicted = result.prediction_value
            
            # 檢查是否在預期範圍內（允許一定誤差）
            tolerance = 0.15
            if expected_min - tolerance <= predicted <= expected_max + tolerance:
                correct_count += 1
        
        accuracy = correct_count / len(test_cases)
        assert accuracy >= 0.75, f"預測準確率 {accuracy:.0%} < 75%"


class TestAlertTimeliness:
    """預警及時性測試（驗收標準：及時且不過度）。"""
    
    def setup_method(self):
        """測試前設置。"""
        self.model = LearningPredictionModel()
    
    def test_alert_timeliness(self):
        """測試預警及時性。"""
        user_id = "user_alert"
        
        # 測試案例：不同情況下是否正確預警
        test_cases = [
            # (分數列表，應該有預警)
            ([0.2, 0.2, 0.2], True),   # 持續低分 → 應該預警
            ([0.3, 0.2, 0.1], True),   # 下降趨勢 → 應該預警
            ([0.9, 0.9, 0.9], False),  # 持續高分 → 不預警
            ([0.7, 0.8, 0.9], False),  # 上升趨勢 → 不預警
        ]
        
        correct_count = 0
        
        for i, (scores, should_alert) in enumerate(test_cases):
            kp_id = f"kp_alert_{i}"
            
            # 記錄行為
            for j, score in enumerate(scores):
                behavior = create_learning_behavior(
                    session_id=f"session_alert_{i}_{j}",
                    knowledge_point_id=kp_id,
                    time_spent_minutes=30,
                    test_score=score,
                )
                self.model.record_behavior(user_id, behavior)
            
            # 檢查預警
            result = self.model.predict_mastery(user_id, kp_id)
            has_alert = result.alert is not None and result.alert["level"] != "low"
            
            if has_alert == should_alert:
                correct_count += 1
        
        accuracy = correct_count / len(test_cases)
        assert accuracy >= 0.75, f"預警準確率 {accuracy:.0%} < 75%"


class TestReviewRecommendation:
    """複習建議合理性測試（驗收標準）。"""
    
    def setup_method(self):
        """測試前設置。"""
        self.model = LearningPredictionModel()
    
    def test_review_time_reasonable(self):
        """測試複習時長建議合理。"""
        user_id = "user_review"
        kp_id = "kp_review"
        
        # 記錄學習行為
        behavior = create_learning_behavior(
            session_id="session_review",
            knowledge_point_id=kp_id,
            time_spent_minutes=30,
            test_score=0.6,
        )
        self.model.record_behavior(user_id, behavior)
        
        # 獲取複習建議
        needs_review, recommendation = self.model.predict_review_need(user_id, kp_id)
        
        # 檢查時長合理性
        assert 10 <= recommendation.estimated_minutes <= 60
        assert recommendation.review_type in ["quick", "standard", "deep"]
    
    def test_review_priority_reasonable(self):
        """測試複習優先級合理。"""
        user_id = "user_priority"
        
        # 情況 1：剛學完且掌握良好（多次優秀表現）
        kp1 = "kp_priority_1"
        recent_time = (datetime.now() - timedelta(days=1)).isoformat()
        for i in range(5):
            behavior = LearningBehavior(
                session_id=f"session_recent_{i}",
                knowledge_point_id=kp1,
                timestamp=recent_time,
                time_spent_minutes=40,
                test_score=0.95,
            )
            self.model.record_behavior(user_id, behavior)
        
        _, rec1 = self.model.predict_review_need(user_id, kp1)
        # 掌握良好，優先級應該較低或中等
        assert rec1.priority in ["low", "medium"]
        
        # 情況 2：很久沒複習且掌握一般
        kp2 = "kp_priority_2"
        old_time = (datetime.now() - timedelta(days=14)).isoformat()
        behavior2 = LearningBehavior(
            session_id="session_old",
            knowledge_point_id=kp2,
            timestamp=old_time,
            time_spent_minutes=20,
            test_score=0.5,
        )
        self.model.record_behavior(user_id, behavior2)
        
        _, rec2 = self.model.predict_review_need(user_id, kp2)
        assert rec2.priority in ["high", "medium"]
    
    def test_review_type_reasonable(self):
        """測試複習類型建議合理。"""
        user_id = "user_type"
        
        # 掌握度低 → 深度複習
        kp1 = "kp_type_1"
        for i in range(3):
            behavior = create_learning_behavior(
                session_id=f"session_type_1_{i}",
                knowledge_point_id=kp1,
                time_spent_minutes=15,
                test_score=0.3,
            )
            self.model.record_behavior(user_id, behavior)
        
        _, rec1 = self.model.predict_review_need(user_id, kp1)
        assert rec1.review_type == "deep"
        
        # 掌握度高 → 快速複習
        kp2 = "kp_type_2"
        for i in range(5):
            behavior = create_learning_behavior(
                session_id=f"session_type_2_{i}",
                knowledge_point_id=kp2,
                time_spent_minutes=40,
                test_score=0.9,
            )
            self.model.record_behavior(user_id, behavior)
        
        _, rec2 = self.model.predict_review_need(user_id, kp2)
        assert rec2.review_type in ["quick", "standard"]


class TestForgettingCurve:
    """遺忘曲線測試。"""
    
    def setup_method(self):
        """測試前設置。"""
        self.model = LearningPredictionModel()
    
    def test_forgetting_increases_with_time(self):
        """測試遺忘隨時間增加。"""
        user_id = "user_forgetting"
        
        # 不同天數前的學習
        days_list = [1, 3, 7, 14]
        risks = []
        
        for i, days in enumerate(days_list):
            kp_id = f"kp_forget_{i}"
            old_time = (datetime.now() - timedelta(days=days)).isoformat()
            
            behavior = LearningBehavior(
                session_id=f"session_forget_{i}",
                knowledge_point_id=kp_id,
                timestamp=old_time,
                time_spent_minutes=30,
                test_score=0.8,
            )
            self.model.record_behavior(user_id, behavior)
            
            result = self.model.get_forgetting_risk(user_id, kp_id)
            risks.append(result.prediction_value)
        
        # 遺忘風險應該隨天數增加
        for i in range(len(risks) - 1):
            assert risks[i] <= risks[i + 1], f"遺忘風險未隨天數增加：{risks}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
