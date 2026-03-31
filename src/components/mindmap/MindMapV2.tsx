/**
 * 思维导图组件 v2 - React Flow 实现
 * 用于知识图谱可视化
 * 新增功能:
 * - 导出为图片 (PNG/SVG)
 * - 节点搜索与过滤
 * - 自动布局优化
 * - 节点批量操作
 */

import React, { useCallback, useMemo, useState, useRef } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  MarkerType,
  Position,
  ReactFlowProvider,
  MiniMap,
  useReactFlow,
  Panel,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Card, Button, Space, Input, Select, message, Modal, Dropdown, MenuProps } from 'antd';
import {
  PlusOutlined,
  SaveOutlined,
  ShareAltOutlined,
  DownloadOutlined,
  UnorderedListOutlined,
  SearchOutlined,
  LayoutOutlined,
  CopyOutlined,
  DeleteOutlined,
  ZoomInOutlined,
  ZoomOutOutlined,
} from '@ant-design/icons';
import { toPng, toSvg } from 'html-to-image';

// 节点类型定义
export type MindMapNodeType = 'root' | 'concept' | 'detail' | 'example';

export interface MindMapNodeData {
  label: string;
  type: MindMapNodeType;
  description?: string;
  color?: string;
}

export interface MindMapData {
  id: string;
  title: string;
  nodes: Node<MindMapNodeData>[];
  edges: Edge[];
}

// 节点样式配置
const nodeStyleConfig: Record<MindMapNodeType, { bg: string; border: string; color: string }> = {
  root: { bg: '#1890ff', border: '#096dd9', color: 'white' },
  concept: { bg: '#e6f7ff', border: '#1890ff', color: '#0050b3' },
  detail: { bg: '#f6ffed', border: '#52c41a', color: '#237804' },
  example: { bg: '#fff7e6', border: '#faad14', color: '#d46b08' },
};

// 初始节点
const initialNodes: Node<MindMapNodeData>[] = [
  {
    id: '1',
    type: 'default',
    position: { x: 400, y: 50 },
    data: { label: '核心概念', type: 'root', color: nodeStyleConfig.root.bg },
    style: {
      background: nodeStyleConfig.root.bg,
      color: nodeStyleConfig.root.color,
      border: `2px solid ${nodeStyleConfig.root.border}`,
      borderRadius: 8,
      padding: '12px 24px',
      fontWeight: 'bold',
    },
  },
  {
    id: '2',
    type: 'default',
    position: { x: 200, y: 200 },
    data: { label: '子概念 A', type: 'concept', color: nodeStyleConfig.concept.bg },
    style: {
      background: nodeStyleConfig.concept.bg,
      color: nodeStyleConfig.concept.color,
      border: `2px solid ${nodeStyleConfig.concept.border}`,
      borderRadius: 6,
      padding: '10px 16px',
    },
  },
  {
    id: '3',
    type: 'default',
    position: { x: 600, y: 200 },
    data: { label: '子概念 B', type: 'concept', color: nodeStyleConfig.concept.bg },
    style: {
      background: nodeStyleConfig.concept.bg,
      color: nodeStyleConfig.concept.color,
      border: `2px solid ${nodeStyleConfig.concept.border}`,
      borderRadius: 6,
      padding: '10px 16px',
    },
  },
  {
    id: '4',
    type: 'default',
    position: { x: 150, y: 350 },
    data: { label: '详细说明', type: 'detail', color: nodeStyleConfig.detail.bg },
    style: {
      background: nodeStyleConfig.detail.bg,
      color: nodeStyleConfig.detail.color,
      border: `2px solid ${nodeStyleConfig.detail.border}`,
      borderRadius: 6,
      padding: '8px 12px',
      fontSize: '12px',
    },
  },
  {
    id: '5',
    type: 'default',
    position: { x: 650, y: 350 },
    data: { label: '示例', type: 'example', color: nodeStyleConfig.example.bg },
    style: {
      background: nodeStyleConfig.example.bg,
      color: nodeStyleConfig.example.color,
      border: `2px solid ${nodeStyleConfig.example.border}`,
      borderRadius: 6,
      padding: '8px 12px',
      fontSize: '12px',
    },
  },
];

const initialEdges: Edge[] = [
  { id: 'e1-2', source: '1', target: '2', markerEnd: { type: MarkerType.ArrowClosed } },
  { id: 'e1-3', source: '1', target: '3', markerEnd: { type: MarkerType.ArrowClosed } },
  { id: 'e2-4', source: '2', target: '4', markerEnd: { type: MarkerType.ArrowClosed } },
  { id: 'e3-5', source: '3', target: '5', markerEnd: { type: MarkerType.ArrowClosed } },
];

interface MindMapProps {
  initialData?: MindMapData;
  editable?: boolean;
  onSave?: (data: MindMapData) => void;
  height?: number;
  showExport?: boolean;
  showSearch?: boolean;
}

