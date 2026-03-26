"""
動態難度調整服務單元測試

測試覆蓋率目標：≥ 85%
"""

import pytest
import math
from datetime import datetime
import sys
import os

# Add backend/app/services to path
SERVICES_DIR = os.path.join(os.path.dirname(__file__), '..', 'edict', 'backend', 'app', 'services')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'edict', 'backend', 'app'))

# Import directly from file
import importlib.util
spec = importlib.util.spec_from_file_location(
    "adaptive_difficulty",
    os.path.join(SERVICES_DIR, "adaptive_difficulty.py")
)
adaptive_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adaptive_module)

AdaptiveDifficultyService = adaptive_module.AdaptiveDifficultyService
ItemParameters = adaptive_module.ItemParameters
UserProgress = adaptive_module.UserProgress
ItemResponse = adaptive_module.ItemResponse
IRT2PLModel = adaptive_module.IRT2PLModel
get_service = adaptive_module.get_service


class TestIRT2PLModel:
    """IRT 2PL 模型測試"""
    
    def test_probability_midpoint(self):
        """測試 θ=b 時 P=0.5"""
        p = IRT2PLModel.probability(theta=0.0, a=1.0, b=0.0)
        assert abs(p - 0.5) < 0.001
    
    def test_probability_high_ability(self):
        """測試 θ>>b 時 P≈1"""
        p = IRT2PLModel.probability(theta=2.0, a=1.0, b=-1.0)
        assert p > 0.9
    
    def test_probability_low_ability(self):
        """測試 θ<<b 時 P≈0"""
        p = IRT2PLModel.probability(theta=-2.0, a=1.0, b=1.0)
        assert p < 0.1
    
    def test_probability_discrimination_effect(self):
        """測試區分度 a 的影響"""
        # 高區分度時曲線更陡峭
        p_high_a = IRT2PLModel.probability(theta=0.5, a=2.0, b=0.0)
        p_low_a = IRT2PLModel.probability(theta=0.5, a=0.5, b=0.0)
        assert p_high_a > p_low_a
    
    def test_probability_bounds(self):
        """測試概率邊界"""
        p1 = IRT2PLModel.probability(theta=100, a=1.0, b=-100)
        p2 = IRT2PLModel.probability(theta=-100, a=1.0, b=100)
        
        assert 0.0 <= p1 <= 1.0
        assert 0.0 <= p2 <= 1.0
    
    def test_log_likelihood(self):
        """測試對數似然計算"""
        responses = [
            (1.0, 0.0, True),   # a=1, b=0, correct
            (1.0, 0.0, False),  # a=1, b=0, wrong
        ]
        
        ll = IRT2PLModel.log_likelihood(theta=0.0, responses=responses)
        
        # 當θ=b=0 時，P=0.5，LL = log(0.5) + log(0.5)
        expected_ll = 2 * math.log(0.5)
        assert abs(ll - expected_ll) < 0.01
    
    def test_estimate_ability_convergence(self):
        """測試能力估計收斂"""
        import random
        random.seed(42)
        
        # 生成模擬數據：θ=0.5 的用戶
        responses = []
        true_theta = 0.5
        for _ in range(30):
            a, b = 1.0, 0.0
            p = IRT2PLModel.probability(true_theta, a, b)
            # 按概率生成正確/錯誤（更真實的模擬）
            correct = (random.random() < p)
            responses.append((a, b, correct))
        
        theta_est, std = IRT2PLModel.estimate_ability(responses, theta_init=0.0)
        
        # 估計值應該在合理範圍內（不要求非常精確，因為有隨機性）
        assert -2.0 < theta_est < 2.0
        assert std > 0
        assert std < 1.0  # 30 題後標準誤應該較小
    
    def test_estimate_ability_insufficient_data(self):
        """測試數據不足時的處理"""
        responses = [(1.0, 0.0, True)]  # 只有 1 題
        
        theta, std = IRT2PLModel.estimate_ability(responses, theta_init=0.0)
        
        # 應該返回初始值和較大標準誤
        assert theta == 0.0
        assert std >= 1.0


