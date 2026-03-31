/**
 * AI 内容生成器 UI
 * - 降阶法内容生成
 * - 知识图谱可视化
 */

import React, { useState } from 'react';
import {
  Card,
  Form,
  Input,
  Select,
  Button,
  Space,
  Collapse,
  List,
  Tag,
  message,
  Spin,
  Result,
} from 'antd';
import {
  RobotOutlined,
  ThunderboltOutlined,
  BranchesOutlined,
  BookOutlined,
  QuestionCircleOutlined,
  LoadingOutlined,
} from '@ant-design/icons';
import aiService, {
  type SimplificationRequest,
  type KnowledgeGraphRequest,
  type KnowledgeGraph,
} from '../../services/ai/content';
import MindMap from '../mindmap/MindMap';
import { type Node, type Edge } from '@xyflow/react';

const { TextArea } = Input;
const { Panel } = Collapse;

interface AIContentGeneratorProps {
  onContentGenerated?: (content: any) => void;
  onGraphExtracted?: (graph: KnowledgeGraph) => void;
}

const AIContentGenerator: React.FC<AIContentGeneratorProps> = ({
  onContentGenerated,
  onGraphExtracted,
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'simplify' | 'graph'>('simplify');
  const [simplifiedResult, setSimplifiedResult] = useState<any>(null);
  const [knowledgeGraph, setKnowledgeGraph] = useState<KnowledgeGraph | null>(null);

  // 降阶法内容生成
  const handleSimplify = async (values: any) => {
    setLoading(true);
    try {
      const request: SimplificationRequest = {
        content: values.content,
        targetLevel: values.targetLevel,
        style: values.style,
        maxLength: values.maxLength,
      };

      const result = await aiService.simplifyContent(request);
      setSimplifiedResult(result);
      onContentGenerated?.(result);
      message.success('内容简化完成！');
    } catch (error: any) {
      message.error(`生成失败：${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 知识图谱提取
  const handleExtractGraph = async (values: any) => {
    setLoading(true);
    try {
      const request: KnowledgeGraphRequest = {
        text: values.content,
        domain: values.domain,
        maxNodes: values.maxNodes || 20,
        maxRelations: values.maxRelations || 30,
      };

      const graph = await aiService.extractKnowledgeGraph(request);
      setKnowledgeGraph(graph);
      onGraphExtracted?.(graph);
      message.success('知识图谱提取完成！');
    } catch (error: any) {
      message.error(`提取失败：${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 将知识图谱转换为 React Flow 格式
  const convertToFlowData = (graph: KnowledgeGraph) => {
    const nodes: Node[] = graph.nodes.map((node, index) => ({
      id: node.id,
      type: 'default',
      position: {
        x: (index % 5) * 250 + 100,
        y: Math.floor(index / 5) * 150 + 50,
      },
      data: {
        label: node.label,
        type: node.type,
        description: node.description,
      },
      style: {
        background: getNodeColor(node.type),
        border: '2px solid #1890ff',
        borderRadius: 8,
        padding: '12px 16px',
        maxWidth: 200,
      },
    }));

    const edges: Edge[] = graph.edges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      label: edge.label || edge.type,
      type: 'smoothstep',
      animated: true,
    }));

    return { nodes, edges };
  };

  const getNodeColor = (type: string) => {
    const colors: Record<string, string> = {
      concept: '#e6f7ff',
      term: '#f6ffed',
      person: '#fff7e6',
      event: '#fff0f6',
      theory: '#f0f5ff',
      example: '#fcffe6',
    };
    return colors[type] || '#ffffff';
  };

  return (
    <Card
      title={
        <Space>
          <RobotOutlined />
          <span>🤖 AI 内容生成器</span>
        </Space>
      }
      tabList={[
        {
          key: 'simplify',
          label: (
            <Space>
              <ThunderboltOutlined />
              降阶法生成
            </Space>
          ),
        },
        {
          key: 'graph',
          label: (
            <Space>
              <BranchesOutlined />
              知识图谱
            </Space>
          ),
        },
      ]}
      activeTabKey={activeTab}
      onTabChange={(key) => {
        setActiveTab(key);
        setSimplifiedResult(null);
        setKnowledgeGraph(null);
      }}
    >
      {activeTab === 'simplify' && (
        <Form form={form} layout="vertical" onFinish={handleSimplify}>
          <Form.Item
            name="content"
            label="原始内容"
            rules={[{ required: true, message: '请输入内容' }]}
          >
            <TextArea
              rows={6}
              placeholder="输入需要简化的复杂概念或内容..."
            />
          </Form.Item>

          <Form.Item
            name="targetLevel"
            label="目标水平"
            initialValue="middle"
          >
            <Select>
              <Select.Option value="elementary">小学水平</Select.Option>
              <Select.Option value="middle">初中水平</Select.Option>
              <Select.Option value="high">高中水平</Select.Option>
              <Select.Option value="college">大学水平</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item name="style" label="生成风格" initialValue="explanation">
            <Select>
              <Select.Option value="explanation">解释说明</Select.Option>
              <Select.Option value="story">故事化</Select.Option>
              <Select.Option value="analogy">类比</Select.Option>
              <Select.Option value="example">示例驱动</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                icon={loading ? <LoadingOutlined /> : <ThunderboltOutlined />}
                size="large"
              >
                生成简化内容
              </Button>
            </Space>
          </Form.Item>
        </Form>
      )}

      {activeTab === 'graph' && (
        <Form form={form} layout="vertical" onFinish={handleExtractGraph}>
          <Form.Item
            name="content"
            label="文本内容"
            rules={[{ required: true, message: '请输入内容' }]}
          >
            <TextArea
              rows={6}
              placeholder="输入教材、文章或讲义内容，AI 将自动提取知识图谱..."
            />
          </Form.Item>

          <Form.Item name="domain" label="领域">
            <Select allowClear>
              <Select.Option value="math">数学</Select.Option>
              <Select.Option value="physics">物理</Select.Option>
              <Select.Option value="chemistry">化学</Select.Option>
              <Select.Option value="biology">生物</Select.Option>
              <Select.Option value="history">历史</Select.Option>
              <Select.Option value="literature">文学</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item name="maxNodes" label="最大节点数" initialValue={20}>
            <Select>
              <Select.Option value={10}>10 个</Select.Option>
              <Select.Option value={20}>20 个</Select.Option>
              <Select.Option value={50}>50 个</Select.Option>
              <Select.Option value={100}>100 个</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                icon={loading ? <LoadingOutlined /> : <BranchesOutlined />}
                size="large"
              >
                提取知识图谱
              </Button>
            </Space>
          </Form.Item>
        </Form>
      )}

      {loading && (
        <div className="text-center py-8">
          <Spin size="large" tip="AI 正在处理中..." />
        </div>
      )}

      {/* 降阶法结果 */}
      {simplifiedResult && activeTab === 'simplify' && (
        <div className="mt-6">
          <Card
            size="small"
            title="✅ 简化结果"
            extra={
              <Tag color="blue">{simplifiedResult.level}</Tag>
            }
          >
            <div className="whitespace-pre-wrap text-gray-700">
              {simplifiedResult.simplified}
            </div>
          </Card>

          {simplifiedResult.analogies?.length > 0 && (
            <Card size="small" title="💡 类比解释" className="mt-4">
              <List
                dataSource={simplifiedResult.analogies}
                renderItem={(item) => (
                  <List.Item>• {item}</List.Item>
                )}
              />
            </Card>
          )}

          {simplifiedResult.examples?.length > 0 && (
            <Card size="small" title="📖 示例" className="mt-4">
              <List
                dataSource={simplifiedResult.examples}
                renderItem={(item) => (
                  <List.Item>• {item}</List.Item>
                )}
              />
            </Card>
          )}

          {simplifiedResult.quiz?.length > 0 && (
            <Card
              size="small"
              title="📝 小测验"
              className="mt-4"
              extra={<QuestionCircleOutlined />}
            >
              <Collapse>
                {simplifiedResult.quiz.map((q: any, index: number) => (
                  <Panel header={`问题 ${index + 1}: ${q.question}`} key={index}>
                    <List
                      dataSource={q.options}
                      renderItem={(option, i) => (
                        <List.Item
                          style={{
                            background:
                              i === q.correctAnswer ? '#f6ffed' : 'transparent',
                          }}
                        >
                          {String.fromCharCode(65 + i)}. {option}
                        </List.Item>
                      )}
                    />
                    {q.explanation && (
                      <div className="mt-2 text-gray-600">
                        💡 {q.explanation}
                      </div>
                    )}
                  </Panel>
                ))}
              </Collapse>
            </Card>
          )}
        </div>
      )}

      {/* 知识图谱结果 */}
      {knowledgeGraph && activeTab === 'graph' && (
        <div className="mt-6">
          <Card
            size="small"
            title="📊 知识图谱概览"
            className="mb-4"
          >
            <p className="text-gray-600">{knowledgeGraph.summary}</p>
            <div className="mt-4 flex gap-4">
              <Tag color="blue">节点：{knowledgeGraph.nodes.length}</Tag>
              <Tag color="green">关系：{knowledgeGraph.edges.length}</Tag>
              <Tag color="purple">
                核心概念：{knowledgeGraph.rootConcepts.join(', ')}
              </Tag>
            </div>
          </Card>

          <MindMap
            initialData={{
              id: 'extracted-graph',
              title: '知识图谱',
              ...convertToFlowData(knowledgeGraph),
            }}
            editable={false}
            height={500}
          />
        </div>
      )}
    </Card>
  );
};

export default AIContentGenerator;