// 自定义工具栏组件
const CustomToolbar = ({ 
  onAddNode, 
  onExport, 
  onLayout, 
  onSearch,
  searchValue,
  onSearchChange,
}: {
  onAddNode: (type: MindMapNodeType) => void;
  onExport: (format: 'png' | 'svg') => void;
  onLayout: () => void;
  onSearch: (value: string) => void;
  searchValue: string;
  onSearchChange: (value: string) => void;
}) => {
  return (
    <Panel position="top-right" style={{ background: 'white', padding: 8, borderRadius: 8, boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
      <Space direction="vertical" size="small">
        <Input
          placeholder="搜索节点..."
          prefix={<SearchOutlined />}
          value={searchValue}
          onChange={(e) => onSearchChange(e.target.value)}
          onPressEnter={() => onSearch(searchValue)}
          style={{ width: 180 }}
          size="small"
        />
        <Select
          defaultValue="concept"
          style={{ width: 120 }}
          size="small"
          onChange={(value) => onAddNode(value)}
        >
          <Select.Option value="root">根节点</Select.Option>
          <Select.Option value="concept">概念</Select.Option>
          <Select.Option value="detail">详情</Select.Option>
          <Select.Option value="example">示例</Select.Option>
        </Select>
        <Button
          icon={<DownloadOutlined />}
          onClick={() => onExport('png')}
          size="small"
          block
        >
          导出 PNG
        </Button>
        <Button
          icon={<DownloadOutlined />}
          onClick={() => onExport('svg')}
          size="small"
          block
        >
          导出 SVG
        </Button>
        <Button
          icon={<LayoutOutlined />}
          onClick={onLayout}
          size="small"
          block
        >
          自动布局
        </Button>
      </Space>
    </Panel>
  );
};

const MindMapContent: React.FC<MindMapProps> = ({
  initialData,
  editable = true,
  onSave,
  height = 500,
  showExport = true,
  showSearch = true,
}) => {
  const [nodes, setNodes, onNodesChange] = useNodesState<MindMapNodeData>(
    initialData?.nodes || initialNodes
  );
  const [edges, setEdges, onEdgesChange] = useEdgesState(
    initialData?.edges || initialEdges
  );
  const [searchValue, setSearchValue] = useState('');
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const { fitView, zoomIn, zoomOut } = useReactFlow();

  const onConnect = useCallback(
    (params: Connection) => {
      if (editable) {
        setEdges((eds) =>
          addEdge(
            {
              ...params,
              markerEnd: { type: MarkerType.ArrowClosed },
              type: 'smoothstep',
              animated: true,
            },
            eds
          )
        );
      }
    },
    [setEdges, editable]
  );

  // 添加新节点
  const addNode = useCallback((type: MindMapNodeType = 'concept') => {
    const newNode: Node<MindMapNodeData> = {
      id: `node-${Date.now()}`,
      type: 'default',
      position: {
        x: Math.random() * 400 + 200,
        y: Math.random() * 300 + 200,
      },
      data: {
        label: `新节点 ${type}`,
        type,
        color: nodeStyleConfig[type].bg,
      },
      style: {
        background: nodeStyleConfig[type].bg,
        color: nodeStyleConfig[type].color,
        border: `2px solid ${nodeStyleConfig[type].border}`,
        borderRadius: 6,
        padding: '10px 16px',
      },
    };
    setNodes((nds) => [...nds, newNode]);
    message.success('节点已添加');
  }, [setNodes]);

  // 保存思维导图
  const handleSave = useCallback(() => {
    const data: MindMapData = {
      id: initialData?.id || `mindmap-${Date.now()}`,
      title: initialData?.title || '未命名思维导图',
      nodes: nodes as Node<MindMapNodeData>[],
      edges,
    };
    onSave?.(data);
    message.success('思维导图已保存');
  }, [nodes, edges, onSave, initialData]);

  // 导出为图片
  const handleExport = useCallback(async (format: 'png' | 'svg') => {
    if (!reactFlowWrapper.current) {
      message.error('导出失败：无法找到画布');
      return;
    }

    try {
      const exportFunction = format === 'png' ? toPng : toSvg;
      const dataUrl = await exportFunction(reactFlowWrapper.current, {
        quality: 1.0,
        backgroundColor: '#ffffff',
        pixelRatio: 2,
      });

      const link = document.createElement('a');
      link.download = `mindmap-${Date.now()}.${format}`;
      link.href = dataUrl;
      link.click();
      
      message.success(`已导出 ${format.toUpperCase()} 格式`);
    } catch (error) {
      console.error('Export error:', error);
      message.error(`导出失败：${error}`);
    }
  }, []);

  // 自动布局 (简化版：重新排列节点)
  const handleLayout = useCallback(() => {
    const newNodes = nodes.map((node, index) => ({
      ...node,
      position: {
        x: (index % 5) * 250 + 100,
        y: Math.floor(index / 5) * 150 + 50,
      },
    }));
    setNodes(newNodes);
    fitView({ padding: 0.2 });
    message.success('布局已优化');
  }, [nodes, setNodes, fitView]);

  // 搜索节点
  const handleSearch = useCallback((value: string) => {
    if (!value.trim()) {
      message.warning('请输入搜索内容');
      return;
    }

    const foundNode = nodes.find(
      (node) => node.data?.label.toLowerCase().includes(value.toLowerCase())
    );

    if (foundNode) {
      setSelectedNode(foundNode.id);
      // 聚焦到该节点
      fitView({ 
        nodes: [foundNode], 
        padding: 0.2 
      });
      message.success(`找到节点：${foundNode.data.label}`);
    } else {
      message.warning('未找到匹配的节点');
    }
  }, [nodes, fitView]);

  // 节点点击处理
  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    setSelectedNode(node.id);
  }, []);

  // 删除选中节点
  const deleteSelectedNode = useCallback(() => {
    if (!selectedNode) {
      message.warning('请先选择节点');
      return;
    }

    setNodes((nds) => nds.filter((node) => node.id !== selectedNode));
    setEdges((eds) => eds.filter((edge) => edge.source !== selectedNode && edge.target !== selectedNode));
    setSelectedNode(null);
    message.success('节点已删除');
  }, [selectedNode, setNodes, setEdges]);

  // 复制选中节点
  const duplicateSelectedNode = useCallback(() => {
    if (!selectedNode) {
      message.warning('请先选择节点');
      return;
    }

    const nodeToDuplicate = nodes.find((n) => n.id === selectedNode);
    if (nodeToDuplicate) {
      const newNode: Node<MindMapNodeData> = {
        ...nodeToDuplicate,
        id: `node-${Date.now()}`,
        position: {
          x: nodeToDuplicate.position.x + 50,
          y: nodeToDuplicate.position.y + 50,
        },
      };
      setNodes((nds) => [...nds, newNode]);
      message.success('节点已复制');
    }
  }, [selectedNode, nodes, setNodes]);

  // 键盘快捷键
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Delete' && selectedNode) {
        deleteSelectedNode();
      }
      if ((e.ctrlKey || e.metaKey) && e.key === 'd' && selectedNode) {
        e.preventDefault();
        duplicateSelectedNode();
      }
      if ((e.ctrlKey || e.metaKey) && e.key === 's' && onSave) {
        e.preventDefault();
        handleSave();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedNode, deleteSelectedNode, duplicateSelectedNode, handleSave, onSave]);

  // 上下文菜单
  const contextMenuItems: MenuProps['items'] = [
    {
      key: 'duplicate',
      label: '复制节点',
      icon: <CopyOutlined />,
      onClick: duplicateSelectedNode,
    },
    {
      key: 'delete',
      label: '删除节点',
      icon: <DeleteOutlined />,
      danger: true,
      onClick: deleteSelectedNode,
    },
  ];

  return (
    <div ref={reactFlowWrapper} style={{ height: `${height}px`, width: '100%' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={editable ? onConnect : undefined}
        onNodeClick={onNodeClick}
        fitView
        attributionPosition="bottom-left"
        deleteKeyCode={null}
      >
        <Controls showInteractive={false} />
        <MiniMap
          nodeStrokeColor={(n) => n.data?.color || '#1a192b'}
          nodeColor={(n) => n.data?.color || '#fff'}
          nodeBorderRadius={8}
          zoomable
          pannable
        />
        <Background variant="dots" gap={12} size={1} />
        
        {editable && (
          <CustomToolbar
            onAddNode={addNode}
            onExport={handleExport}
            onLayout={handleLayout}
            onSearch={handleSearch}
            searchValue={searchValue}
            onSearchChange={setSearchValue}
          />
        )}

        {/* 顶部工具栏 */}
        <Panel position="top-left">
          <Space>
            <Button
              icon={<ZoomInOutlined />}
              onClick={() => zoomIn()}
              size="small"
            />
            <Button
              icon={<ZoomOutOutlined />}
              onClick={() => zoomOut()}
              size="small"
            />
            {selectedNode && (
              <Dropdown menu={{ items: contextMenuItems }} trigger={['click']}>
                <Button size="small">
                  节点操作 <span style={{ marginLeft: 4 }}>▼</span>
                </Button>
              </Dropdown>
            )}
            {onSave && (
              <Button
                icon={<SaveOutlined />}
                onClick={handleSave}
                size="small"
              >
                保存
              </Button>
            )}
          </Space>
        </Panel>

        {/* 状态栏 */}
        <Panel position="bottom-left">
          <div style={{ 
            background: 'white', 
            padding: '4px 8px', 
            borderRadius: 4,
            fontSize: 12,
            boxShadow: '0 1px 4px rgba(0,0,0,0.1)'
          }}>
            节点：{nodes.length} | 连接：{edges.length}
            {selectedNode && ` | 选中：${selectedNode}`}
          </div>
        </Panel>
      </ReactFlow>
    </div>
  );
};

// 包装组件 (提供 ReactFlowProvider)
const MindMap: React.FC<MindMapProps> = (props) => {
  return (
    <ReactFlowProvider>
      <MindMapContent {...props} />
    </ReactFlowProvider>
  );
};

export default MindMap;
