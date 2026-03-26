"""測試 knowledge_graph.py - 知識圖譜服務。

測試覆蓋：
- ✅ 分層加載
- ✅ 虛擬滾動
- ✅ 數據結構優化
- ✅ 進度回調
"""

import pytest
import time
from typing import List, Dict, Any
from edict.backend.app.services.knowledge_graph import (
    KnowledgeGraph,
    GraphNode,
    GraphEdge,
    GraphViewport,
    LoadProgress,
    KnowledgeGraphService,
    create_knowledge_graph,
    load_graph_from_points
)


class TestGraphNode:
    """測試 GraphNode 數據類。"""
    
    def test_node_creation(self):
        node = GraphNode(
            id="node_001",
            label="測試節點",
            type="concept",
            level=0,
            parent_id=None,
            children_ids=["node_002", "node_003"],
            metadata={"page": 1, "confidence": 0.9},
            is_loaded=True,
            child_count=2
        )
        
        assert node.id == "node_001"
        assert node.label == "測試節點"
        assert node.type == "concept"
        assert len(node.children_ids) == 2
    
    def test_node_to_dict(self):
        node = GraphNode(
            id="node_002",
            label="子節點",
            type="definition",
            level=1,
            parent_id="node_001"
        )
        
        data = node.to_dict()
        
        assert data["id"] == "node_002"
        assert data["label"] == "子節點"
        assert data["parent_id"] == "node_001"
        assert data["is_loaded"] is False
        assert data["child_count"] == 0
    
    def test_node_from_dict(self):
        data = {
            "id": "node_003",
            "label": "從字典創建",
            "type": "formula",
            "level": 2,
            "parent_id": "node_002",
            "children_ids": [],
            "metadata": {},
            "is_loaded": False,
            "child_count": 0
        }
        
        node = GraphNode.from_dict(data)
        
        assert node.id == "node_003"
        assert node.type == "formula"
        assert node.level == 2


class TestGraphEdge:
    """測試 GraphEdge 數據類。"""
    
    def test_edge_creation(self):
        edge = GraphEdge(
            source="node_001",
            target="node_002",
            type="related",
            weight=0.8,
            metadata={"strength": "strong"}
        )
        
        assert edge.source == "node_001"
        assert edge.target == "node_002"
        assert edge.weight == 0.8
    
    def test_edge_to_dict(self):
        edge = GraphEdge(source="A", target="B")
        data = edge.to_dict()
        
        assert data["source"] == "A"
        assert data["target"] == "B"
        assert data["type"] == "related"
        assert data["weight"] == 1.0


class TestLoadProgress:
    """測試 LoadProgress 數據類。"""
    
    def test_progress_creation(self):
        progress = LoadProgress(
            loaded_nodes=500,
            total_nodes=1000,
            percentage=50.0,
            status="loading",
            elapsed_ms=1500.0
        )
        
        assert progress.loaded_nodes == 500
        assert progress.total_nodes == 1000
        assert progress.percentage == 50.0
    
    def test_progress_to_dict(self):
        progress = LoadProgress(
            loaded_nodes=100,
            total_nodes=1000,
            percentage=10.0,
            status="ready",
            elapsed_ms=500.0
        )
        
        data = progress.to_dict()
        assert data["status"] == "ready"
        assert data["elapsed_ms"] == 500.0