class TestAdaptiveDifficultyService:
    """動態難度調整服務測試"""
    
    @pytest.fixture
    def service(self):
        """創建服務實例"""
        return AdaptiveDifficultyService()
    
    def test_register_item(self, service):
        """測試註冊題目"""
        item = service.register_item(
            item_id="item_001",
            difficulty=0.0,
            discrimination=1.2,
            knowledge_point_id="kp_01"
        )
        
        assert item.item_id == "item_001"
        assert item.difficulty == 0.0
        assert item.discrimination == 1.2
        assert item.difficulty_level == 3  # L3: -0.5 <= b < 0.5
    
    def test_register_item_clamps_difficulty(self, service):
        """測試難度參數限制在 [-3, 3]"""
        item1 = service.register_item("item_001", difficulty=5.0, discrimination=1.0)
        item2 = service.register_item("item_002", difficulty=-5.0, discrimination=1.0)
        
        assert item1.difficulty == 3.0
        assert item2.difficulty == -3.0
    
    def test_register_item_clamps_discrimination(self, service):
        """測試區分度參數限制在 [0.5, 2.0]"""
        item1 = service.register_item("item_001", difficulty=0.0, discrimination=3.0)
        item2 = service.register_item("item_002", difficulty=0.0, discrimination=0.1)
        
        assert item1.discrimination == 2.0
        assert item2.discrimination == 0.5
    
    def test_difficulty_level_mapping(self, service):
        """測試難度等級映射"""
        # L1: b < -1.5
        item_l1 = service.register_item("item_l1", difficulty=-2.0, discrimination=1.0)
        assert item_l1.difficulty_level == 1
        
        # L2: -1.5 ≤ b < -0.5
        item_l2 = service.register_item("item_l2", difficulty=-1.0, discrimination=1.0)
        assert item_l2.difficulty_level == 2
        
        # L3: -0.5 ≤ b < 0.5
        item_l3 = service.register_item("item_l3", difficulty=0.0, discrimination=1.0)
        assert item_l3.difficulty_level == 3
        
        # L4: 0.5 ≤ b < 1.5
        item_l4 = service.register_item("item_l4", difficulty=1.0, discrimination=1.0)
        assert item_l4.difficulty_level == 4
        
        # L5: b ≥ 1.5
        item_l5 = service.register_item("item_l5", difficulty=2.0, discrimination=1.0)
        assert item_l5.difficulty_level == 5
    
    def test_cold_start_detection(self, service):
        """測試冷啟動檢測"""
        service.register_item("item_001", difficulty=0.0, discrimination=1.0)
        
        # 新用戶處於冷啟動期
        assert service.is_cold_start("new_user") is True
        
        # 作答 5 題後退出冷啟動
        for i in range(5):
            service.update_ability("new_user", "item_001", correct=True, response_time=30.0)
        
        assert service.is_cold_start("new_user") is False
    
    def test_cold_start_item_selection(self, service):
        """測試冷啟動期題目選擇"""
        service.register_item("item_l1", difficulty=-2.0, discrimination=1.0)
        service.register_item("item_l3", difficulty=0.0, discrimination=1.0)
        service.register_item("item_l5", difficulty=2.0, discrimination=1.0)
        
        candidate_items = ["item_l1", "item_l3", "item_l5"]
        
        # 冷啟動期應該選擇 L3 題目
        next_item = service.get_next_item("new_user", candidate_items)
        
        assert next_item["is_cold_start"] is True
        assert next_item["difficulty_level"] == 3
        assert next_item["item_id"] == "item_l3"
    
    def test_post_cold_start_item_selection(self, service):
        """測試冷啟動後題目選擇"""
        # 註冊題目
        service.register_item("item_001", difficulty=-1.0, discrimination=1.0)
        service.register_item("item_002", difficulty=0.0, discrimination=1.0)
        service.register_item("item_003", difficulty=1.0, discrimination=1.0)
        
        candidate_items = ["item_001", "item_002", "item_003"]
        
        # 先完成冷啟動（5 題）
        for _ in range(5):
            service.update_ability("user_001", "item_002", correct=True, response_time=30.0)
        
        # 冷啟動後選擇匹配能力的題目
        next_item = service.get_next_item("user_001", candidate_items)
        
        assert next_item["is_cold_start"] is False
        assert "estimated_success_rate" in next_item
    
    def test_update_ability_cold_start(self, service):
        """測試冷啟動期能力更新"""
        service.register_item("item_001", difficulty=0.0, discrimination=1.0)
        
        result = service.update_ability("user_001", "item_001", correct=True, response_time=30.0)
        
        assert result["is_cold_start"] is True
        assert result["new_ability"] == 0.0  # 冷啟動期不更新能力
    
    def test_update_ability_post_cold_start(self, service):
        """測試冷啟動後能力更新"""
        service.register_item("item_001", difficulty=0.0, discrimination=1.0)
        
        # 完成冷啟動
        for _ in range(5):
            service.update_ability("user_001", "item_001", correct=True, response_time=30.0)
        
        # 第 6 題開始更新能力
        result = service.update_ability("user_001", "item_001", correct=True, response_time=30.0)
        
        assert result["is_cold_start"] is False
        assert "new_ability" in result
        assert "confidence_interval" in result
    
    def test_update_ability_invalid_item(self, service):
        """測試無效題目 ID 拋出錯誤"""
        with pytest.raises(ValueError, match="未知的題目 ID"):
            service.update_ability("user_001", "nonexistent_item", correct=True, response_time=30.0)
    
    def test_level_upgrade_on_consecutive_correct(self, service):
        """測試連續答對升級"""
        service.register_item("item_001", difficulty=0.0, discrimination=1.0)
        
        # 完成冷啟動
        for _ in range(5):
            service.update_ability("user_001", "item_001", correct=True, response_time=30.0)
        
        # 連續 3 題正確應該升級
        for _ in range(3):
            service.update_ability("user_001", "item_001", correct=True, response_time=30.0)
        
        progress = service.get_user_progress("user_001")
        assert progress.current_level == 4  # 從 L3 升到 L4
    
    def test_level_downgrade_on_consecutive_wrong(self, service):
        """測試連續答錯降級"""
        service.register_item("item_001", difficulty=0.0, discrimination=1.0)
        
        # 完成冷啟動
        for _ in range(5):
            service.update_ability("user_001", "item_001", correct=False, response_time=30.0)
        
        # 連續 2 題錯誤應該降級
        for _ in range(2):
            service.update_ability("user_001", "item_001", correct=False, response_time=30.0)
        
        progress = service.get_user_progress("user_001")
        assert progress.current_level == 2  # 從 L3 降到 L2
    
    def test_level_bounds(self, service):
        """測試等級邊界（不超過 L1 或 L5）"""
        service.register_item("item_001", difficulty=0.0, discrimination=1.0)
        
        # 測試 L5 上限
        progress = service.get_user_progress("user_001")
        progress.current_level = 5
        
        # 即使連續答對也不超過 L5
        for _ in range(3):
            service.update_ability("user_001", "item_001", correct=True, response_time=30.0)
        
        assert progress.current_level == 5
        
        # 測試 L1 下限
        progress.current_level = 1
        for _ in range(2):
            service.update_ability("user_001", "item_001", correct=False, response_time=30.0)
        
        assert progress.current_level == 1
    
    def test_get_user_progress(self, service):
        """測試獲取用戶進度"""
        service.register_item("item_001", difficulty=0.0, discrimination=1.0)
        
        # 作答 10 題
        for i in range(10):
            service.update_ability("user_001", "item_001", correct=(i % 2 == 0), response_time=30.0)
        
        progress = service.get_user_progress("user_001")
        
        assert progress.questions_answered == 10
        assert progress.total_answered == 10
        assert progress.total_correct == 5  # 5 題正確
    
    def test_get_user_progress_to_dict(self, service):
        """測試用戶進度序列化"""
        progress = UserProgress(user_id="user_001")
        data = progress.to_dict()
        
        assert data["user_id"] == "user_001"
        assert data["current_level"] == 3
        assert "cold_start_complete" in data
        assert "accuracy_rate" in data
    
    def test_item_parameters_to_dict(self, service):
        """測試題目參數序列化"""
        item = service.register_item("item_001", difficulty=0.5, discrimination=1.2)
        data = item.to_dict()
        
        assert data["item_id"] == "item_001"
        assert data["difficulty"] == 0.5
        assert data["discrimination"] == 1.2
        assert "calibration_date" in data
    
    def test_get_item_parameters(self, service):
        """測試獲取題目參數"""
        service.register_item("item_001", difficulty=0.5, discrimination=1.2)
        
        item = service.get_item_parameters("item_001")
        assert item is not None
        assert item.difficulty == 0.5
    
    def test_get_item_parameters_nonexistent(self, service):
        """測試獲取不存在的題目"""
        item = service.get_item_parameters("nonexistent")
        assert item is None
    
    def test_get_response_history(self, service):
        """測試獲取作答歷史"""
        service.register_item("item_001", difficulty=0.0, discrimination=1.0)
        
        for _ in range(3):
            service.update_ability("user_001", "item_001", correct=True, response_time=30.0)
        
        history = service.get_response_history("user_001")
        assert len(history) == 3
    
    def test_calibrate_item_from_responses(self, service):
        """測試題目標定"""
        # 生成模擬數據
        responses = [(0.0, True)] * 15 + [(0.0, False)] * 5  # 75% 正確率
        
        item = service.calibrate_item_from_responses("item_001", responses)
        
        assert item.item_id == "item_001"
        assert item.calibrated_by == "sample_test"
    
    def test_calibrate_item_insufficient_data(self, service):
        """測試標定數據不足"""
        responses = [(0.0, True)] * 5  # 只有 5 題
        
        with pytest.raises(ValueError, match="至少需要 10 個"):
            service.calibrate_item_from_responses("item_001", responses)


class TestGetService:
    """服務單例測試"""
    
    def test_get_service_returns_singleton(self):
        """測試獲取服務單例"""
        service1 = get_service()
        service2 = get_service()
        
        assert service1 is service2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
