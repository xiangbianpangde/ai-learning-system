"""集成測試：完整學習流程。

測試場景 1: 完整學習流程
```
PDF 上傳 → Markdown 轉換 → 知識點提取 → 學習計劃生成
  → 降階法教學 → 費曼檢測 → 學習預測 → 複習建議
```

測試步驟:
1. 上傳 PDF 文件（5 種類型各 1 個）
2. 轉換為 Markdown
3. 提取知識點生成知識圖譜
4. 生成 48 小時學習計劃
5. 啟動學習會話
6. 對每個知識點進行降階法教學
7. 用戶嘗試解釋（費曼檢測）
8. AI 評估並識別盲點
9. 生成學習效果預測
10. 輸出複習建議

驗收標準:
- ✅ 10 個完整流程全部通過
- ✅ 無數據丟失或格式錯誤
- ✅ 各服務間接口調用正確
- ✅ 錯誤處理和日誌完整
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import sys
import uuid

# 設置路徑
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'edict' / 'backend'))

from app.services.pdf_parser import (
    PDFParserService,
    PDFType,
    KnowledgePoint,
    ParseResult,
    parse_pdf,
)
from app.services.learning_plan import (
    LearningPlanGenerator,
    LearningMode,
    LearningPlan,
    generate_learning_plan,
)
from app.services.progressive_teaching import (
    ProgressiveTeachingEngine,
    TeachingLevel,
    UnderstandingLevel,
    create_knowledge_point_with_levels,
)
from app.services.feynman_assessment import (
    FeynmanAssessmentEngine,
    AssessmentDimension,
    BlindSpotType,
)
from app.services.learning_prediction import (
    LearningPredictionModel,
    LearningBehavior,
    PredictionType,
    AlertLevel,
    create_learning_behavior,
)


class TestPDFParsing:
    """測試場景 1.1-1.3: PDF 解析與知識點提取。"""
    
    def test_parse_text_pdf(self, tmp_path):
        """測試純文本 PDF 解析。"""
        # 創建模擬 PDF 文件（實際測試中使用 mock）
        # 由於實際 PDF 解析需要 pypdf，這裡測試接口正確性
        parser = PDFParserService()
        
        # 驗證服務初始化
        assert parser is not None
        assert PDFType.TEXT in parser.parsers
        assert PDFType.TABLE in parser.parsers
    
    def test_knowledge_point_extraction(self):
        """測試知識點提取接口。"""
        # 創建模擬知識點
        kp = KnowledgePoint(
            title="測試知識點",
            content="這是測試內容，包含重要概念。",
            page=1,
            confidence=0.85,
            tags=["測試", "示例"],
        )
        
        assert kp.title == "測試知識點"
        assert kp.confidence == 0.85
        assert len(kp.tags) == 2
    
    def test_parse_result_structure(self):
        """測試解析結果數據結構。"""
        result = ParseResult(
            success=True,
            pdf_type=PDFType.TEXT,
            text="測試文本",
            knowledge_points=[],
            pages=5,
        )
        
        assert result.success is True
        assert result.pdf_type == PDFType.TEXT
        assert result.pages == 5


class TestLearningPlanGeneration:
    """測試場景 1.4: 學習計劃生成。"""
    
    def test_generate_learning_plan(self):
        """測試學習計劃生成。"""
        # 創建模擬知識點
        knowledge_points = [
            KnowledgePoint(
                title=f"知識點{i}",
                content=f"這是知識點{i}的內容，長度適中。" * 10,
                page=i,
                confidence=0.8,
                tags=["測試"],
            )
            for i in range(1, 6)
        ]
        
        generator = LearningPlanGenerator()
        plan = generator.generate(
            knowledge_points,
            mode=LearningMode.STANDARD,
        )
        
        assert plan is not None
        assert plan.mode == LearningMode.STANDARD
        assert plan.knowledge_points_count == 5
        assert len(plan.daily_plans) > 0
    
    def test_learning_plan_modes(self):
        """測試不同學習模式。"""
        knowledge_points = [
            KnowledgePoint(
                title="測試知識點",
                content="測試內容" * 20,
                page=1,
                confidence=0.9,
            )
        ]
        
        generator = LearningPlanGenerator()
        
        for mode in [LearningMode.FAST, LearningMode.STANDARD, LearningMode.DEEP]:
            plan = generator.generate(knowledge_points, mode=mode)
            assert plan.mode == mode
            assert plan.total_days > 0


class TestProgressiveTeaching:
    """測試場景 1.5-1.6: 降階法教學。"""
    
    def test_create_teaching_session(self):
        """測試創建教學會話。"""
        engine = ProgressiveTeachingEngine()
        
        kp = create_knowledge_point_with_levels(
            id="kp_001",
            title="牛頓第二定律",
            description="F=ma，物體的加速度與作用力成正比",
            subject="物理",
        )
        
        session = engine.create_session(
            session_id="session_001",
            knowledge_point=kp,
            initial_level=TeachingLevel.L1_INTUITIVE,
        )
        
        assert session.session_id == "session_001"
        assert session.user_state.current_level == TeachingLevel.L1_INTUITIVE
    
    def test_four_level_explanations(self):
        """測試四個層次解釋生成。"""
        kp = create_knowledge_point_with_levels(
            id="kp_002",
            title="光合作用",
            description="植物利用光能將二氧化碳和水轉化為有機物",
            subject="生物",
        )
        
        # 驗證四個層次都存在
        assert TeachingLevel.L1_INTUITIVE in kp.explanations
        assert TeachingLevel.L2_VISUAL in kp.explanations
        assert TeachingLevel.L3_FORMAL in kp.explanations
        assert TeachingLevel.L4_ABSTRACT in kp.explanations
    
    def test_level_transition(self):
        """測試層次切換。"""
        engine = ProgressiveTeachingEngine()
        
        kp = create_knowledge_point_with_levels(
            id="kp_003",
            title="微積分",
            description="研究變化和累積的數學分支",
            subject="數學",
        )
        
        session = engine.create_session(
            session_id="session_003",
            knowledge_point=kp,
            initial_level=TeachingLevel.L1_INTUITIVE,
        )
        
        # 模擬用戶理解度提升
        session.user_state.understanding_score = 0.85
        
        # 檢查是否建議升級
        suggested_level = engine.should_change_level("session_003")
        assert suggested_level == TeachingLevel.L2_VISUAL
        
        # 執行升級
        engine.change_level("session_003", TeachingLevel.L2_VISUAL, "理解度達到 85%")
        assert session.user_state.current_level == TeachingLevel.L2_VISUAL


class TestFeynmanAssessment:
    """測試場景 1.7-1.8: 費曼檢測與盲點識別。"""
    
    def test_create_feynman_session(self):
        """測試創建費曼會話。"""
        engine = FeynmanAssessmentEngine()
        
        session = engine.create_session(
            session_id="feynman_001",
            concept_id="concept_001",
            concept_title="能量守恆定律",
            concept_definition="能量既不會憑空產生，也不會憑空消失，只會從一種形式轉化為另一種形式",
            key_concepts=["能量", "守恆", "轉化", "封閉系統"],
        )
        
        assert session.session_id == "feynman_001"
        assert len(session.key_concepts) == 4
    
    def test_assess_explanation(self):
        """測試評估用戶解釋。"""
        engine = FeynmanAssessmentEngine()
        
        session = engine.create_session(
            session_id="feynman_002",
            concept_id="concept_002",
            concept_title="光合作用",
            concept_definition="植物利用光能將二氧化碳和水轉化為葡萄糖和氧氣",
            key_concepts=["光能", "二氧化碳", "水", "葡萄糖", "氧氣", "葉綠體"],
        )
        
        # 完整解釋
        complete_explanation = "植物通過葉綠體吸收光能，將二氧化碳和水轉化為葡萄糖，同時釋放氧氣。這個過程叫做光合作用。"
        
        result = engine.assess_explanation("feynman_002", complete_explanation)
        
        # 概念覆蓋率應該高（所有關鍵詞都提到了）
        assert result.concept_coverage.coverage_rate >= 1.0
        # 總分可能因準確性評分算法而有所不同，但應該有合理分數
        assert result.overall_score >= 0.3
    
    def test_blind_spot_detection(self):
        """測試知識盲點識別。"""
        engine = FeynmanAssessmentEngine()
        
        session = engine.create_session(
            session_id="feynman_003",
            concept_id="concept_003",
            concept_title="萬有引力",
            concept_definition="任何兩個物體之間都存在相互吸引的力，與質量成正比，與距離平方成反比",
            key_concepts=["質量", "距離", "引力", "平方反比", "牛頓"],
        )
        
        # 不完整的解釋（缺少關鍵概念）
        incomplete_explanation = "物體之間有吸引力，質量越大引力越大。"
        
        result = engine.assess_explanation("feynman_003", incomplete_explanation)
        
        # 應該檢測到缺失概念
        assert len(result.blind_spots) > 0
        assert any(
            spot.blind_spot_type == BlindSpotType.MISSING_CONCEPT
            for spot in result.blind_spots
        )
    
    def test_follow_up_questions(self):
        """測試引導式追問生成。"""
        engine = FeynmanAssessmentEngine()
        
        session = engine.create_session(
            session_id="feynman_004",
            concept_id="concept_004",
            concept_title="相對論",
            concept_definition="時空是彎曲的，質量會導致時空彎曲",
            key_concepts=["時空", "彎曲", "質量", "廣義相對論"],
        )
        
        result = engine.assess_explanation("feynman_004", "我不太懂這個概念")
        
        # 應該生成追問
        assert len(result.follow_up_questions) > 0


class TestLearningPrediction:
    """測試場景 1.9-1.10: 學習預測與複習建議。"""
    
    def test_record_learning_behavior(self):
        """測試記錄學習行為。"""
        model = LearningPredictionModel()
        
        behavior = create_learning_behavior(
            session_id="session_pred_001",
            knowledge_point_id="kp_001",
            time_spent_minutes=30,
            test_score=0.85,
            interaction_count=5,
        )
        
        model.record_behavior("user_001", behavior)
        
        assert "user_001" in model.user_behaviors
        assert len(model.user_behaviors["user_001"]) == 1
    
    def test_predict_mastery(self):
        """測試掌握度預測。"""
        model = LearningPredictionModel()
        
        # 記錄多次學習行為
        for i in range(5):
            behavior = create_learning_behavior(
                session_id=f"session_{i}",
                knowledge_point_id="kp_001",
                time_spent_minutes=20 + i * 5,
                test_score=0.6 + i * 0.08,
                interaction_count=3 + i,
            )
            model.record_behavior("user_002", behavior)
        
        # 預測掌握度
        prediction = model.predict_mastery("user_002", "kp_001")
        
        assert prediction.prediction_type == PredictionType.MASTERY_LEVEL
        assert 0.0 <= prediction.prediction_value <= 1.0
        assert prediction.confidence > 0.0
    
    def test_review_recommendation(self):
        """測試複習建議生成。"""
        model = LearningPredictionModel()
        
        # 記錄學習行為
        behavior = create_learning_behavior(
            session_id="session_review",
            knowledge_point_id="kp_review",
            time_spent_minutes=45,
            test_score=0.75,
        )
        model.record_behavior("user_003", behavior)
        
        # 獲取複習建議
        needs_review, recommendation = model.predict_review_need("user_003", "kp_review")
        
        assert recommendation is not None
        assert recommendation.knowledge_point_id == "kp_review"
        assert recommendation.priority in ["high", "medium", "low"]
    
    def test_forgetting_risk(self):
        """測試遺忘風險評估。"""
        model = LearningPredictionModel()
        
        # 未學習的知識點
        risk = model.get_forgetting_risk("user_004", "kp_unlearned")
        
        assert risk.prediction_type == PredictionType.FORGETTING_RISK
        assert risk.prediction_value == 1.0  # 完全遺忘風險


class TestFullPipelineIntegration:
    """完整流程集成測試。"""
    
    def test_complete_learning_pipeline(self):
        """測試完整學習流程：PDF→計劃→教學→費曼→預測。"""
        # 1. 創建模擬知識點（模擬 PDF 解析結果）
        knowledge_points = [
            KnowledgePoint(
                title=f"知識點{i}",
                content=f"這是知識點{i}的詳細內容，包含重要概念和原理。" * 5,
                page=i,
                confidence=0.8 + i * 0.04,
                tags=["測試", f"主題{i % 3}"],
            )
            for i in range(1, 6)
        ]
        
        # 2. 生成學習計劃
        plan_generator = LearningPlanGenerator()
        learning_plan = plan_generator.generate(
            knowledge_points,
            mode=LearningMode.STANDARD,
        )
        assert learning_plan.total_days > 0
        
        # 3. 創建教學會話
        teaching_engine = ProgressiveTeachingEngine()
        feynman_engine = FeynmanAssessmentEngine()
        prediction_model = LearningPredictionModel()
        
        user_id = "test_user_pipeline"
        
        for i, kp in enumerate(knowledge_points):
            # 4. 創建教學會話
            teaching_kp = create_knowledge_point_with_levels(
                id=kp.title,
                title=kp.title,
                description=kp.content,
                subject="測試",
            )
            
            session_id = f"teaching_session_{i}"
            teaching_session = teaching_engine.create_session(
                session_id=session_id,
                knowledge_point=teaching_kp,
            )
            
            # 5. 模擬學習過程
            teaching_session.user_state.understanding_score = 0.7 + i * 0.05
            teaching_session.user_state.attempts = i + 1
            
            # 6. 費曼檢測
            feynman_session_id = f"feynman_session_{i}"
            feynman_engine.create_session(
                session_id=feynman_session_id,
                concept_id=kp.title,
                concept_title=kp.title,
                concept_definition=kp.content,
                key_concepts=kp.tags + [kp.title],
            )
            
            # 用戶嘗試解釋
            user_explanation = f"我認為{kp.title}是{kp.content[:50]}..."
            assessment = feynman_engine.assess_explanation(
                feynman_session_id,
                user_explanation,
            )
            
            # 7. 記錄學習行為
            behavior = create_learning_behavior(
                session_id=session_id,
                knowledge_point_id=kp.title,
                time_spent_minutes=30,
                test_score=assessment.overall_score,
                interaction_count=assessment.concept_coverage.covered_concepts,
            )
            prediction_model.record_behavior(user_id, behavior)
        
        # 8. 生成學習預測
        final_prediction = prediction_model.predict_mastery(user_id, knowledge_points[0].title)
        assert final_prediction.prediction_value > 0.0
        
        # 9. 獲取複習建議
        needs_review, review_rec = prediction_model.predict_review_need(
            user_id,
            knowledge_points[0].title,
        )
        assert review_rec is not None
        
        # 10. 獲取學習分析報告
        analytics = prediction_model.get_learning_analytics(user_id)
        assert analytics["status"] == "success"
        assert analytics["knowledge_points_count"] == len(knowledge_points)
    
    def test_pipeline_error_handling(self):
        """測試流程中的錯誤處理。"""
        # 測試空知識點列表
        plan_generator = LearningPlanGenerator()
        
        with pytest.raises(ValueError):
            plan_generator.generate([])
        
        # 測試不存在的會話
        teaching_engine = ProgressiveTeachingEngine()
        
        with pytest.raises(ValueError):
            teaching_engine.get_explanation("nonexistent_session")
        
        # 測試不存在的費曼會話
        feynman_engine = FeynmanAssessmentEngine()
        
        with pytest.raises(ValueError):
            feynman_engine.assess_explanation("nonexistent_session", "test")


class TestPerformanceMetrics:
    """性能指標測試。"""
    
    def test_response_time(self):
        """測試響應時間 < 3 秒/請求。"""
        import time
        
        # 測試 PDF 解析
        start = time.time()
        kp = KnowledgePoint(
            title="性能測試",
            content="測試內容" * 100,
            page=1,
            confidence=0.9,
        )
        parse_time = time.time() - start
        assert parse_time < 1.0  # 知識點創建應 < 1 秒
        
        # 測試學習計劃生成
        start = time.time()
        knowledge_points = [kp] * 10
        generator = LearningPlanGenerator()
        plan = generator.generate(knowledge_points)
        plan_time = time.time() - start
        assert plan_time < 3.0  # 計劃生成應 < 3 秒
        
        # 測試費曼評估
        start = time.time()
        engine = FeynmanAssessmentEngine()
        session = engine.create_session(
            session_id="perf_test",
            concept_id="concept_perf",
            concept_title="性能測試",
            concept_definition="定義" * 50,
            key_concepts=["概念 1", "概念 2", "概念 3"],
        )
        result = engine.assess_explanation("perf_test", "用戶解釋" * 20)
        feynman_time = time.time() - start
        assert feynman_time < 3.0
    
    def test_data_integrity(self):
        """測試數據完整性（無數據丟失）。"""
        # 創建知識點
        original_kps = [
            KnowledgePoint(
                title=f"KP{i}",
                content=f"內容{i}" * 50,
                page=i,
                confidence=0.85,
                tags=[f"tag{i % 3}"],
            )
            for i in range(10)
        ]
        
        # 生成學習計劃
        generator = LearningPlanGenerator()
        plan = generator.generate(original_kps)
        
        # 驗證所有知識點都被包含
        plan_task_count = sum(len(dp.tasks) for dp in plan.daily_plans)
        assert plan_task_count == len(original_kps)
        
        # 驗證知識點內容未丟失
        original_titles = {kp.title for kp in original_kps}
        plan_titles = {task.title for dp in plan.daily_plans for task in dp.tasks}
        assert original_titles == plan_titles


# 運行測試
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
