"""
學習風格識別服務單元測試

測試覆蓋率目標：≥ 85%
"""

import pytest
import sys
import os
from datetime import datetime

# Add backend/app/services to path directly
SERVICES_DIR = os.path.join(os.path.dirname(__file__), '..', 'edict', 'backend', 'app', 'services')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'edict', 'backend', 'app'))
sys.path.insert(0, SERVICES_DIR)

# Import directly from file to avoid package import issues
import importlib.util
spec = importlib.util.spec_from_file_location(
    "learning_style",
    os.path.join(SERVICES_DIR, "learning_style.py")
)
learning_style_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(learning_style_module)

LearningStyleService = learning_style_module.LearningStyleService
LearningStyle = learning_style_module.LearningStyle
BehaviorData = learning_style_module.BehaviorData
VARKStyle = learning_style_module.VARKStyle
VARK_QUESTIONS = learning_style_module.VARK_QUESTIONS
get_service = learning_style_module.get_service


class TestVARKQuestions:
    """VARK 問卷題目測試"""
    
    def test_questionnaire_has_12_questions(self):
        """驗證問卷有 12 題"""
        assert len(VARK_QUESTIONS) == 12
    
    def test_each_question_has_4_options(self):
        """驗證每題有 4 個選項"""
        for question in VARK_QUESTIONS:
            assert len(question["options"]) == 4
    
    def test_options_cover_all_vark_styles(self):
        """驗證選項覆蓋 V/A/R/K 四種風格"""
        styles = {"V", "A", "R", "K"}
        for question in VARK_QUESTIONS:
            question_styles = {opt["style"] for opt in question["options"]}
            assert question_styles == styles


