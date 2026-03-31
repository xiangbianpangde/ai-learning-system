/**
 * AI 内容生成服务
 * - 降阶法内容生成 (将复杂概念简化为易懂内容)
 * - 知识图谱提取
 */

import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

// ==================== 降阶法内容生成 ====================

export interface SimplificationRequest {
  content: string;
  targetLevel: 'elementary' | 'middle' | 'high' | 'college';
  style?: 'explanation' | 'story' | 'analogy' | 'example';
  maxLength?: number;
}

export interface SimplifiedContent {
  original: string;
  simplified: string;
  level: string;
  keyPoints: string[];
  analogies: string[];
  examples: string[];
  quiz: QuizQuestion[];
}

export interface QuizQuestion {
  question: string;
  options: string[];
  correctAnswer: number;
  explanation: string;
}

// ==================== 知识图谱提取 ====================

export interface KnowledgeGraphRequest {
  text: string;
  domain?: string;
  maxNodes?: number;
  maxRelations?: number;
}

export interface KnowledgeNode {
  id: string;
  label: string;
  type: 'concept' | 'term' | 'person' | 'event' | 'theory' | 'example';
  description?: string;
  importance: number; // 0-1
}

export interface KnowledgeRelation {
  id: string;
  source: string; // node id
  target: string; // node id
  type: 'is-a' | 'part-of' | 'related-to' | 'causes' | 'example-of' | 'prerequisite';
  label?: string;
  strength: number; // 0-1
}

export interface KnowledgeGraph {
  nodes: KnowledgeNode[];
  edges: KnowledgeRelation[];
  summary: string;
  rootConcepts: string[];
}

// ==================== API 函数 ====================

/**
 * 降阶法：将复杂内容简化为目标水平
 */
export async function simplifyContent(
  request: SimplificationRequest
): Promise<SimplifiedContent> {
  const response = await axios.post(`${API_BASE}/ai/simplify`, request);
  return response.data;
}

/**
 * 生成类比解释
 */
export async function generateAnalogy(
  concept: string,
  context: string
): Promise<{ analogy: string; explanation: string }> {
  const response = await axios.post(`${API_BASE}/ai/analogy`, {
    concept,
    context,
  });
  return response.data;
}

/**
 * 生成示例
 */
export async function generateExamples(
  concept: string,
  count: number = 3
): Promise<string[]> {
  const response = await axios.post(`${API_BASE}/ai/examples`, {
    concept,
    count,
  });
  return response.data.examples;
}

/**
 * 生成测验题目
 */
export async function generateQuiz(
  content: string,
  count: number = 5,
  difficulty: 'easy' | 'medium' | 'hard' = 'medium'
): Promise<QuizQuestion[]> {
  const response = await axios.post(`${API_BASE}/ai/quiz`, {
    content,
    count,
    difficulty,
  });
  return response.data.questions;
}

/**
 * 从文本提取知识图谱
 */
export async function extractKnowledgeGraph(
  request: KnowledgeGraphRequest
): Promise<KnowledgeGraph> {
  const response = await axios.post(`${API_BASE}/ai/extract-graph`, request);
  return response.data;
}

/**
 * 从课程/教材提取知识图谱
 */
export async function extractFromCourse(
  courseId: string
): Promise<KnowledgeGraph> {
  const response = await axios.get(`${API_BASE}/ai/course-graph/${courseId}`);
  return response.data;
}

/**
 * 查询节点相关信息
 */
export async function queryNodeInfo(nodeId: string): Promise<{
  node: KnowledgeNode;
  relatedNodes: KnowledgeNode[];
  resources: string[];
}> {
  const response = await axios.get(`${API_BASE}/ai/node/${nodeId}`);
  return response.data;
}

/**
 * 推荐学习路径
 */
export async function recommendLearningPath(
  currentNodeId: string,
  goalNodeId?: string
): Promise<{
  path: string[]; // node ids
  estimatedTime: number; // minutes
  prerequisites: string[];
}> {
  const response = await axios.post(`${API_BASE}/ai/learning-path`, {
    currentNodeId,
    goalNodeId,
  });
  return response.data;
}

/**
 * 评估理解程度
 */
export async function assessUnderstanding(
  conceptId: string,
  userExplanation: string
): Promise<{
  score: number; // 0-100
  gaps: string[];
  suggestions: string[];
  nextSteps: string[];
}> {
  const response = await axios.post(`${API_BASE}/ai/assess`, {
    conceptId,
    userExplanation,
  });
  return response.data;
}

// ==================== 导出 ====================

export default {
  simplifyContent,
  generateAnalogy,
  generateExamples,
  generateQuiz,
  extractKnowledgeGraph,
  extractFromCourse,
  queryNodeInfo,
  recommendLearningPath,
  assessUnderstanding,
};
