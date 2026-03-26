"""
遺忘曲線校準服務單元測試

測試覆蓋率目標：≥ 85%
"""

import pytest
from datetime import datetime, timedelta
import sys
import os

# Add backend/app/services to path
SERVICES_DIR = os.path.join(os.path.dirname(__file__), '..', 'edict', 'backend', 'app', 'services')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'edict', 'backend', 'app'))

# Import directly from file
import importlib.util
spec = importlib.util.spec_from_file_location(
    "forgetting_curve",
    os.path.join(SERVICES_DIR, "forgetting_curve.py")
)
fc_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fc_module)

ForgettingCurveService = fc_module.ForgettingCurveService
ForgettingCurve = fc_module.ForgettingCurve
ReviewRecord = fc_module.ReviewRecord
EbbinghausModel = fc_module.EbbinghausModel
SM2Algorithm = fc_module.SM2Algorithm
get_service = fc_module.get_service


class TestEbbinghausModel:
    """Ebbinghaus 遺忘曲線模型測試"""
    
    def test_retention_rate_initial(self):
        """測試初始保留率為 100%"""
        R = EbbinghausModel.retention_rate(0, S=2.5)
        assert abs(R - 1.0) < 0.001
    
    def test_retention_rate_decays(self):
        """測試保留率隨時間衰減"""
        R1 = EbbinghausModel.retention_rate(1, S=2.5)
        R7 = EbbinghausModel.retention_rate(7, S=2.5)
        
        assert R1 > R7  # 7 天後保留率更低
    
    def test_retention_rate_larger_S_slower_decay(self):
        """測試 S 越大衰減越慢"""
        R_small_S = EbbinghausModel.retention_rate(7, S=1.0)
        R_large_S = EbbinghausModel.retention_rate(7, S=5.0)
        
        assert R_large_S > R_small_S
    
    def test_retention_rate_bounds(self):
        """測試保留率邊界"""
        R = EbbinghausModel.retention_rate(100, S=0.1)
        assert 0.0 <= R <= 1.0
    
    def test_time_to_threshold(self):
        """測試到達閾值的時間計算"""
        # S=2.5，到達 70% 保留率需要的時間
        t = EbbinghausModel.time_to_threshold(0.7, S=2.5)
        
        # t = -S * ln(0.7) ≈ 2.5 * 0.357 ≈ 0.89 天
        assert 0.5 < t < 1.5
    
    def test_time_to_threshold_invalid_input(self):
        """測試無效輸入處理"""
        t1 = EbbinghausModel.time_to_threshold(0, S=2.5)
        t2 = EbbinghausModel.time_to_threshold(1, S=2.5)
        
        # 邊界情況應返回默認值
        assert t1 > 0
        assert t2 > 0


class TestSM2Algorithm:
    """SM-2 算法測試"""
    
    def test_initial_intervals(self):
        """測試初始間隔"""
        assert SM2Algorithm.INITIAL_INTERVALS == [1, 3, 7]
    
    def test_forget_threshold(self):
        """測試遺忘閾值"""
        assert SM2Algorithm.FORGET_THRESHOLD == 3
    
    def test_interval_on_forget(self):
        """測試遺忘時重置間隔"""
        interval = SM2Algorithm.calculate_next_interval(
            ease_factor=2.5, review_number=5, quality_score=2, current_interval=10.0
        )
        assert interval == 1.0  # 重置為 1 天
    
    def test_interval_first_review(self):
        """測試第一次復習間隔"""
        interval = SM2Algorithm.calculate_next_interval(
            ease_factor=2.5, review_number=0, quality_score=4, current_interval=0.0
        )
        assert interval == 1.0
    
    def test_interval_second_review(self):
        """測試第二次復習間隔"""
        interval = SM2Algorithm.calculate_next_interval(
            ease_factor=2.5, review_number=1, quality_score=4, current_interval=1.0
        )
        assert interval == 3.0
    
    def test_interval_third_review(self):
        """測試第三次復習間隔"""
        interval = SM2Algorithm.calculate_next_interval(
            ease_factor=2.5, review_number=2, quality_score=4, current_interval=3.0
        )
        assert interval == 7.0
    
    def test_interval_subsequent_review(self):
        """測試後續復習間隔"""
        interval = SM2Algorithm.calculate_next_interval(
            ease_factor=2.5, review_number=3, quality_score=4, current_interval=7.0
        )
        assert interval == 7.0 * 2.5  # 7 * EF
    
    def test_update_ease_factor_high_quality(self):
        """測試高質量更新難度係數"""
        new_ef = SM2Algorithm.update_ease_factor(2.5, quality_score=5)
        assert new_ef > 2.5
        assert new_ef <= SM2Algorithm.EF_MAX
    
    def test_update_ease_factor_low_quality(self):
        """測試低質量更新難度係數"""
        new_ef = SM2Algorithm.update_ease_factor(2.5, quality_score=0)
        assert new_ef < 2.5
        assert new_ef >= SM2Algorithm.EF_MIN
    
    def test_update_ease_factor_bounds(self):
        """測試難度係數邊界"""
        ef1 = SM2Algorithm.update_ease_factor(2.9, quality_score=5)
        ef2 = SM2Algorithm.update_ease_factor(1.4, quality_score=0)
        
        assert ef1 <= SM2Algorithm.EF_MAX
        assert ef2 >= SM2Algorithm.EF_MIN