class TestKnowledgeGraph:
    """測試 KnowledgeGraph 類。"""
    
    def test_graph_initialization(self):
        graph = KnowledgeGraph(max_visible_nodes=100)
        
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0
        assert graph.max_visible_nodes == 100
    
    def test_add_node(self):
        graph = KnowledgeGraph()
        
        node = GraphNode(
            id="node_001",
            label="根節點",
            type="concept",
            level=0
        )
        
        graph.add_node(node)
        
        assert "node_001" in graph.nodes
        assert graph.root_ids == ["node_001"]
        assert "node_001" in graph._type_index["concept"]
    
    def test_add_node_with_parent(self):
        graph = KnowledgeGraph()
        
        parent = GraphNode(id="parent", label="父節點", type="concept")
        child = GraphNode(
            id="child",
            label="子節點",
            type="concept",
            parent_id="parent",
            children_ids=[]
        )
        
        graph.add_node(parent)
        graph.add_node(child)
        
        assert "child" in graph._children_index["parent"]
        assert graph._parent_index["child"] == "parent"
    
    def test_add_edge(self):
        graph = KnowledgeGraph()
        
        edge = GraphEdge(source="A", target="B", type="related")
        graph.add_edge(edge)
        
        assert len(graph.edges) == 1
        assert graph.edges[0].source == "A"
    
    def test_get_node(self):
        graph = KnowledgeGraph()
        
        node = GraphNode(id="test", label="測試", type="concept")
        graph.add_node(node)
        
        retrieved = graph.get_node("test")
        assert retrieved is not None
        assert retrieved.label == "測試"
        
        not_found = graph.get_node("nonexistent")
        assert not_found is None
    
    def test_get_children(self):
        graph = KnowledgeGraph()
        
        parent = GraphNode(id="parent", label="父", type="concept", children_ids=["c1", "c2", "c3"])
        c1 = GraphNode(id="c1", label="子 1", type="concept", parent_id="parent")
        c2 = GraphNode(id="c2", label="子 2", type="concept", parent_id="parent")
        c3 = GraphNode(id="c3", label="子 3", type="concept", parent_id="parent")
        
        graph.add_node(parent)
        graph.add_node(c1)
        graph.add_node(c2)
        graph.add_node(c3)
        
        children = graph.get_children("parent", limit=2)
        
        assert len(children) == 2  # 限制為 2
        assert all(c.id in ["c1", "c2", "c3"] for c in children)
    
    def test_get_subtree(self):
        graph = KnowledgeGraph()
        
        # 創建樹狀結構
        root = GraphNode(id="root", label="根", type="concept", children_ids=["n1", "n2"])
        n1 = GraphNode(id="n1", label="節點 1", type="concept", parent_id="root", children_ids=["n11"])
        n2 = GraphNode(id="n2", label="節點 2", type="concept", parent_id="root")
        n11 = GraphNode(id="n11", label="節點 1-1", type="concept", parent_id="n1")
        
        for node in [root, n1, n2, n11]:
            graph.add_node(node)
        
        subtree = graph.get_subtree("root", max_depth=1, max_nodes=10)
        
        assert len(subtree) <= 3  # root + n1 + n2 (n11 在第 2 層，被排除)
        assert any(n.id == "root" for n in subtree)
    
    def test_get_visible_nodes(self):
        graph = KnowledgeGraph()
        
        # 創建多個節點
        for i in range(20):
            node = GraphNode(
                id=f"node_{i}",
                label=f"節點{i}",
                type="concept",
                level=0
            )
            graph.add_node(node)
        
        # 獲取可見節點（虛擬滾動）
        visible = graph.get_visible_nodes(
            expanded_nodes=set(),
            scroll_offset=0,
            viewport_size=10
        )
        
        assert len(visible) <= 20  # 最多返回所有節點
    
    def test_get_viewport_info(self):
        graph = KnowledgeGraph()
        
        for i in range(50):
            node = GraphNode(id=f"n{i}", label=f"N{i}", type="concept")
            graph.add_node(node)
        
        viewport = graph.get_viewport_info(
            expanded_nodes=set(),
            scroll_offset=10,
            viewport_size=20
        )
        
        assert viewport.visible_start == 10
        assert viewport.visible_end == 30
        assert viewport.total_nodes == 50
    
    def test_load_from_knowledge_points(self):
        graph = KnowledgeGraph()
        
        knowledge_points = [
            {"title": "知識點 1", "content": "內容 1", "page": 1, "confidence": 0.9, "tags": ["concept"]},
            {"title": "知識點 2", "content": "內容 2", "page": 2, "confidence": 0.8, "tags": ["definition"]},
            {"title": "知識點 3", "content": "內容 3", "page": 3, "confidence": 0.95, "tags": ["formula"]},
        ]
        
        progress_calls = []
        
        def progress_callback(progress: LoadProgress):
            progress_calls.append(progress)
        
        graph.set_load_progress_callback(progress_callback)
        graph.load_from_knowledge_points(knowledge_points, batch_size=2)
        
        assert len(graph.nodes) == 3
        assert len(progress_calls) > 0  # 應該有進度回調
    
    def test_to_dict(self):
        graph = KnowledgeGraph()
        
        node = GraphNode(id="test", label="測試", type="concept")
        graph.add_node(node)
        
        data = graph.to_dict()
        
        assert "nodes" in data
        assert "edges" in data
        assert "root_ids" in data
        assert len(data["nodes"]) == 1
    
    def test_to_flat_dict(self):
        graph = KnowledgeGraph()
        
        for i in range(5):
            node = GraphNode(id=f"n{i}", label=f"N{i}", type="concept")
            graph.add_node(node)
        
        flat = graph.to_flat_dict()
        
        assert "nodes" in flat
        assert "edges" in flat
        assert "roots" in flat
        
        # 檢查字段縮寫
        node_data = list(flat["nodes"].values())[0]
        assert "l" in node_data  # label
        assert "t" in node_data  # type