class TestLearningStyleService:
    """學習風格服務測試"""
    
    @pytest.fixture
    def service(self):
        """創建服務實例"""
        return LearningStyleService()
    
    def test_get_questionnaire(self, service):
        """測試獲取問卷"""
        questions = service.get_questionnaire()
        assert len(questions) == 12
    
    def test_submit_complete_questionnaire(self, service):
        """測試提交完整問卷"""
        answers = [
            {"question_id": q["id"], "selected_option": 0}
            for q in VARK_QUESTIONS
        ]
        
        style = service.submit_questionnaire("user_001", answers)
        
        assert style.user_id == "user_001"
        assert style.questionnaire_completed is True
        assert style.v_score == 100.0  # 全选 V 選項
        assert style.dominant_style == "V"
    
    def test_submit_incomplete_questionnaire_raises_error(self, service):
        """測試提交不完整問卷拋出錯誤"""
        answers = [
            {"question_id": "q1", "selected_option": 0}
        ]  # 只有 1 題
        
        with pytest.raises(ValueError, match="必須完成全部"):
            service.submit_questionnaire("user_001", answers)
    
    def test_submit_invalid_question_id_raises_error(self, service):
        """測試提交無效題目 ID 拋出錯誤"""
        answers = [
            {"question_id": "q999", "selected_option": 0}
        ] + [
            {"question_id": q["id"], "selected_option": 0}
            for q in VARK_QUESTIONS[1:]
        ]
        
        with pytest.raises(ValueError, match="無效的題目 ID"):
            service.submit_questionnaire("user_001", answers)
    
    def test_submit_invalid_option_index_raises_error(self, service):
        """測試提交無效選項索引拋出錯誤"""
        answers = [
            {"question_id": "q1", "selected_option": 10}  # 超出範圍
        ] + [
            {"question_id": q["id"], "selected_option": 0}
            for q in VARK_QUESTIONS[1:]
        ]
        
        with pytest.raises(ValueError, match="無效的選項索引"):
            service.submit_questionnaire("user_001", answers)
    
    def test_balanced_answers_yield_equal_scores(self, service):
        """測試平衡答案產生均衡分數"""
        # 每種風格各選 3 題
        answers = []
        style_sequence = ["V", "A", "R", "K"] * 3  # 12 題
        
        for i, q in enumerate(VARK_QUESTIONS):
            # 找到對應風格的選項索引
            target_style = style_sequence[i]
            for idx, opt in enumerate(q["options"]):
                if opt["style"] == target_style:
                    answers.append({
                        "question_id": q["id"],
                        "selected_option": idx
                    })
                    break
        
        style = service.submit_questionnaire("user_002", answers)
        
        # 每種風格應該各得 25 分（3/12 * 100）
        assert abs(style.v_score - 25.0) < 0.1
        assert abs(style.a_score - 25.0) < 0.1
        assert abs(style.r_score - 25.0) < 0.1
        assert abs(style.k_score - 25.0) < 0.1
    
    def test_confidence_calculation(self, service):
        """測試置信度計算"""
        # 極端情況：全部選 V
        answers = [
            {"question_id": q["id"], "selected_option": 0}
            for q in VARK_QUESTIONS
        ]
        
        style = service.submit_questionnaire("user_003", answers)
        
        # V=100, 其他=0, 差距=100, 置信度=min(100/50, 1)=1.0
        assert style.confidence == 1.0
    
    def test_record_behavior_click(self, service):
        """測試記錄點擊行為"""
        service.record_behavior("user_004", "visual", "click")
        service.record_behavior("user_004", "visual", "click")
        
        behavior = service.get_behavior_data("user_004")
        assert behavior is not None
        assert behavior.visual_clicks == 2
    
    def test_record_behavior_time(self, service):
        """測試記錄時長行為"""
        service.record_behavior("user_005", "auditory", "time", 300.0)
        service.record_behavior("user_005", "auditory", "time", 200.0)
        
        behavior = service.get_behavior_data("user_005")
        assert behavior.auditory_time == 500.0
    
    def test_record_behavior_interaction(self, service):
        """測試記錄互動行為"""
        service.record_behavior("user_006", "kinesthetic", "interaction")
        service.record_behavior("user_006", "kinesthetic", "interaction")
        service.record_behavior("user_006", "kinesthetic", "interaction")
        
        behavior = service.get_behavior_data("user_006")
        assert behavior.kinesthetic_interactions == 3
    
    def test_calculate_behavior_scores_no_data(self, service):
        """測試無行為數據時的默認得分"""
        scores = service.calculate_behavior_scores("nonexistent_user")
        
        # 應該返回平均分
        assert scores["V"] == 25.0
        assert scores["A"] == 25.0
        assert scores["R"] == 25.0
        assert scores["K"] == 25.0
    
    def test_calculate_behavior_scores_with_data(self, service):
        """測試有行為數據時的得分計算"""
        # 大量視覺行為
        for _ in range(20):
            service.record_behavior("user_007", "visual", "click")
        service.record_behavior("user_007", "visual", "time", 2000.0)
        
        scores = service.calculate_behavior_scores("user_007")
        
        # 視覺得分應該最高
        assert scores["V"] > scores["A"]
        assert scores["V"] > scores["R"]
        assert scores["V"] > scores["K"]
    
    def test_calculate_final_style_questionnaire_only(self, service):
        """測試只有問卷數據時的最終風格"""
        answers = [
            {"question_id": q["id"], "selected_option": 2}  # 全选 R 選項
            for q in VARK_QUESTIONS
        ]
        
        service.submit_questionnaire("user_008", answers)
        final_style = service.calculate_final_style("user_008")
        
        assert final_style.dominant_style == "R"
        assert final_style.r_score == 100.0
        assert final_style.behavior_data_collected is False
    
    def test_calculate_final_style_weighted(self, service):
        """測試問卷 + 行為加權計算"""
        # 問卷：全选 V（100 分）
        answers = [
            {"question_id": q["id"], "selected_option": 0}
            for q in VARK_QUESTIONS
        ]
        service.submit_questionnaire("user_009", answers)
        
        # 行為：全选 K
        for _ in range(20):
            service.record_behavior("user_009", "kinesthetic", "click")
        service.record_behavior("user_009", "kinesthetic", "time", 2000.0)
        
        final_style = service.calculate_final_style("user_009")
        
        # V: 100*0.6 + 0*0.4 = 60
        # K: 0*0.6 + 100*0.4 = 40
        assert abs(final_style.v_score - 60.0) < 1.0
        assert abs(final_style.k_score - 40.0) < 1.0
    
    def test_get_learning_style_nonexistent_user(self, service):
        """測試獲取不存在的用戶風格"""
        style = service.get_learning_style("nonexistent")
        assert style is None
    
    def test_get_behavior_data_nonexistent_user(self, service):
        """測試獲取不存在的用戶行為"""
        behavior = service.get_behavior_data("nonexistent")
        assert behavior is None
    
    def test_recommend_content_no_style(self, service):
        """測試無風格時的推薦（返回原始順序）"""
        content_pool = [
            {"id": "1", "type": "video"},
            {"id": "2", "type": "article"},
        ]
        
        recommendations = service.recommend_content("nonexistent", content_pool)
        
        assert len(recommendations) == 2
        assert recommendations[0]["id"] == "1"
        assert recommendations[1]["id"] == "2"
    
    def test_recommend_content_with_style(self, service):
        """測試有風格時的推薦"""
        # 創建視覺型用戶
        answers = [
            {"question_id": q["id"], "selected_option": 0}
            for q in VARK_QUESTIONS
        ]
        service.submit_questionnaire("user_010", answers)
        
        content_pool = [
            {"id": "1", "type": "video", "tags": ["tutorial"]},
            {"id": "2", "type": "article", "tags": ["theory"]},
            {"id": "3", "type": "podcast", "tags": ["audio"]},
        ]
        
        recommendations = service.recommend_content("user_010", content_pool)
        
        # 視頻應該排第一（匹配視覺風格）
        assert recommendations[0]["id"] == "1"
        assert recommendations[0]["matched_style"] == "V"
        assert recommendations[0]["recommendation_score"] > 50
    
    def test_recommend_content_tag_bonus(self, service):
        """測試標籤匹配加分"""
        # 創建視覺型用戶
        answers = [
            {"question_id": q["id"], "selected_option": 0}
            for q in VARK_QUESTIONS
        ]
        service.submit_questionnaire("user_011", answers)
        
        content_pool = [
            {"id": "1", "type": "video", "tags": ["visual", "tutorial"]},  # 2 個匹配標籤
            {"id": "2", "type": "video", "tags": ["general"]},  # 無匹配標籤
        ]
        
        recommendations = service.recommend_content("user_011", content_pool)
        
        # 有匹配標籤的分數應該更高
        assert recommendations[0]["id"] == "1"
        assert recommendations[0]["recommendation_score"] > recommendations[1]["recommendation_score"]
    
    def test_learning_style_to_dict(self, service):
        """測試 LearningStyle 序列化"""
        answers = [
            {"question_id": q["id"], "selected_option": 0}
            for q in VARK_QUESTIONS
        ]
        style = service.submit_questionnaire("user_012", answers)
        
        data = style.to_dict()
        
        assert data["user_id"] == "user_012"
        assert data["v_score"] == 100.0
        assert data["dominant_style"] == "V"
        assert data["questionnaire_completed"] is True
        assert "last_updated" in data
    
    def test_behavior_data_to_dict(self, service):
        """測試 BehaviorData 序列化"""
        service.record_behavior("user_013", "visual", "click")
        service.record_behavior("user_013", "visual", "time", 100.0)
        
        behavior = service.get_behavior_data("user_013")
        data = behavior.to_dict()
        
        assert data["user_id"] == "user_013"
        assert data["clicks"]["visual"] == 1
        assert data["time_spent"]["visual"] == 100.0


class TestGetService:
    """服務單例測試"""
    
    def test_get_service_returns_singleton(self):
        """測試獲取服務單例"""
        service1 = get_service()
        service2 = get_service()
        
        assert service1 is service2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
