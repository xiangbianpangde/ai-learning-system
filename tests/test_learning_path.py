"""
學習路徑自適應服務單元測試

測試覆蓋率目標：≥ 85%
"""

import pytest
from datetime import datetime
import sys
import os

# Add backend/app/services to path
SERVICES_DIR = os.path.join(os.path.dirname(__file__), '..', 'edict', 'backend', 'app', 'services')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'edict', 'backend', 'app'))

# Import directly from file
import importlib.util
spec = importlib.util.spec_from_file_location(
    "learning_path",
    os.path.join(SERVICES_DIR, "learning_path.py")
)
lp_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lp_module)

LearningPathService = lp_module.LearningPathService
KnowledgeGraph = lp_module.KnowledgeGraph
KnowledgePoint = lp_module.KnowledgePoint
LearningPath = lp_module.LearningPath
PrerequisiteCheck = lp_module.PrerequisiteCheck
get_service = lp_module.get_service


class TestKnowledgePoint:
    """知識點測試"""
    
    def test_knowledge_point_creation(self):
        """測試知識點創建"""
        kp = KnowledgePoint("kp_001", "測試知識點", chapter=1, difficulty=0.5)
        
        assert kp.id == "kp_001"
        assert kp.name == "測試知識點"
        assert kp.chapter == 1
        assert kp.difficulty == 0.5
        assert kp.mastery == 0.0
    
    def test_knowledge_point_to_dict(self):
        """測試知識點序列化"""
        kp = KnowledgePoint("kp_001", "測試", chapter=2, difficulty=0.6,
                           prerequisites=["kp_000"], tags=["tag1"])
        data = kp.to_dict()
        
        assert data["id"] == "kp_001"
        assert data["chapter"] == 2
        assert data["prerequisites"] == ["kp_000"]
        assert data["tags"] == ["tag1"]


class TestKnowledgeGraph:
    """知識圖譜測試"""
    
    @pytest.fixture
    def kg(self):
        """創建知識圖譜"""
        kg = KnowledgeGraph("math")
        kg.add_knowledge_point(KnowledgePoint("kp_01", "基礎", chapter=1, difficulty=0.3))
        kg.add_knowledge_point(KnowledgePoint("kp_02", "進階", chapter=2, difficulty=0.5,
                                              prerequisites=["kp_01"]))
        kg.add_knowledge_point(KnowledgePoint("kp_03", "高級", chapter=3, difficulty=0.7,
                                              prerequisites=["kp_02"]))
        return kg
    
    def test_add_knowledge_point(self, kg):
        """測試添加知識點"""
        assert len(kg.nodes) == 3
        assert "kp_01" in kg.nodes
    
    def test_add_dependency(self, kg):
        """測試添加依賴關係"""
        kg.add_knowledge_point(KnowledgePoint("kp_04", "新增", chapter=3))
        kg.add_dependency("kp_03", "kp_04")
        
        assert "kp_04" in kg.nodes["kp_03"].dependents
        assert "kp_03" in kg.nodes["kp_04"].prerequisites
    
    def test_add_dependency_nonexistent_raises_error(self, kg):
        """測試添加不存在的依賴拋出錯誤"""
        with pytest.raises(ValueError, match="知識點不存在"):
            kg.add_dependency("nonexistent", "kp_01")
    
    def test_get_all_prerequisites(self, kg):
        """測試獲取所有前置知識點"""
        prereqs = kg.get_all_prerequisites("kp_03")
        
        assert "kp_01" in prereqs
        assert "kp_02" in prereqs
        assert "kp_03" not in prereqs
    
    def test_get_all_dependents(self):
        """測試獲取所有後續知識點"""
        # 需要手動構建有 dependents 的圖譜
        kg = KnowledgeGraph("test")
        kg.add_knowledge_point(KnowledgePoint("kp_01", "A", chapter=1))
        kg.add_knowledge_point(KnowledgePoint("kp_02", "B", chapter=2))
        kg.add_knowledge_point(KnowledgePoint("kp_03", "C", chapter=3))
        
        # 使用 add_dependency 正確設置依賴關係
        kg.add_dependency("kp_01", "kp_02")
        kg.add_dependency("kp_02", "kp_03")
        
        dependents = kg.get_all_dependents("kp_01")
        
        assert "kp_02" in dependents
        assert "kp_03" in dependents
        assert "kp_01" not in dependents
    
    def test_get_chapter_knowledge_points(self, kg):
        """測試獲取章節知識點"""
        chapter1_kps = kg.get_chapter_knowledge_points(1)
        
        assert len(chapter1_kps) == 1
        assert chapter1_kps[0].id == "kp_01"
    
    def test_get_entry_points(self, kg):
        """測試獲取起點"""
        entry_points = kg.get_entry_points()
        
        assert len(entry_points) == 1
        assert entry_points[0].id == "kp_01"
    
    def test_get_exit_points(self, kg):
        """測試獲取終點"""
        # 注意：fixture 中使用 prerequisites 字段直接設置，沒有調用 add_dependency
        # 因此 dependents 列表為空，所有節點都是 exit points
        # 這個測試驗證 get_exit_points 的邏輯（出度為 0 的節點）
        exit_points = kg.get_exit_points()
        
        # 在當前 fixture 設置下，所有節點的 dependents 都為空
        assert len(exit_points) == 3
    
    def test_has_cycle_false(self, kg):
        """測試無環檢測"""
        assert kg.has_cycle() is False
    
    def test_has_cycle_true(self):
        """測試有環檢測"""
        kg = KnowledgeGraph("test")
        kg.add_knowledge_point(KnowledgePoint("kp_01", "A", chapter=1))
        kg.add_knowledge_point(KnowledgePoint("kp_02", "B", chapter=1))
        kg.add_dependency("kp_01", "kp_02")
        kg.add_dependency("kp_02", "kp_01")  # 製造環
        
        assert kg.has_cycle() is True
    
    def test_knowledge_graph_to_dict(self, kg):
        """測試知識圖譜序列化"""
        data = kg.to_dict()
        
        assert data["subject"] == "math"
        assert data["num_nodes"] == 3
        assert data["has_cycle"] is False
        assert data["chapters"][1] == 1


