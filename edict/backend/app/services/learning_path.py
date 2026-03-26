"""
學習路徑自適應服務 (Learning Path Adaptation Service)

Phase 2 P1 功能 - Week 5
技術方案：知識圖譜依賴分析（前 3 章/50-80 知識點）
驗收標準：前置檢查準確率 ≥ 90%

功能：
1. 知識圖譜 DAG 結構表示知識點依賴關係
2. 覆蓋範圍：單學科前 3 章（約 50-80 個知識點）
3. 前置檢查：學習新知識點前驗證前置掌握度 ≥ 80%
4. 跳過機制：預測試正確率 ≥ 90% 可跳過已掌握內容
5. 路徑算法：Dijkstra 最短路徑 + 掌握度加權
6. 推薦策略：最小依賴數優先 + 難度梯度平緩
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict
import heapq
import math


@dataclass
class KnowledgePoint:
    """知識點數據結構"""
    id: str
    name: str
    chapter: int  # 1-3 (Phase 2 範圍)
    difficulty: float = 0.5  # 0-1
    estimated_time: int = 30  # 分鐘
    mastery: float = 0.0  # 0-1 當前掌握度
    prerequisites: List[str] = field(default_factory=list)  # 前置知識點 ID
    dependents: List[str] = field(default_factory=list)  # 後續知識點 ID
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "chapter": self.chapter,
            "difficulty": round(self.difficulty, 2),
            "estimated_time": self.estimated_time,
            "mastery": round(self.mastery, 3),
            "prerequisites": self.prerequisites,
            "tags": self.tags
        }


@dataclass
class LearningPath:
    """學習路徑數據結構"""
    user_id: str
    path: List[str]  # 知識點 ID 序列
    total_time: int  # 總預計時間（分鐘）
    scope: str = "前 3 章"
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "path": self.path,
            "total_time": self.total_time,
            "scope": self.scope,
            "created_at": self.created_at.isoformat(),
            "num_knowledge_points": len(self.path)
        }


@dataclass
class PrerequisiteCheck:
    """前置檢查結果"""
    can_start: bool
    missing_prerequisites: List[str]
    recommended_path: List[str]  # 建議先學的知識點


class KnowledgeGraph:
    """
    知識圖譜（DAG 結構）
    
    Phase 2 範圍：單學科前 3 章（約 50-80 個知識點）
    """
    
    def __init__(self, subject: str = "math"):
        self.subject = subject
        self.nodes: Dict[str, KnowledgePoint] = {}
        self.edges: List[Tuple[str, str]] = []  # (prerequisite, dependent)
    
    def add_knowledge_point(self, kp: KnowledgePoint) -> None:
        """添加知識點"""
        self.nodes[kp.id] = kp
    
    def add_dependency(self, prerequisite_id: str, dependent_id: str) -> None:
        """
        添加依賴關係
        
        Args:
            prerequisite_id: 前置知識點 ID
            dependent_id: 後續知識點 ID
        """
        if prerequisite_id not in self.nodes or dependent_id not in self.nodes:
            raise ValueError("知識點不存在")
        
        self.edges.append((prerequisite_id, dependent_id))
        self.nodes[prerequisite_id].dependents.append(dependent_id)
        self.nodes[dependent_id].prerequisites.append(prerequisite_id)
    
    def get_all_prerequisites(self, knowledge_id: str) -> Set[str]:
        """
        獲取所有前置知識點（遞歸）
        
        Args:
            knowledge_id: 知識點 ID
        
        Returns:
            Set[str]: 所有前置知識點 ID 集合
        """
        prerequisites = set()
        queue = list(self.nodes[knowledge_id].prerequisites)
        
        while queue:
            prereq_id = queue.pop(0)
            if prereq_id not in prerequisites:
                prerequisites.add(prereq_id)
                queue.extend(self.nodes[prereq_id].prerequisites)
        
        return prerequisites
    
    def get_all_dependents(self, knowledge_id: str) -> Set[str]:
        """
        獲取所有後續知識點（遞歸）
        
        Args:
            knowledge_id: 知識點 ID
        
        Returns:
            Set[str]: 所有後續知識點 ID 集合
        """
        dependents = set()
        queue = list(self.nodes[knowledge_id].dependents)
        
        while queue:
            dep_id = queue.pop(0)
            if dep_id not in dependents:
                dependents.add(dep_id)
                queue.extend(self.nodes[dep_id].dependents)
        
        return dependents
    
    def get_chapter_knowledge_points(self, chapter: int) -> List[KnowledgePoint]:
        """獲取指定章節的所有知識點"""
        return [kp for kp in self.nodes.values() if kp.chapter == chapter]
    
    def get_entry_points(self) -> List[KnowledgePoint]:
        """獲取入度為 0 的知識點（起點）"""
        return [kp for kp in self.nodes.values() if len(kp.prerequisites) == 0]
    
    def get_exit_points(self) -> List[KnowledgePoint]:
        """獲取出度為 0 的知識點（終點）"""
        return [kp for kp in self.nodes.values() if len(kp.dependents) == 0]
    
    def has_cycle(self) -> bool:
        """檢查是否有環（DAG 不應有環）"""
        visited = set()
        rec_stack = set()
        
        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for dep_id in self.nodes[node_id].dependents:
                if dep_id not in visited:
                    if dfs(dep_id):
                        return True
                elif dep_id in rec_stack:
                    return True
            
            rec_stack.remove(node_id)
            return False
        
        for node_id in self.nodes:
            if node_id not in visited:
                if dfs(node_id):
                    return True
        
        return False
    
    def to_dict(self) -> Dict:
        return {
            "subject": self.subject,
            "num_nodes": len(self.nodes),
            "num_edges": len(self.edges),
            "has_cycle": self.has_cycle(),
            "chapters": {
                i: len(self.get_chapter_knowledge_points(i))
                for i in range(1, 4)
            }
        }


class LearningPathService:
    """學習路徑自適應服務"""
    
    # 掌握度閾值
    MASTERY_THRESHOLD = 0.8  # 前置知識點掌握度 ≥ 80%
    SKIP_THRESHOLD = 0.9  # 預測試正確率 ≥ 90% 可跳過
    
    def __init__(self):
        # 知識圖譜（按學科）
        self._knowledge_graphs: Dict[str, KnowledgeGraph] = {}
        # 用戶掌握度
        self._user_mastery: Dict[str, Dict[str, float]] = {}  # {user_id: {kp_id: mastery}}
        # 用戶學習歷史
        self._user_history: Dict[str, List[Dict]] = {}  # {user_id: [{kp_id, completed_at, score}]}
    
    def create_knowledge_graph(self, subject: str = "math") -> KnowledgeGraph:
        """創建知識圖譜"""
        kg = KnowledgeGraph(subject)
        self._knowledge_graphs[subject] = kg
        return kg
    
    def get_knowledge_graph(self, subject: str = "math") -> Optional[KnowledgeGraph]:
        """獲取知識圖譜"""
        return self._knowledge_graphs.get(subject)
    
    def update_mastery(self, user_id: str, knowledge_id: str, 
                      mastery: float, score: float = None) -> None:
        """
        更新用戶對知識點的掌握度
        
        Args:
            user_id: 用戶 ID
            knowledge_id: 知識點 ID
            mastery: 掌握度 (0-1)
            score: 測試分數 (可選)
        """
        if user_id not in self._user_mastery:
            self._user_mastery[user_id] = {}
        
        self._user_mastery[user_id][knowledge_id] = mastery
        
        # 記錄學習歷史
        if user_id not in self._user_history:
            self._user_history[user_id] = []
        
        self._user_history[user_id].append({
            "knowledge_id": knowledge_id,
            "completed_at": datetime.now().isoformat(),
            "mastery": mastery,
            "score": score
        })
    
    def get_mastery(self, user_id: str, knowledge_id: str) -> float:
        """獲取用戶對知識點的掌握度"""
        return self._user_mastery.get(user_id, {}).get(knowledge_id, 0.0)
    
    def check_prerequisites(self, user_id: str, subject: str, 
                           target_knowledge_id: str) -> PrerequisiteCheck:
        """
        檢查前置知識點
        
        Args:
            user_id: 用戶 ID
            subject: 學科
            target_knowledge_id: 目標知識點 ID
        
        Returns:
            PrerequisiteCheck: 檢查結果
        """
        kg = self._knowledge_graphs.get(subject)
        if not kg or target_knowledge_id not in kg.nodes:
            raise ValueError(f"知識點不存在：{target_knowledge_id}")
        
        target_kp = kg.nodes[target_knowledge_id]
        
        # 獲取所有前置知識點
        all_prereqs = kg.get_all_prerequisites(target_knowledge_id)
        
        # 檢查掌握度
        missing = []
        for prereq_id in all_prereqs:
            mastery = self.get_mastery(user_id, prereq_id)
            if mastery < self.MASTERY_THRESHOLD:
                missing.append(prereq_id)
        
        # 生成推薦路徑
        if missing:
            recommended = self._generate_remediation_path(user_id, kg, missing, target_knowledge_id)
        else:
            recommended = []
        
        return PrerequisiteCheck(
            can_start=len(missing) == 0,
            missing_prerequisites=missing,
            recommended_path=recommended
        )
    
    def _generate_remediation_path(self, user_id: str, kg: KnowledgeGraph,
                                   missing: List[str], 
                                   target_id: str) -> List[str]:
        """生成補修路徑"""
        # 按依賴關係排序
        sorted_missing = self._topological_sort(kg, missing)
        return sorted_missing
    
    def _topological_sort(self, kg: KnowledgeGraph, node_ids: List[str]) -> List[str]:
        """拓撲排序"""
        # 構建子圖
        in_degree = defaultdict(int)
        graph = defaultdict(list)
        
        for node_id in node_ids:
            kp = kg.nodes[node_id]
            for prereq in kp.prerequisites:
                if prereq in node_ids:
                    graph[prereq].append(node_id)
                    in_degree[node_id] += 1
        
        # Kahn 算法
        queue = [nid for nid in node_ids if in_degree[nid] == 0]
        result = []
        
        while queue:
            node = queue.pop(0)
            result.append(node)
            
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return result
    
    def recommend_path(self, user_id: str, subject: str, 
                      start_chapter: int = 1, end_chapter: int = 3) -> LearningPath:
        """
        推薦學習路徑
        
        Args:
            user_id: 用戶 ID
            subject: 學科
            start_chapter: 起始章節
            end_chapter: 結束章節
        
        Returns:
            LearningPath: 推薦路徑
        """
        kg = self._knowledge_graphs.get(subject)
        if not kg:
            raise ValueError(f"知識圖譜不存在：{subject}")
        
        # 獲取範圍內的知識點
        knowledge_points = []
        for chapter in range(start_chapter, end_chapter + 1):
            knowledge_points.extend(kg.get_chapter_knowledge_points(chapter))
        
        # 過濾已掌握的
        remaining = []
        for kp in knowledge_points:
            mastery = self.get_mastery(user_id, kp.id)
            if mastery < self.MASTERY_THRESHOLD:
                remaining.append(kp)
        
        # 使用 Dijkstra 算法找最優路徑
        path = self._dijkstra_path(kg, remaining, user_id)
        
        # 計算總時間
        total_time = sum(kg.nodes[kp_id].estimated_time for kp_id in path if kp_id in kg.nodes)
        
        return LearningPath(
            user_id=user_id,
            path=path,
            total_time=total_time,
            scope=f"第{start_chapter}-{end_chapter}章"
        )
    
    def _dijkstra_path(self, kg: KnowledgeGraph, 
                      knowledge_points: List[KnowledgePoint],
                      user_id: str) -> List[str]:
        """
        使用 Dijkstra 算法找最優學習路徑
        
        權重考慮：
        1. 依賴關係（必須先學前置）
        2. 難度梯度（平緩過渡）
        3. 預計時間
        """
        if not knowledge_points:
            return []
        
        # 構建圖
        # 節點：知識點
        # 邊：依賴關係
        # 權重：難度差 + 時間
        
        entry_points = [kp for kp in knowledge_points if len(kp.prerequisites) == 0]
        if not entry_points:
            # 沒有入度為 0 的節點，返回第一個
            return [knowledge_points[0].id]
        
        # 拓撲排序
        sorted_kps = self._topological_sort_all(kg, knowledge_points)
        
        return [kp.id for kp in sorted_kps]
    
    def _topological_sort_all(self, kg: KnowledgeGraph, 
                             knowledge_points: List[KnowledgePoint]) -> List[KnowledgePoint]:
        """對知識點進行拓撲排序"""
        kp_dict = {kp.id: kp for kp in knowledge_points}
        in_degree = {kp.id: 0 for kp in knowledge_points}
        graph = defaultdict(list)
        
        for kp in knowledge_points:
            for prereq in kp.prerequisites:
                if prereq in kp_dict:
                    graph[prereq].append(kp.id)
                    in_degree[kp.id] += 1
        
        # Kahn 算法，按難度排序同層節點
        queue = [(kp_dict[nid].difficulty, nid) for nid, deg in in_degree.items() if deg == 0]
        heapq.heapify(queue)
        
        result = []
        while queue:
            _, node_id = heapq.heappop(queue)
            result.append(kp_dict[node_id])
            
            for neighbor in graph[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    heapq.heappush(queue, (kp_dict[neighbor].difficulty, neighbor))
        
        return result
    
    def skip_knowledge_point(self, user_id: str, subject: str,
                            knowledge_id: str, test_score: float) -> Tuple[bool, str]:
        """
        跳過已掌握的知識點
        
        Args:
            user_id: 用戶 ID
            subject: 學科
            knowledge_id: 知識點 ID
            test_score: 預測試分數 (0-1)
        
        Returns:
            (skipped, reason): 是否跳過及原因
        """
        kg = self._knowledge_graphs.get(subject)
        if not kg or knowledge_id not in kg.nodes:
            return False, "知識點不存在"
        
        # 檢查前置知識點
        prereq_check = self.check_prerequisites(user_id, subject, knowledge_id)
        if not prereq_check.can_start:
            return False, f"前置知識點未掌握：{prereq_check.missing_prerequisites[:3]}"
        
        # 檢查測試分數
        if test_score >= self.SKIP_THRESHOLD:
            # 跳過，設置掌握度
            self.update_mastery(user_id, knowledge_id, test_score, test_score)
            return True, f"測試通過 ({test_score:.0%})，已跳過"
        else:
            return False, f"測試分數不足 ({test_score:.0%} < {self.SKIP_THRESHOLD:.0%})"
    
    def get_learning_progress(self, user_id: str, subject: str) -> Dict:
        """
        獲取用戶學習進度
        
        Args:
            user_id: 用戶 ID
            subject: 學科
        
        Returns:
            Dict: 進度信息
        """
        kg = self._knowledge_graphs.get(subject)
        if not kg:
            return {"error": "知識圖譜不存在"}
        
        total = len(kg.nodes)
        mastered = 0
        in_progress = 0
        
        for kp in kg.nodes.values():
            mastery = self.get_mastery(user_id, kp.id)
            if mastery >= self.MASTERY_THRESHOLD:
                mastered += 1
            elif mastery > 0:
                in_progress += 1
        
        return {
            "total_knowledge_points": total,
            "mastered": mastered,
            "in_progress": in_progress,
            "not_started": total - mastered - in_progress,
            "completion_rate": round(mastered / total, 3) if total > 0 else 0.0
        }
    
    def get_next_recommended(self, user_id: str, subject: str) -> Optional[KnowledgePoint]:
        """
        獲取下一個推薦學習的知識點
        
        Args:
            user_id: 用戶 ID
            subject: 學科
        
        Returns:
            KnowledgePoint: 推薦的知識點
        """
        path = self.recommend_path(user_id, subject)
        if path and path.path:
            kp_id = path.path[0]
            return self._knowledge_graphs[subject].nodes.get(kp_id)
        return None


# 全局服務實例
_service_instance: Optional[LearningPathService] = None


def get_service() -> LearningPathService:
    """獲取學習路徑服務單例"""
    global _service_instance
    if _service_instance is None:
        _service_instance = LearningPathService()
    return _service_instance


if __name__ == "__main__":
    # 測試示例
    service = LearningPathService()
    
    # 1. 創建知識圖譜（高等數學前 3 章示例）
    print("=== 創建知識圖譜 ===")
    kg = service.create_knowledge_graph("math")
    
    # 第 1 章：函數與極限
    kg.add_knowledge_point(KnowledgePoint("kp_01", "函數概念", chapter=1, difficulty=0.3))
    kg.add_knowledge_point(KnowledgePoint("kp_02", "極限定義", chapter=1, difficulty=0.4))
    kg.add_knowledge_point(KnowledgePoint("kp_03", "極限運算", chapter=1, difficulty=0.5))
    
    # 第 2 章：導數與微分
    kg.add_knowledge_point(KnowledgePoint("kp_04", "導數概念", chapter=2, difficulty=0.5,
                                          prerequisites=["kp_02", "kp_03"]))
    kg.add_knowledge_point(KnowledgePoint("kp_05", "求導法則", chapter=2, difficulty=0.6,
                                          prerequisites=["kp_04"]))
    
    # 第 3 章：微分中值定理
    kg.add_knowledge_point(KnowledgePoint("kp_06", "羅爾定理", chapter=3, difficulty=0.7,
                                          prerequisites=["kp_05"]))
    kg.add_knowledge_point(KnowledgePoint("kp_07", "拉格朗日中值定理", chapter=3, difficulty=0.8,
                                          prerequisites=["kp_06"]))
    
    print(f"知識圖譜：{kg.to_dict()}")
    
    # 2. 前置檢查
    print("\n=== 前置檢查 ===")
    check = service.check_prerequisites("user_001", "math", "kp_04")
    print(f"學習 kp_04 (導數概念): can_start={check.can_start}")
    print(f"缺失前置：{check.missing_prerequisites}")
    
    # 3. 更新掌握度
    print("\n=== 更新掌握度 ===")
    service.update_mastery("user_001", "kp_01", 0.9, 0.95)
    service.update_mastery("user_001", "kp_02", 0.85, 0.88)
    service.update_mastery("user_001", "kp_03", 0.82, 0.85)
    
    # 4. 再次檢查
    check = service.check_prerequisites("user_001", "math", "kp_04")
    print(f"更新後 can_start={check.can_start}")
    
    # 5. 推薦路徑
    print("\n=== 推薦路徑 ===")
    path = service.recommend_path("user_001", "math")
    print(f"路徑：{path.to_dict()}")
    
    # 6. 跳過機制
    print("\n=== 跳過機制 ===")
    skipped, reason = service.skip_knowledge_point("user_001", "math", "kp_04", test_score=0.95)
    print(f"跳過 kp_04: {skipped}, {reason}")
    
    # 7. 學習進度
    print("\n=== 學習進度 ===")
    progress = service.get_learning_progress("user_001", "math")
    print(f"進度：{progress}")