class TestForgettingCurveService:
    """遺忘曲線服務測試"""
    
    @pytest.fixture
    def service(self):
        """創建服務實例"""
        return ForgettingCurveService()
    
    def test_learn_item(self, service):
        """測試學習新知識點"""
        curve = service.learn_item("user_001", "item_001", quality_score=5)
        
        assert curve.user_id == "user_001"
        assert curve.item_id == "item_001"
        assert curve.decay_coefficient > 0
        assert len(curve.reviews) == 1
        assert curve.interval_days == 1.0  # 第一次復習 1 天後
    
    def test_learn_item_low_quality(self, service):
        """測試低質量學習不添加復習記錄"""
        curve = service.learn_item("user_001", "item_001", quality_score=2)
        
        # 質量<3，不添加初始復習記錄
        assert len(curve.reviews) == 0
    
    def test_review_item(self, service):
        """測試復習知識點"""
        service.learn_item("user_001", "item_001", quality_score=5)
        curve = service.review_item("user_001", "item_001", quality_score=4)
        
        assert len(curve.reviews) == 2
        assert curve.reviews[-1].quality_score == 4
    
    def test_review_item_updates_ease_factor(self, service):
        """測試復習更新難度係數"""
        service.learn_item("user_001", "item_001", quality_score=5)
        
        curve1 = service.review_item("user_001", "item_001", quality_score=5)
        ef1 = curve1.ease_factor
        
        curve2 = service.review_item("user_001", "item_001", quality_score=5)
        ef2 = curve2.ease_factor
        
        assert ef2 > ef1  # 連續高質量，EF 增加
    
    def test_review_item_nonexistent_raises_error(self, service):
        """測試復習不存在的知識點拋出錯誤"""
        with pytest.raises(ValueError, match="未學習"):
            service.review_item("user_001", "nonexistent_item", quality_score=4)
    
    def test_get_due_items(self, service):
        """測試獲取待復習項目"""
        service.learn_item("user_001", "item_001", quality_score=5)
        
        # 剛學習，不應該有待復習項目
        due_items = service.get_due_items("user_001")
        assert len(due_items) == 0
    
    def test_get_due_items_approaching(self, service):
        """測試即將到期的項目"""
        # 學習一個質量低的項目（更快到期）
        curve = service.learn_item("user_001", "item_001", quality_score=3)
        
        # 手動設置下次復習時間為現在
        curve.next_review = datetime.now()
        
        due_items = service.get_due_items("user_001")
        assert len(due_items) == 1
        assert due_items[0]["item_id"] == "item_001"
    
    def test_get_due_items_priority_order(self, service):
        """測試待復習項目按優先級排序"""
        curve1 = service.learn_item("user_001", "item_001", quality_score=5)
        curve2 = service.learn_item("user_001", "item_002", quality_score=3)
        
        # 都設置為到期
        curve1.next_review = datetime.now()
        curve2.next_review = datetime.now()
        
        due_items = service.get_due_items("user_001")
        
        # 質量低的優先級更高
        assert len(due_items) == 2
        assert due_items[0]["item_id"] == "item_002"  # 質量低，保留率低，優先級高
    
    def test_calculate_current_retention(self, service):
        """測試當前保留率計算"""
        curve = service.learn_item("user_001", "item_001", quality_score=5)
        
        # 剛學習時保留率應該接近 100%
        retention = service._calculate_current_retention(curve)
        assert retention > 0.8
    
    def test_forgetting_curve_to_dict(self, service):
        """測試遺忘曲線序列化"""
        curve = service.learn_item("user_001", "item_001", quality_score=5)
        data = curve.to_dict()
        
        assert data["user_id"] == "user_001"
        assert data["item_id"] == "item_001"
        assert "decay_coefficient" in data
        assert "next_review" in data
        assert "retention_rate" in data
    
    def test_review_record_to_dict(self):
        """測試復習記錄序列化"""
        record = ReviewRecord(review_number=1, quality_score=4, interval_days=3.0)
        data = record.to_dict()
        
        assert data["review_number"] == 1
        assert data["quality_score"] == 4
        assert data["interval_days"] == 3.0
    
    def test_get_forgetting_curve(self, service):
        """測試獲取遺忘曲線"""
        service.learn_item("user_001", "item_001", quality_score=5)
        
        curve = service.get_forgetting_curve("user_001", "item_001")
        assert curve is not None
        assert curve.item_id == "item_001"
    
    def test_get_forgetting_curve_nonexistent(self, service):
        """測試獲取不存在的遺忘曲線"""
        curve = service.get_forgetting_curve("user_001", "nonexistent")
        assert curve is None
    
    def test_calibrate_decay_coefficient(self, service):
        """測試衰減係數校準"""
        # 生成模擬數據
        review_history = [
            (1, 5), (3, 4), (7, 4), (14, 3), (30, 2)
        ]
        
        S = service.calibrate_decay_coefficient("user_001", review_history)
        
        assert S > 0
        assert S <= 10.0
    
    def test_calibrate_decay_coefficient_insufficient_data(self, service):
        """測試數據不足時的校準"""
        review_history = [(1, 5), (3, 4)]  # 只有 2 條
        
        S = service.calibrate_decay_coefficient("user_001", review_history)
        
        # 應該返回默認值
        assert S == 2.5
    
    def test_get_review_statistics(self, service):
        """測試獲取復習統計"""
        service.learn_item("user_001", "item_001", quality_score=5)
        service.learn_item("user_001", "item_002", quality_score=4)
        
        stats = service.get_review_statistics("user_001")
        
        assert stats["total_items"] == 2
        assert stats["total_reviews"] == 2  # 每個項目初始復習 1 次
        assert "avg_retention_rate" in stats
        assert "due_items" in stats
    
    def test_adjust_decay_coefficient_on_forget(self, service):
        """測試遺忘時調整衰減係數"""
        service.learn_item("user_001", "item_001", quality_score=5)
        
        # 模擬遺忘
        initial_S = service._get_user_decay_coefficient("user_001")
        service._adjust_decay_coefficient("user_001", days_elapsed=7, quality_score=2)
        new_S = service._get_user_decay_coefficient("user_001")
        
        # 遺忘後 S 應該減小
        assert new_S < initial_S
    
    def test_adjust_decay_coefficient_on_good_memory(self, service):
        """測試記憶好時調整衰減係數"""
        service.learn_item("user_001", "item_001", quality_score=5)
        
        initial_S = service._get_user_decay_coefficient("user_001")
        service._adjust_decay_coefficient("user_001", days_elapsed=7, quality_score=5)
        new_S = service._get_user_decay_coefficient("user_001")
        
        # 記憶好 S 應該增大
        assert new_S > initial_S


class TestGetService:
    """服務單例測試"""
    
    def test_get_service_returns_singleton(self):
        """測試獲取服務單例"""
        service1 = get_service()
        service2 = get_service()
        
        assert service1 is service2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