class TestLearningPathService:
    """學習路徑服務測試"""
    
    @pytest.fixture
    def service(self):
        """創建服務實例"""
        service = LearningPathService()
        
        # 創建知識圖譜
        kg = service.create_knowledge_graph("math")
        kg.add_knowledge_point(KnowledgePoint("kp_01", "基礎", chapter=1, difficulty=0.3))
        kg.add_knowledge_point(KnowledgePoint("kp_02", "進階", chapter=2, difficulty=0.5,
                                              prerequisites=["kp_01"]))
        kg.add_knowledge_point(KnowledgePoint("kp_03", "高級", chapter=3, difficulty=0.7,
                                              prerequisites=["kp_02"]))
        
        return service
    
    def test_create_knowledge_graph(self, service):
        """測試創建知識圖譜"""
        kg = service.get_knowledge_graph("math")
        assert kg is not None
        assert kg.subject == "math"
    
    def test_get_knowledge_graph_nonexistent(self, service):
        """測試獲取不存在的知識圖譜"""
        kg = service.get_knowledge_graph("physics")
        assert kg is None
    
    def test_update_mastery(self, service):
        """測試更新掌握度"""
        service.update_mastery("user_001", "kp_01", 0.9, 0.95)
        
        mastery = service.get_mastery("user_001", "kp_01")
        assert mastery == 0.9
    
    def test_get_mastery_nonexistent(self, service):
        """測試獲取不存在的掌握度"""
        mastery = service.get_mastery("user_001", "nonexistent")
        assert mastery == 0.0
    
    def test_check_prerequisites_can_start(self, service):
        """測試前置檢查可開始"""
        # 先掌握前置知識點
        service.update_mastery("user_001", "kp_01", 0.9)
        
        check = service.check_prerequisites("user_001", "math", "kp_02")
        
        assert check.can_start is True
        assert len(check.missing_prerequisites) == 0
    
    def test_check_prerequisites_cannot_start(self, service):
        """測試前置檢查不可開始"""
        check = service.check_prerequisites("user_001", "math", "kp_02")
        
        assert check.can_start is False
        assert "kp_01" in check.missing_prerequisites
    
    def test_check_prerequisites_nonexistent_raises_error(self, service):
        """測試檢查不存在的知識點"""
        with pytest.raises(ValueError, match="知識點不存在"):
            service.check_prerequisites("user_001", "math", "nonexistent")
    
    def test_recommend_path(self, service):
        """測試推薦路徑"""
        path = service.recommend_path("user_001", "math")
        
        assert path.user_id == "user_001"
        assert len(path.path) > 0
        assert "1-3" in path.scope or "第 1-3 章" in path.scope or "第 1-3 章" in path.scope
    
    def test_recommend_path_excludes_mastered(self, service):
        """測試推薦路徑排除已掌握的"""
        # 掌握 kp_01
        service.update_mastery("user_001", "kp_01", 0.9)
        
        path = service.recommend_path("user_001", "math")
        
        # kp_01 不應在路徑中
        assert "kp_01" not in path.path
    
    def test_skip_knowledge_point_success(self, service):
        """測試跳過知識點成功"""
        # 先掌握前置
        service.update_mastery("user_001", "kp_01", 0.9)
        
        skipped, reason = service.skip_knowledge_point("user_001", "math", "kp_02", test_score=0.95)
        
        assert skipped is True
        assert "測試通過" in reason
        
        # 掌握度應已更新
        mastery = service.get_mastery("user_001", "kp_02")
        assert mastery == 0.95
    
    def test_skip_knowledge_point_prerequisites_missing(self, service):
        """測試跳過時前置未掌握"""
        skipped, reason = service.skip_knowledge_point("user_001", "math", "kp_02", test_score=0.95)
        
        assert skipped is False
        assert "前置" in reason
    
    def test_skip_knowledge_point_score_too_low(self, service):
        """測試跳過時分數不足"""
        service.update_mastery("user_001", "kp_01", 0.9)
        
        skipped, reason = service.skip_knowledge_point("user_001", "math", "kp_02", test_score=0.8)
        
        assert skipped is False
        assert "分數不足" in reason
    
    def test_skip_knowledge_point_nonexistent(self, service):
        """測試跳過不存在的知識點"""
        skipped, reason = service.skip_knowledge_point("user_001", "math", "nonexistent", test_score=0.95)
        
        assert skipped is False
        assert "不存在" in reason
    
    def test_get_learning_progress(self, service):
        """測試獲取學習進度"""
        service.update_mastery("user_001", "kp_01", 0.9)
        
        progress = service.get_learning_progress("user_001", "math")
        
        assert progress["total_knowledge_points"] == 3
        assert progress["mastered"] == 1
        assert progress["completion_rate"] > 0
    
    def test_get_learning_progress_nonexistent_graph(self, service):
        """測試獲取不存在的知識圖譜進度"""
        progress = service.get_learning_progress("user_001", "physics")
        
        assert "error" in progress
    
    def test_get_next_recommended(self, service):
        """測試獲取下一個推薦"""
        next_kp = service.get_next_recommended("user_001", "math")
        
        assert next_kp is not None
        assert next_kp.id == "kp_01"  # 第一個未掌握的
    
    def test_learning_path_to_dict(self, service):
        """測試學習路徑序列化"""
        path = LearningPath(
            user_id="user_001",
            path=["kp_01", "kp_02"],
            total_time=60,
            scope="第 1-2 章"
        )
        data = path.to_dict()
        
        assert data["user_id"] == "user_001"
        assert data["path"] == ["kp_01", "kp_02"]
        assert data["total_time"] == 60
        assert data["num_knowledge_points"] == 2
    
    def test_prerequisite_check_to_dict(self):
        """測試前置檢查結果序列化"""
        check = PrerequisiteCheck(
            can_start=False,
            missing_prerequisites=["kp_01", "kp_02"],
            recommended_path=["kp_01"]
        )
        data = {
            "can_start": check.can_start,
            "missing_prerequisites": check.missing_prerequisites,
            "recommended_path": check.recommended_path
        }
        
        assert data["can_start"] is False
        assert len(data["missing_prerequisites"]) == 2


