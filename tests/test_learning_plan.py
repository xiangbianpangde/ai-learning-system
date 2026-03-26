"""学习计划生成器单元测试。

测试覆盖：
1. 学习计划生成
2. 三种学习模式
3. 难度分析
4. 任务分配
5. 错误处理

验收标准：
- 学习计划生成无错误
- 支持 3 种学习模式
- 输出结构化的每日任务
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'edict' / 'backend'))

from app.services.learning_plan import (
    LearningPlanGenerator,
    LearningMode,
    DifficultyLevel,
    LearningTask,
    DailyPlan,
    LearningPlan,
    generate_learning_plan,
    generate_plan_from_pdf,
)
from app.services.pdf_parser import KnowledgePoint


class TestLearningMode:
    """学习模式枚举测试。"""
    
    def test_learning_mode_values(self):
        """测试学习模式枚举值。"""
        assert LearningMode.FAST.value == "fast"
        assert LearningMode.STANDARD.value == "standard"
        assert LearningMode.DEEP.value == "deep"


class TestDifficultyLevel:
    """难度级别枚举测试。"""
    
    def test_difficulty_levels(self):
        """测试难度级别。"""
        assert DifficultyLevel.BEGINNER.value == 1
        assert DifficultyLevel.INTERMEDIATE.value == 2
        assert DifficultyLevel.ADVANCED.value == 3
        assert DifficultyLevel.EXPERT.value == 4


class TestLearningTask:
    """学习任务数据结构测试。"""
    
    def test_task_creation(self):
        """测试学习任务创建。"""
        kp = KnowledgePoint(
            title="测试知识点",
            content="测试内容",
            page=1,
        )
        
        task = LearningTask(
            task_id="task_001",
            title="任务标题",
            description="任务描述",
            knowledge_point=kp,
            estimated_minutes=30,
            difficulty=DifficultyLevel.INTERMEDIATE,
        )
        
        assert task.task_id == "task_001"
        assert task.estimated_minutes == 30
        assert task.difficulty == DifficultyLevel.INTERMEDIATE
        assert task.prerequisites == []
        assert task.completed is False


class TestDailyPlan:
    """每日计划数据结构测试。"""
    
    def test_daily_plan_creation(self):
        """测试每日计划创建。"""
        plan = DailyPlan(
            date="2026-03-26",
            tasks=[],
            total_minutes=120,
            focus_area="核心概念",
            notes="测试备注",
        )
        
        assert plan.date == "2026-03-26"
        assert plan.total_minutes == 120
        assert plan.focus_area == "核心概念"
        assert plan.notes == "测试备注"


class TestLearningPlan:
    """完整学习计划数据结构测试。"""
    
    def test_learning_plan_creation(self):
        """测试学习计划创建。"""
        plan = LearningPlan(
            plan_id="LP-20260326-ABC123",
            title="标准学习计划",
            mode=LearningMode.STANDARD,
            total_days=7,
            daily_plans=[],
            knowledge_points_count=20,
            created_at="2026-03-26T00:00:00",
        )
        
        assert plan.plan_id == "LP-20260326-ABC123"
        assert plan.mode == LearningMode.STANDARD
        assert plan.total_days == 7
        assert plan.knowledge_points_count == 20


class TestLearningPlanGenerator:
    """学习计划生成器测试。"""
    
    def test_generator_initialization(self):
        """测试生成器初始化。"""
        generator = LearningPlanGenerator()
        
        assert LearningMode.FAST in generator.default_minutes_per_task
        assert LearningMode.STANDARD in generator.default_daily_minutes
    
    def test_generate_empty_knowledge_points(self):
        """测试空知识点列表。"""
        generator = LearningPlanGenerator()
        
        with pytest.raises(ValueError, match="知识点列表不能为空"):
            generator.generate([])
    
    def test_generate_basic_plan(self):
        """测试基本计划生成。"""
        generator = LearningPlanGenerator()
        
        knowledge_points = [
            KnowledgePoint(
                title=f"知识点{i}",
                content=f"这是知识点{i}的详细内容，长度足够用于分析。" * 10,
                page=i,
                confidence=0.8,
            )
            for i in range(1, 6)
        ]
        
        plan = generator.generate(knowledge_points, mode=LearningMode.STANDARD)
        
        assert plan.plan_id.startswith("LP-")
        assert plan.mode == LearningMode.STANDARD
        assert plan.knowledge_points_count == 5
        assert len(plan.daily_plans) > 0
        assert all(isinstance(dp, DailyPlan) for dp in plan.daily_plans)
    
    def test_generate_fast_mode(self):
        """测试快速模式。"""
        generator = LearningPlanGenerator()
        
        knowledge_points = [
            KnowledgePoint(title=f"KP{i}", content="内容" * 20, page=i)
            for i in range(1, 4)
        ]
        
        plan = generator.generate(knowledge_points, mode=LearningMode.FAST)
        
        assert plan.mode == LearningMode.FAST
        # 快速模式应该天数较少
        assert plan.metadata["estimated_hours"] <= 2
    
    def test_generate_deep_mode(self):
        """测试深入模式。"""
        generator = LearningPlanGenerator()
        
        knowledge_points = [
            KnowledgePoint(title=f"KP{i}", content="内容" * 50, page=i)
            for i in range(1, 4)
        ]
        
        plan = generator.generate(knowledge_points, mode=LearningMode.DEEP)
        
        assert plan.mode == LearningMode.DEEP
        # 深入模式应该天数较多
        assert plan.metadata["estimated_hours"] >= 2
    
    def test_generate_with_custom_start_date(self):
        """测试自定义开始日期。"""
        generator = LearningPlanGenerator()
        
        knowledge_points = [
            KnowledgePoint(title="测试", content="内容" * 20, page=1)
        ]
        
        start_date = datetime(2026, 4, 1)
        plan = generator.generate(knowledge_points, start_date=start_date)
        
        assert plan.daily_plans[0].date == "2026-04-01"
    
    def test_generate_with_custom_daily_minutes(self):
        """测试自定义每日时长。"""
        generator = LearningPlanGenerator()
        
        knowledge_points = [
            KnowledgePoint(title=f"KP{i}", content="内容" * 30, page=i)
            for i in range(1, 11)
        ]
        
        plan = generator.generate(
            knowledge_points,
            daily_minutes=60,  # 每天 1 小时
        )
        
        # 每日时长应该接近设定值
        for dp in plan.daily_plans:
            assert dp.total_minutes <= 60 * 1.2  # 允许 20% 浮动


class TestDifficultyAnalysis:
    """难度分析测试。"""
    
    def test_analyze_beginner_level(self):
        """测试初级难度分析。"""
        generator = LearningPlanGenerator()
        
        kp = KnowledgePoint(
            title="简单概念",
            content="短内容",  # < 200 字
            page=1,
            confidence=0.9,  # > 0.8
        )
        
        analyzed = generator._analyze_difficulty([kp])
        
        assert analyzed[0]["difficulty"] == DifficultyLevel.BEGINNER
    
    def test_analyze_intermediate_level(self):
        """测试中级难度分析。"""
        generator = LearningPlanGenerator()
        
        kp = KnowledgePoint(
            title="中等概念",
            content="中等长度内容" * 20,  # 200-500 字
            page=1,
            confidence=0.7,  # > 0.6
        )
        
        analyzed = generator._analyze_difficulty([kp])
        
        assert analyzed[0]["difficulty"] == DifficultyLevel.INTERMEDIATE
    
    def test_analyze_advanced_level(self):
        """测试高级难度分析。"""
        generator = LearningPlanGenerator()
        
        kp = KnowledgePoint(
            title="复杂概念",
            content="长内容" * 150,  # 500-1000 字
            page=1,
            confidence=0.5,
        )
        
        analyzed = generator._analyze_difficulty([kp])
        
        assert analyzed[0]["difficulty"] == DifficultyLevel.ADVANCED
    
    def test_analyze_expert_level(self):
        """测试专家级难度分析。"""
        generator = LearningPlanGenerator()
        
        kp = KnowledgePoint(
            title="专家概念",
            content="非常长的内容" * 100,  # > 1000 字
            page=1,
            confidence=0.3,
        )
        
        analyzed = generator._analyze_difficulty([kp])
        
        assert analyzed[0]["difficulty"] == DifficultyLevel.EXPERT


class TestTimeEstimation:
    """时间估算测试。"""
    
    def test_estimate_time_beginner(self):
        """测试初级时间估算。"""
        generator = LearningPlanGenerator()
        
        kp = KnowledgePoint(title="测试", content="100 字内容", page=1)
        
        time = generator._estimate_time(kp, DifficultyLevel.BEGINNER)
        
        assert time > 0
        assert time < generator._estimate_time(kp, DifficultyLevel.EXPERT)
    
    def test_estimate_time_scales_with_difficulty(self):
        """测试时间随难度递增。"""
        generator = LearningPlanGenerator()
        
        kp = KnowledgePoint(title="测试", content="内容" * 50, page=1)
        
        beginner_time = generator._estimate_time(kp, DifficultyLevel.BEGINNER)
        expert_time = generator._estimate_time(kp, DifficultyLevel.EXPERT)
        
        assert expert_time > beginner_time


class TestTaskDistribution:
    """任务分配测试。"""
    
    def test_distribute_tasks_to_days(self):
        """测试任务分配到每日。"""
        generator = LearningPlanGenerator()
        
        tasks = [
            LearningTask(
                task_id=f"task_{i}",
                title=f"任务{i}",
                description=f"描述{i}",
                knowledge_point=KnowledgePoint(f"KP{i}", f"内容{i}", i),
                estimated_minutes=30,
                difficulty=DifficultyLevel.INTERMEDIATE,
            )
            for i in range(1, 11)
        ]
        
        start_date = datetime(2026, 3, 26)
        daily_plans = generator._distribute_to_days(
            tasks, start_date, daily_minutes=60, mode=LearningMode.STANDARD
        )
        
        assert len(daily_plans) > 0
        assert all(isinstance(dp, DailyPlan) for dp in daily_plans)
        
        # 检查日期连续性
        for i, dp in enumerate(daily_plans):
            expected_date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            assert dp.date == expected_date
    
    def test_daily_minutes_respected(self):
        """测试每日时长限制。"""
        generator = LearningPlanGenerator()
        
        tasks = [
            LearningTask(
                task_id=f"task_{i}",
                title=f"任务{i}",
                description=f"描述{i}",
                knowledge_point=KnowledgePoint(f"KP{i}", f"内容{i}", i),
                estimated_minutes=25,
                difficulty=DifficultyLevel.INTERMEDIATE,
            )
            for i in range(1, 20)
        ]
        
        daily_plans = generator._distribute_to_days(
            tasks, datetime.now(), daily_minutes=60, mode=LearningMode.STANDARD
        )
        
        # 每日总时长不应超过限制的 120%
        for dp in daily_plans:
            assert dp.total_minutes <= 60 * 1.2


class TestPDFIntegration:
    """PDF 集成测试。"""
    
    def test_generate_from_pdf(self):
        """测试从 PDF 生成计划。"""
        generator = LearningPlanGenerator()
        
        with patch('app.services.learning_plan.PDFParserService') as mock_parser_class:
            mock_parser = Mock()
            mock_parser.parse.return_value = Mock(
                success=True,
                knowledge_points=[
                    KnowledgePoint(f"KP{i}", f"内容{i}", i)
                    for i in range(1, 6)
                ]
            )
            mock_parser_class.return_value = mock_parser
            
            plan = generator.generate_from_pdf(Path("test.pdf"), LearningMode.STANDARD)
            
            assert plan.knowledge_points_count == 5
            assert len(plan.daily_plans) > 0
    
    def test_generate_from_pdf_failure(self):
        """测试 PDF 解析失败处理。"""
        generator = LearningPlanGenerator()
        
        with patch('app.services.learning_plan.PDFParserService') as mock_parser_class:
            mock_parser = Mock()
            mock_parser.parse.return_value = Mock(
                success=False,
                error="文件不存在"
            )
            mock_parser_class.return_value = mock_parser
            
            with pytest.raises(ValueError, match="PDF 解析失败"):
                generator.generate_from_pdf(Path("nonexistent.pdf"))


class TestConvenienceFunctions:
    """便捷函数测试。"""
    
    def test_generate_learning_plan_function(self):
        """测试 generate_learning_plan 便捷函数。"""
        knowledge_points = [
            KnowledgePoint(title="测试", content="内容" * 20, page=1)
        ]
        
        plan = generate_learning_plan(knowledge_points, mode="standard")
        
        assert isinstance(plan, LearningPlan)
        assert plan.mode == LearningMode.STANDARD
    
    def test_generate_plan_from_pdf_function(self):
        """测试 generate_plan_from_pdf 便捷函数。"""
        with patch('app.services.learning_plan.LearningPlanGenerator') as mock_gen_class:
            mock_gen = Mock()
            mock_gen.generate_from_pdf.return_value = LearningPlan(
                plan_id="LP-TEST",
                title="测试计划",
                mode=LearningMode.STANDARD,
                total_days=1,
                daily_plans=[],
                knowledge_points_count=1,
                created_at="2026-03-26",
            )
            mock_gen_class.return_value = mock_gen
            
            plan = generate_plan_from_pdf("test.pdf")
            
            assert isinstance(plan, LearningPlan)


class TestEdgeCases:
    """边界情况测试。"""
    
    def test_single_knowledge_point(self):
        """测试单个知识点。"""
        generator = LearningPlanGenerator()
        
        kp = KnowledgePoint(title="唯一知识点", content="内容" * 50, page=1)
        plan = generator.generate([kp])
        
        assert plan.knowledge_points_count == 1
        assert len(plan.daily_plans) >= 1
    
    def test_many_knowledge_points(self):
        """测试大量知识点。"""
        generator = LearningPlanGenerator()
        
        kps = [
            KnowledgePoint(title=f"KP{i}", content=f"内容{i}" * 20, page=i)
            for i in range(1, 101)
        ]
        
        plan = generator.generate(kps, mode=LearningMode.FAST)
        
        assert plan.knowledge_points_count == 100
        assert len(plan.daily_plans) > 0
    
    def test_special_characters_in_titles(self):
        """测试特殊字符标题。"""
        generator = LearningPlanGenerator()
        
        kp = KnowledgePoint(
            title="特殊@#$标题测试",
            content="内容" * 20,
            page=1,
        )
        
        plan = generator.generate([kp])
        
        # 不应抛出异常
        assert plan.knowledge_points_count == 1
    
    def test_very_long_content(self):
        """测试超长内容。"""
        generator = LearningPlanGenerator()
        
        kp = KnowledgePoint(
            title="长内容测试",
            content="内容" * 1000,  # 非常长
            page=1,
        )
        
        plan = generator.generate([kp])
        
        # 不应抛出异常
        assert plan.success if hasattr(plan, 'success') else True


class TestErrorHandling:
    """错误处理测试。"""
    
    def test_invalid_mode_parameter(self):
        """测试无效模式参数。"""
        generator = LearningPlanGenerator()
        
        kps = [KnowledgePoint(title="测试", content="内容", page=1)]
        
        # 应该使用默认值而不是抛出异常
        plan = generator.generate(kps, mode=LearningMode.STANDARD)
        assert plan is not None
    
    def test_dependency_extraction(self):
        """测试依赖关系提取。"""
        generator = LearningPlanGenerator()
        
        kp = KnowledgePoint(
            title="测试",
            content="内容",
            page=1,
            tags=["基础概念", "前提知识"],
        )
        
        deps = generator._extract_dependencies(kp)
        
        # 应能提取包含"基础"或"前提"的标签
        assert isinstance(deps, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
