"""学习计划生成服务 - 基于知识点生成个性化学习计划。

功能：
1. 根据知识点难度和依赖关系生成学习路径
2. 支持多种学习模式（快速/标准/深入）
3. 考虑用户时间约束
4. 生成每日学习任务

验收标准：
- 学习计划生成无错误
- 支持 3 种学习模式
- 输出结构化的每日任务
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any
from pathlib import Path

from .pdf_parser import KnowledgePoint

logger = logging.getLogger(__name__)


class LearningMode(Enum):
    """学习模式枚举。"""
    FAST = "fast"  # 快速模式 - 重点覆盖核心知识点
    STANDARD = "standard"  # 标准模式 - 平衡深度和广度
    DEEP = "deep"  # 深入模式 - 全面掌握所有细节


class DifficultyLevel(Enum):
    """难度级别。"""
    BEGINNER = 1
    INTERMEDIATE = 2
    ADVANCED = 3
    EXPERT = 4


@dataclass
class LearningTask:
    """学习任务数据结构。"""
    task_id: str
    title: str
    description: str
    knowledge_point: KnowledgePoint
    estimated_minutes: int
    difficulty: DifficultyLevel
    prerequisites: List[str] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)
    completed: bool = False


@dataclass
class DailyPlan:
    """每日学习计划。"""
    date: str
    tasks: List[LearningTask]
    total_minutes: int
    focus_area: str
    notes: str = ""


@dataclass
class LearningPlan:
    """完整学习计划。"""
    plan_id: str
    title: str
    mode: LearningMode
    total_days: int
    daily_plans: List[DailyPlan]
    knowledge_points_count: int
    created_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class LearningPlanGenerator:
    """学习计划生成器。"""
    
    def __init__(self):
        self.default_minutes_per_task = {
            LearningMode.FAST: 15,
            LearningMode.STANDARD: 30,
            LearningMode.DEEP: 45,
        }
        self.default_daily_minutes = {
            LearningMode.FAST: 60,
            LearningMode.STANDARD: 120,
            LearningMode.DEEP: 180,
        }
    
    def generate(
        self,
        knowledge_points: List[KnowledgePoint],
        mode: LearningMode = LearningMode.STANDARD,
        start_date: Optional[datetime] = None,
        daily_minutes: Optional[int] = None,
    ) -> LearningPlan:
        """生成学习计划。
        
        Args:
            knowledge_points: 知识点列表
            mode: 学习模式
            start_date: 开始日期，默认今天
            daily_minutes: 每日学习时长，默认根据模式设定
        
        Returns:
            LearningPlan: 生成的学习计划
        """
        if not knowledge_points:
            raise ValueError("知识点列表不能为空")
        
        start_date = start_date or datetime.now()
        daily_minutes = daily_minutes or self.default_daily_minutes[mode]
        
        # 1. 分析知识点，估算难度
        analyzed_points = self._analyze_difficulty(knowledge_points)
        
        # 2. 排序知识点（按难度和依赖关系）
        sorted_points = self._sort_by_dependency(analyzed_points)
        
        # 3. 生成学习任务
        tasks = self._create_tasks(sorted_points, mode)
        
        # 4. 分配到每日计划
        daily_plans = self._distribute_to_days(tasks, start_date, daily_minutes, mode)
        
        # 5. 创建学习计划
        plan = LearningPlan(
            plan_id=self._generate_plan_id(),
            title=f"{mode.value.capitalize()} Learning Plan",
            mode=mode,
            total_days=len(daily_plans),
            daily_plans=daily_plans,
            knowledge_points_count=len(knowledge_points),
            created_at=datetime.now().isoformat(),
            metadata={
                "total_tasks": len(tasks),
                "estimated_hours": sum(dp.total_minutes for dp in daily_plans) / 60,
            }
        )
        
        logger.info(f"生成学习计划：{plan.plan_id}, {plan.total_days}天，{len(tasks)}个任务")
        return plan
    
    def _analyze_difficulty(
        self,
        knowledge_points: List[KnowledgePoint]
    ) -> List[Dict[str, Any]]:
        """分析知识点难度。"""
        analyzed = []
        
        for kp in knowledge_points:
            # 基于内容长度和置信度估算难度
            content_length = len(kp.content)
            confidence = kp.confidence
            
            # 简单规则：内容越长、置信度越低，难度越高
            if content_length < 200 and confidence > 0.8:
                difficulty = DifficultyLevel.BEGINNER
            elif content_length < 500 and confidence > 0.6:
                difficulty = DifficultyLevel.INTERMEDIATE
            elif content_length < 1000:
                difficulty = DifficultyLevel.ADVANCED
            else:
                difficulty = DifficultyLevel.EXPERT
            
            analyzed.append({
                "knowledge_point": kp,
                "difficulty": difficulty,
                "estimated_minutes": self._estimate_time(kp, difficulty),
                "dependencies": self._extract_dependencies(kp),
            })
        
        return analyzed
    
    def _estimate_time(
        self,
        kp: KnowledgePoint,
        difficulty: DifficultyLevel
    ) -> int:
        """估算学习时长（分钟）。"""
        base_time = len(kp.content) / 100  # 每 100 字约 1 分钟
        
        # 根据难度调整
        multipliers = {
            DifficultyLevel.BEGINNER: 1.0,
            DifficultyLevel.INTERMEDIATE: 1.5,
            DifficultyLevel.ADVANCED: 2.0,
            DifficultyLevel.EXPERT: 3.0,
        }
        
        return int(base_time * multipliers[difficulty])
    
    def _extract_dependencies(self, kp: KnowledgePoint) -> List[str]:
        """提取知识点依赖关系。"""
        # 简单实现：从标签中提取
        deps = []
        for tag in kp.tags:
            if "基础" in tag or "前提" in tag:
                deps.append(tag)
        return deps
    
    def _sort_by_dependency(
        self,
        analyzed_points: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """按依赖关系排序知识点。"""
        # 简单拓扑排序：先学简单的、依赖少的
        return sorted(
            analyzed_points,
            key=lambda x: (x["difficulty"].value, len(x["dependencies"]))
        )
    
    def _create_tasks(
        self,
        sorted_points: List[Dict[str, Any]],
        mode: LearningMode
    ) -> List[LearningTask]:
        """创建学习任务。"""
        tasks = []
        
        for i, point in enumerate(sorted_points):
            kp = point["knowledge_point"]
            task = LearningTask(
                task_id=f"task_{i+1:03d}",
                title=kp.title[:50],
                description=kp.content[:200] + "..." if len(kp.content) > 200 else kp.content,
                knowledge_point=kp,
                estimated_minutes=point["estimated_minutes"],
                difficulty=point["difficulty"],
                prerequisites=point["dependencies"],
            )
            tasks.append(task)
        
        return tasks
    
    def _distribute_to_days(
        self,
        tasks: List[LearningTask],
        start_date: datetime,
        daily_minutes: int,
        mode: LearningMode
    ) -> List[DailyPlan]:
        """将任务分配到每日计划。"""
        daily_plans = []
        current_date = start_date
        task_index = 0
        
        while task_index < len(tasks):
            day_tasks = []
            day_minutes = 0
            focus_areas = set()
            
            # 填充当天的任务
            while task_index < len(tasks) and day_minutes < daily_minutes:
                task = tasks[task_index]
                
                # 检查是否超出每日时长（允许最后一个任务超出）
                if day_minutes > 0 and day_minutes + task.estimated_minutes > daily_minutes * 1.2:
                    break
                
                day_tasks.append(task)
                day_minutes += task.estimated_minutes
                focus_areas.add(task.knowledge_point.tags[0] if task.knowledge_point.tags else "通用")
                task_index += 1
            
            if day_tasks:
                daily_plans.append(DailyPlan(
                    date=current_date.strftime("%Y-%m-%d"),
                    tasks=day_tasks,
                    total_minutes=day_minutes,
                    focus_area=", ".join(focus_areas),
                    notes=self._generate_day_notes(day_tasks, mode)
                ))
            
            current_date += timedelta(days=1)
        
        return daily_plans
    
    def _generate_day_notes(
        self,
        tasks: List[LearningTask],
        mode: LearningMode
    ) -> str:
        """生成每日学习备注。"""
        if mode == LearningMode.FAST:
            return "快速学习模式：重点关注核心概念，跳过细节"
        elif mode == LearningMode.DEEP:
            return "深入学习模式：建议做笔记、完成练习题、复习总结"
        else:
            return "标准学习模式：平衡理解深度和学习进度"
    
    def _generate_plan_id(self) -> str:
        """生成计划 ID。"""
        import uuid
        return f"LP-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    
    def generate_from_pdf(
        self,
        pdf_path: Path,
        mode: LearningMode = LearningMode.STANDARD,
    ) -> LearningPlan:
        """从 PDF 文件生成学习计划。"""
        from .pdf_parser import PDFParserService
        
        parser = PDFParserService()
        result = parser.parse(pdf_path)
        
        if not result.success:
            raise ValueError(f"PDF 解析失败：{result.error}")
        
        return self.generate(result.knowledge_points, mode)


# 便捷函数
def generate_learning_plan(
    knowledge_points: List[KnowledgePoint],
    mode: str = "standard",
    days: int = 7,
) -> LearningPlan:
    """便捷函数：生成学习计划。"""
    mode_map = {
        "fast": LearningMode.FAST,
        "standard": LearningMode.STANDARD,
        "deep": LearningMode.DEEP,
    }
    
    generator = LearningPlanGenerator()
    return generator.generate(
        knowledge_points,
        mode=mode_map.get(mode, LearningMode.STANDARD),
    )


def generate_plan_from_pdf(
    pdf_path: str | Path,
    mode: str = "standard",
) -> LearningPlan:
    """便捷函数：从 PDF 生成学习计划。"""
    generator = LearningPlanGenerator()
    return generator.generate_from_pdf(Path(pdf_path), LearningMode.STANDARD)