class TestKnowledgeGraphService:
    """測試 KnowledgeGraphService 類。"""
    
    def test_create_graph(self):
        service = KnowledgeGraphService()
        
        graph = service.create_graph("test_graph")
        
        assert isinstance(graph, KnowledgeGraph)
        assert "test_graph" in service._graphs
    
    def test_get_graph(self):
        service = KnowledgeGraphService()
        service.create_graph("graph_1")
        
        graph = service.get_graph("graph_1")
        assert graph is not None
        
        not_found = service.get_graph("nonexistent")
        assert not_found is None
    
    def test_max_graphs_limit(self):
        service = KnowledgeGraphService()
        service._max_graphs = 2
        
        service.create_graph("graph_1")
        service.create_graph("graph_2")
        service.create_graph("graph_3")
        
        assert len(service._graphs) <= 2
        assert "graph_3" in service._graphs
        assert "graph_1" not in service._graphs  # 最舊的被移除
    
    def test_load_from_pdf(self):
        service = KnowledgeGraphService()
        
        knowledge_points = [
            {"title": "KP1", "content": "C1", "page": 1, "tags": ["concept"]},
            {"title": "KP2", "content": "C2", "page": 2, "tags": ["concept"]},
        ]
        
        graph = service.load_from_pdf("pdf_graph", knowledge_points)
        
        assert isinstance(graph, KnowledgeGraph)
        assert len(graph.nodes) == 2
    
    def test_get_node_tree(self):
        service = KnowledgeGraphService()
        
        root = GraphNode(id="root", label="根", type="concept", children_ids=["c1"])
        child = GraphNode(id="c1", label="子", type="concept", parent_id="root")
        
        graph = service.create_graph("tree_graph")
        graph.add_node(root)
        graph.add_node(child)
        
        tree = service.get_node_tree("tree_graph", "root", depth=2)
        
        assert "nodes" in tree
        assert "root_id" in tree
        assert len(tree["nodes"]) >= 1
    
    def test_get_visible_nodes(self):
        service = KnowledgeGraphService()
        
        graph = service.create_graph("visible_graph")
        for i in range(30):
            node = GraphNode(id=f"n{i}", label=f"N{i}", type="concept")
            graph.add_node(node)
        
        result = service.get_visible_nodes(
            "visible_graph",
            expanded_nodes=[],
            scroll_offset=0,
            viewport_size=10
        )
        
        assert "nodes" in result
        assert "viewport" in result


class TestConvenienceFunctions:
    """測試便捷函數。"""
    
    def test_create_knowledge_graph(self):
        graph = create_knowledge_graph()
        
        assert isinstance(graph, KnowledgeGraph)
    
    def test_load_graph_from_points(self):
        knowledge_points = [
            {"title": "測試", "content": "內容", "page": 1, "tags": ["test"]},
        ]
        
        graph = load_graph_from_points(knowledge_points)
        
        assert isinstance(graph, KnowledgeGraph)
        assert len(graph.nodes) == 1


class TestPerformance:
    """性能測試。"""
    
    def test_large_graph_loading(self):
        """測試大型圖譜加載性能。"""
        graph = KnowledgeGraph()
        
        # 創建 1000 個節點
        knowledge_points = [
            {
                "title": f"知識點{i}",
                "content": f"內容{i}" * 10,
                "page": i % 100,
                "confidence": 0.9,
                "tags": ["concept"]
            }
            for i in range(1000)
        ]
        
        start_time = time.time()
        graph.load_from_knowledge_points(knowledge_points, batch_size=100)
        elapsed = time.time() - start_time
        
        assert elapsed < 2.0, f"加載時間過長：{elapsed}秒"
        assert len(graph.nodes) == 1000
    
    def test_subtree_extraction(self):
        """測試子樹提取性能。"""
        graph = KnowledgeGraph()
        
        # 創建層級結構
        nodes = []
        for i in range(500):
            parent_id = f"n{i//10}" if i >= 10 else None
            children_ids = [f"n{j}" for j in range(i*10, min(i*10+10, 500))] if i < 50 else []
            
            node = GraphNode(
                id=f"n{i}",
                label=f"節點{i}",
                type="concept",
                parent_id=parent_id,
                children_ids=children_ids,
                level=i // 10
            )
            nodes.append(node)
            graph.add_node(node)
        
        start_time = time.time()
        subtree = graph.get_subtree("n0", max_depth=3, max_nodes=100)
        elapsed = time.time() - start_time
        
        assert elapsed < 0.5, f"子樹提取過慢：{elapsed}秒"
        assert len(subtree) <= 100


class TestEdgeCases:
    """邊界情況測試。"""
    
    def test_empty_graph(self):
        graph = KnowledgeGraph()
        
        assert graph.get_node("nonexistent") is None
        assert graph.get_children("nonexistent") == []
        assert graph.get_subtree("nonexistent") == []
    
    def test_single_node_graph(self):
        graph = KnowledgeGraph()
        
        node = GraphNode(id="single", label="唯一節點", type="concept")
        graph.add_node(node)
        
        subtree = graph.get_subtree("single")
        assert len(subtree) == 1
    
    def test_circular_reference_protection(self):
        """測試循環引用保護（間接測試）。"""
        graph = KnowledgeGraph()
        
        # 創建可能導致循環的結構
        n1 = GraphNode(id="n1", label="N1", type="concept", children_ids=["n2"])
        n2 = GraphNode(id="n2", label="N2", type="concept", children_ids=["n3"])
        n3 = GraphNode(id="n3", label="N3", type="concept")
        
        graph.add_node(n1)
        graph.add_node(n2)
        graph.add_node(n3)
        
        # 應該正常完成，不會無限循環
        subtree = graph.get_subtree("n1", max_depth=5, max_nodes=100)
        assert len(subtree) <= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