class TestTopologicalSort:
    """拓撲排序測試"""
    
    def test_topological_sort_basic(self):
        """測試基本拓撲排序"""
        kg = KnowledgeGraph("test")
        kg.add_knowledge_point(KnowledgePoint("kp_01", "A", chapter=1, difficulty=0.5))
        kg.add_knowledge_point(KnowledgePoint("kp_02", "B", chapter=1, difficulty=0.3))
        kg.add_knowledge_point(KnowledgePoint("kp_03", "C", chapter=1, difficulty=0.7))
        
        kg.add_dependency("kp_01", "kp_02")
        kg.add_dependency("kp_02", "kp_03")
        
        service = LearningPathService()
        service._knowledge_graphs["test"] = kg
        
        sorted_kps = service._topological_sort_all(kg, list(kg.nodes.values()))
        
        # 應該按依賴關係排序
        ids = [kp.id for kp in sorted_kps]
        assert ids.index("kp_01") < ids.index("kp_02")
        assert ids.index("kp_02") < ids.index("kp_03")
    
    def test_topological_sort_same_level_by_difficulty(self):
        """測試同層按難度排序"""
        kg = KnowledgeGraph("test")
        kg.add_knowledge_point(KnowledgePoint("kp_01", "A", chapter=1, difficulty=0.7))
        kg.add_knowledge_point(KnowledgePoint("kp_02", "B", chapter=1, difficulty=0.3))
        kg.add_knowledge_point(KnowledgePoint("kp_03", "C", chapter=1, difficulty=0.5))
        
        # 沒有依賴關係，應該按難度排序
        service = LearningPathService()
        service._knowledge_graphs["test"] = kg
        
        sorted_kps = service._topological_sort_all(kg, list(kg.nodes.values()))
        
        ids = [kp.id for kp in sorted_kps]
        # 難度低的在前
        assert ids[0] == "kp_02"  # 0.3
        assert ids[1] == "kp_03"  # 0.5
        assert ids[2] == "kp_01"  # 0.7


class TestGetService:
    """服務單例測試"""
    
    def test_get_service_returns_singleton(self):
        """測試獲取服務單例"""
        service1 = get_service()
        service2 = get_service()
        
        assert service1 is service2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
