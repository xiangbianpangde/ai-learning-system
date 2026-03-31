/**
 * 思维导图组件 - React Flow 实现
 * 用于知识图谱可视化
 */

import React, { useCallback, useMemo } from 'react';
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
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Card, Button, Space, Input, Select, message } from 'antd';
import {
  PlusOutlined,
  SaveOutlined,
  ShareAltOutlined,
  DownloadOutlined,
  UnorderedListOutlined,
} from '@ant-design/icons';

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
}

const MindMapContent: React.FC<MindMapProps> = ({
  initialData,
  editable = true,
  onSave,
  height = 500,
}) => {
  const [nodes, setNodes, onNodesChange] = useNodesState<MindMapNodeData>(
    initialData?.nodes || initialNodes
  );
  const [edges, setEdges, onEdgesChange] = useEdgesState(
    initialData?.edges || initialEdges
  );

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
  const handleExport = useCallback(async () => {
    message.info('导出功能开发中...');
    // TODO: 使用 html-to-image 或 react-flow 的内置导出
  }, []);

  return (
    <Card
      title="🧠 知识思维导图"
      extra={
        editable && (
          <Space>
            <Select defaultValue="concept" style={{ width: 120 }}>
              <Select.Option value="root">根节点</Select.Option>
              <Select.Option value="concept">概念</Select.Option>
              <Select.Option value="detail">详情</Select.Option>
              <Select.Option value="example">示例</Select.Option>
            </Select>
            <Button
              icon={<PlusOutlined />}
              onClick={() => addNode('concept')}
            >
              添加节点
            </Button>
            <Button icon={<SaveOutlined />} onClick={handleSave}>
              保存
            </Button>
            <Button icon={<DownloadOutlined />} onClick={handleExport}>
              导出
            </Button>
          </Space>
        )
      }
      className="mb-4"
    >
      <div style={{ height: `${height}px`, width: '100%' }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={editable ? onConnect : undefined}
          fitView
          attributionPosition="bottom-left"
        >
          <Controls />
          <MiniMap
            nodeStrokeColor={(n) => n.data?.color || '#1a192b'}
            nodeColor={(n) => n.data?.color || '#fff'}
            nodeBorderRadius={8}
          />
          <Background variant="dots" gap={12} size={1} />
        </ReactFlow>
      </div>
    </Card>
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
