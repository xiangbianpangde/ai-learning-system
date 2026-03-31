#!/usr/bin/env python3
"""
AI 内容生成服务 v2
- 降阶法内容生成 (将复杂概念简化为易懂内容)
- 知识图谱提取
- 知识图谱增量更新
- 学习路径优化算法
- 真实 LLM API 集成 (百川/通义/DeepSeek)

新增功能:
- 多 LLM 提供商支持
- 知识图谱增量更新
- 学习路径优化
- 更好的错误处理与重试
"""

import os
import re
import json
import time
import uuid
import hashlib
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict, field
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 配置 - 支持多个 LLM 提供商
BAICHUAN_API_KEY = os.environ.get('BAICHUAN_API_KEY', '')
BAICHUAN_MODEL = os.environ.get('BAICHUAN_MODEL', 'Baichuan4')

ALIYUN_API_KEY = os.environ.get('ALIYUN_API_KEY', '')
ALIYUN_MODEL = os.environ.get('ALIYUN_MODEL', 'qwen-plus')

DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
DEEPSEEK_MODEL = os.environ.get('DEEPSEEK_MODEL', 'deepseek-chat')

# 默认使用百川，可配置
DEFAULT_PROVIDER = os.environ.get('LLM_PROVIDER', 'baichuan')

# 知识图谱缓存 (生产环境应使用 Redis)
graph_cache: Dict[str, Dict[str, Any]] = {}


@dataclass
class QuizQuestion:
    question: str
    options: List[str]
    correctAnswer: int
    explanation: str


@dataclass
class SimplifiedContent:
    original: str
    simplified: str
    level: str
    keyPoints: List[str]
    analogies: List[str]
    examples: List[str]
    quiz: List[QuizQuestion]


@dataclass
class KnowledgeNode:
    id: str
    label: str
    type: str  # concept, term, person, event, theory, example
    description: Optional[str]
    importance: float  # 0-1
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeRelation:
    id: str
    source: str  # node id
    target: str  # node id
    type: str  # is-a, part-of, related-to, causes, example-of, prerequisite
    label: Optional[str]
    strength: float  # 0-1


@dataclass
class KnowledgeGraph:
    nodes: List[KnowledgeNode]
    edges: List[KnowledgeRelation]
    summary: str
    rootConcepts: List[str]
    version: str = "1.0"
    updatedAt: str = field(default_factory=lambda: datetime.now().isoformat())
    nodeIdMap: Dict[str, str] = field(default_factory=dict)  # label -> id 映射


def call_llm_api(prompt: str, max_tokens: int = 2000, provider: str = None) -> str:
    """调用大语言模型 API (支持多提供商)"""
    provider = provider or DEFAULT_PROVIDER
    
    if provider == 'baichuan' and BAICHUAN_API_KEY:
        return call_baichuan(prompt, max_tokens)
    elif provider == 'aliyun' and ALIYUN_API_KEY:
        return call_aliyun(prompt, max_tokens)
    elif provider == 'deepseek' and DEEPSEEK_API_KEY:
        return call_deepseek(prompt, max_tokens)
    else:
        return generate_fallback_response(prompt)


def call_baichuan(prompt: str, max_tokens: int) -> str:
    """调用百川 API"""
    import requests
    
    url = "https://api.baichuan-ai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {BAICHUAN_API_KEY}",
    }
    payload = {
        "model": BAICHUAN_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }
    
    # 重试机制
    for attempt in range(3):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            if response.status_code == 200:
                data = response.json()
                return data['choices'][0]['message']['content']
            elif response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 5))
                time.sleep(retry_after)
            else:
                print(f"Baichuan API error: {response.text}")
        except Exception as e:
            if attempt == 2:
                print(f"Baichuan API failed after 3 attempts: {e}")
            time.sleep(2 ** attempt)
    
    return generate_fallback_response(prompt)


def call_aliyun(prompt: str, max_tokens: int) -> str:
    """调用阿里云通义千问 API"""
    import requests
    
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ALIYUN_API_KEY}",
    }
    payload = {
        "model": ALIYUN_MODEL,
        "input": {
            "messages": [
                {"role": "system", "content": "你是一个教育专家，擅长知识图谱提取和内容简化。"},
                {"role": "user", "content": prompt}
            ]
        },
        "parameters": {
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }
    }
    
    for attempt in range(3):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            if response.status_code == 200:
                data = response.json()
                return data['output']['text']
            elif response.status_code == 429:
                time.sleep(5)
            else:
                print(f"Aliyun API error: {response.text}")
        except Exception as e:
            if attempt == 2:
                print(f"Aliyun API failed: {e}")
            time.sleep(2 ** attempt)
    
    return generate_fallback_response(prompt)


def call_deepseek(prompt: str, max_tokens: int) -> str:
    """调用 DeepSeek API"""
    import requests
    
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    }
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }
    
    for attempt in range(3):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            if response.status_code == 200:
                data = response.json()
                return data['choices'][0]['message']['content']
            elif response.status_code == 429:
                time.sleep(5)
            else:
                print(f"DeepSeek API error: {response.text}")
        except Exception as e:
            if attempt == 2:
                print(f"DeepSeek API failed: {e}")
            time.sleep(2 ** attempt)
    
    return generate_fallback_response(prompt)


def generate_fallback_response(prompt: str) -> str:
    """回退方案：基于规则的简单生成"""
    if "简化" in prompt or "小学" in prompt or "初中" in prompt:
        return json.dumps({
            "simplified": "这是一个简化版本的内容。在实际应用中，这里会调用 AI 模型进行智能简化。",
            "keyPoints": ["核心概念 1", "核心概念 2", "核心概念 3"],
            "analogies": ["就像...一样"],
            "examples": ["例如：..."],
        }, ensure_ascii=False)
    
    if "图谱" in prompt or "节点" in prompt:
        return json.dumps({
            "nodes": [
                {"id": "1", "label": "核心概念", "type": "concept", "description": "基础概念", "importance": 1.0},
                {"id": "2", "label": "子概念 A", "type": "concept", "description": "分支概念", "importance": 0.8},
                {"id": "3", "label": "示例", "type": "example", "description": "具体例子", "importance": 0.6},
            ],
            "edges": [
                {"id": "e1", "source": "1", "target": "2", "type": "part-of", "label": "包含", "strength": 0.9},
                {"id": "e2", "source": "2", "target": "3", "type": "example-of", "label": "例如", "strength": 0.8},
            ],
            "summary": "这是一个示例知识图谱。",
            "rootConcepts": ["核心概念"],
        }, ensure_ascii=False)
    
    return json.dumps({"error": "无法处理该请求"}, ensure_ascii=False)


def generate_node_id(label: str, version: str = "v1") -> str:
    """生成节点 ID (基于内容哈希，支持去重)"""
    content = f"{label}:{version}"
    return hashlib.md5(content.encode()).hexdigest()[:12]


def simplify_content_llm(content: str, level: str, style: str) -> SimplifiedContent:
    """使用 LLM 进行降阶法内容生成"""
    
    level_descriptions = {
        'elementary': '小学水平，使用最简单的词汇和短句，避免专业术语',
        'middle': '初中水平，适当使用专业术语但要解释清楚',
        'high': '高中水平，可以使用较复杂的概念和推导',
        'college': '大学水平，深入讲解原理和数学推导',
    }
    
    style_instructions = {
        'explanation': '清晰解释每个概念，逻辑严谨',
        'story': '用故事的方式讲述，生动有趣',
        'analogy': '多用类比和比喻，帮助理解',
        'example': '通过具体例子说明，实践导向',
    }
    
    prompt = f"""
请将以下内容简化为{level_descriptions.get(level, '中等水平')}，采用{style_instructions.get(style, '解释说明')}的风格。

原始内容：
{content}

请以 JSON 格式返回，包含以下字段：
- simplified: 简化后的内容 (300-500 字)
- keyPoints: 关键要点列表 (3-5 个)
- analogies: 类比解释列表 (2-3 个)
- examples: 示例列表 (2-3 个)
- quiz: 测验题目列表 (3 题)，每题包含 question, options(4 个选项), correctAnswer(0-3), explanation

只返回 JSON，不要其他内容。
"""
    
    response_text = call_llm_api(prompt, max_tokens=3000)
    
    try:
        # 提取 JSON
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
        else:
            data = json.loads(response_text)
        
        return SimplifiedContent(
            original=content,
            simplified=data.get('simplified', ''),
            level=level,
            keyPoints=data.get('keyPoints', []),
            analogies=data.get('analogies', []),
            examples=data.get('examples', []),
            quiz=[QuizQuestion(**q) for q in data.get('quiz', [])],
        )
    except Exception as e:
        print(f"Parse error: {e}")
        return SimplifiedContent(
            original=content,
            simplified=f"简化版本：{content[:200]}...",
            level=level,
            keyPoints=["核心概念"],
            analogies=["就像日常生活一样"],
            examples=["例如：..."],
            quiz=[],
        )


def extract_knowledge_graph_llm(text: str, domain: str = '', max_nodes: int = 20) -> KnowledgeGraph:
    """使用 LLM 提取知识图谱"""
    
    domain_instruction = f"，领域：{domain}" if domain else ""
    
    prompt = f"""
请从以下文本中提取知识图谱{domain_instruction}。

文本内容：
{text[:3000]}

请识别关键概念、术语、人物、事件等，并建立它们之间的关系。

以 JSON 格式返回，包含：
- nodes: 节点列表，每个节点包含 id(自动生成), label, type(concept/term/person/event/theory/example), description, importance(0-1)
- edges: 关系列表，每个关系包含 id(自动生成), source(源节点 id), target(目标节点 id), type(is-a/part-of/related-to/causes/example-of/prerequisite), label, strength(0-1)
- summary: 图谱摘要 (100 字以内)
- rootConcepts: 核心概念列表 (3-5 个)

节点数控制在{max_nodes}个以内。只返回 JSON，不要其他内容。
"""
    
    response_text = call_llm_api(prompt, max_tokens=4000)
    
    try:
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
        else:
            data = json.loads(response_text)
        
        nodes = []
        node_id_map = {}
        
        for i, n in enumerate(data.get('nodes', [])):
            node_id = generate_node_id(n.get('label', f'node-{i}'))
            node_id_map[n.get('label', f'node-{i}')] = node_id
            nodes.append(KnowledgeNode(
                id=node_id,
                label=n.get('label', ''),
                type=n.get('type', 'concept'),
                description=n.get('description'),
                importance=n.get('importance', 0.5),
            ))
        
        edges = [
            KnowledgeRelation(
                id=f"e-{i}",
                source=node_id_map.get(e.get('source', ''), ''),
                target=node_id_map.get(e.get('target', ''), ''),
                type=e.get('type', 'related-to'),
                label=e.get('label'),
                strength=e.get('strength', 0.5),
            )
            for i, e in enumerate(data.get('edges', []))
        ]
        
        return KnowledgeGraph(
            nodes=nodes,
            edges=edges,
            summary=data.get('summary', ''),
            rootConcepts=data.get('rootConcepts', []),
            nodeIdMap=node_id_map,
        )
    except Exception as e:
        print(f"Parse error: {e}")
        return KnowledgeGraph(
            nodes=[
                KnowledgeNode("1", "核心概念", "concept", "基础概念", 1.0),
                KnowledgeNode("2", "子概念", "concept", "分支概念", 0.8),
            ],
            edges=[
                KnowledgeRelation("e1", "1", "2", "part-of", "包含", 0.9),
            ],
            summary="示例知识图谱",
            rootConcepts=["核心概念"],
        )


def update_knowledge_graph_incremental(
    existing_graph: KnowledgeGraph,
    new_text: str,
    domain: str = ''
) -> KnowledgeGraph:
    """增量更新知识图谱"""
    
    # 从新文本提取图谱
    new_graph = extract_knowledge_graph_llm(new_text, domain)
    
    # 合并节点 (去重)
    existing_labels = {node.label: node.id for node in existing_graph.nodes}
    merged_nodes = list(existing_graph.nodes)
    merged_edges = list(existing_graph.edges)
    
    for node in new_graph.nodes:
        if node.label not in existing_labels:
            merged_nodes.append(node)
            existing_labels[node.label] = node.id
    
    # 添加新关系 (去重)
    existing_edges_set = {(e.source, e.target, e.type) for e in merged_edges}
    for edge in new_graph.edges:
        if (edge.source, edge.target, edge.type) not in existing_edges_set:
            merged_edges.append(edge)
    
    # 更新版本
    return KnowledgeGraph(
        nodes=merged_nodes,
        edges=merged_edges,
        summary=f"{existing_graph.summary} + 新增内容",
        rootConcepts=list(set(existing_graph.rootConcepts + new_graph.rootConcepts)),
        version=f"{existing_graph.version}.1",
        updatedAt=datetime.now().isoformat(),
        nodeIdMap={**existing_graph.nodeIdMap, **new_graph.nodeIdMap},
    )


def optimize_learning_path(
    graph: KnowledgeGraph,
    start_node: str,
    goal_node: str
) -> List[str]:
    """优化学习路径 (基于图的 BFS/DFS)"""
    
    # 构建邻接表
    adjacency: Dict[str, List[str]] = {}
    for edge in graph.edges:
        if edge.source not in adjacency:
            adjacency[edge.source] = []
        adjacency[edge.source].append(edge.target)
    
    # BFS 找最短路径
    from collections import deque
    
    queue = deque([(start_node, [start_node])])
    visited = {start_node}
    
    while queue:
        current, path = queue.popleft()
        
        if current == goal_node:
            return path
        
        for neighbor in adjacency.get(current, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    
    # 如果没有路径，返回直接连接
    return [start_node, goal_node]


@app.route('/api/ai/simplify', methods=['POST'])
def simplify_content():
    """降阶法内容生成"""
    data = request.json
    
    content = data.get('content', '')
    target_level = data.get('targetLevel', 'middle')
    style = data.get('style', 'explanation')
    
    if not content:
        return jsonify({'error': '内容为空'}), 400
    
    result = simplify_content_llm(content, target_level, style)
    
    return jsonify(asdict(result))


@app.route('/api/ai/extract-graph', methods=['POST'])
def extract_graph():
    """提取知识图谱"""
    data = request.json
    
    text = data.get('text', '')
    domain = data.get('domain', '')
    max_nodes = data.get('maxNodes', 20)
    
    if not text:
        return jsonify({'error': '文本为空'}), 400
    
    # 生成缓存键
    cache_key = hashlib.md5(f"{text}:{domain}".encode()).hexdigest()
    
    # 检查缓存
    if cache_key in graph_cache:
        cached = graph_cache[cache_key]
        return jsonify(asdict(KnowledgeGraph(**cached)))
    
    result = extract_knowledge_graph_llm(text, domain, max_nodes)
    
    # 缓存结果
    graph_cache[cache_key] = asdict(result)
    
    return jsonify(asdict(result))


@app.route('/api/ai/update-graph', methods=['POST'])
def update_graph():
    """增量更新知识图谱"""
    data = request.json
    
    existing_graph_data = data.get('existingGraph', {})
    new_text = data.get('newText', '')
    domain = data.get('domain', '')
    
    if not new_text:
        return jsonify({'error': '新文本为空'}), 400
    
    # 转换现有图谱
    existing_graph = KnowledgeGraph(
        nodes=[KnowledgeNode(**n) for n in existing_graph_data.get('nodes', [])],
        edges=[KnowledgeRelation(**e) for e in existing_graph_data.get('edges', [])],
        summary=existing_graph_data.get('summary', ''),
        rootConcepts=existing_graph_data.get('rootConcepts', []),
        version=existing_graph_data.get('version', '1.0'),
        nodeIdMap=existing_graph_data.get('nodeIdMap', {}),
    )
    
    # 增量更新
    updated_graph = update_knowledge_graph_incremental(existing_graph, new_text, domain)
    
    # 更新缓存
    cache_key = hashlib.md5(f"{new_text}:{domain}".encode()).hexdigest()
    graph_cache[cache_key] = asdict(updated_graph)
    
    return jsonify(asdict(updated_graph))


@app.route('/api/ai/learning-path', methods=['POST'])
def recommend_path():
    """推荐学习路径 (优化版)"""
    data = request.json
    graph_id = data.get('graphId', '')
    current_node = data.get('currentNodeId', '')
    goal_node = data.get('goalNodeId', '')
    
    # 从缓存获取图谱
    graph_data = graph_cache.get(graph_id)
    
    if graph_data:
        graph = KnowledgeGraph(**graph_data)
        path = optimize_learning_path(graph, current_node, goal_node)
        
        # 估算时间 (每个节点约 10 分钟)
        estimated_time = len(path) * 10
        
        # 获取前置节点
        prerequisites = []
        for edge in graph.edges:
            if edge.target == goal_node and edge.type == 'prerequisite':
                prerequisites.append(edge.source)
        
        return jsonify({
            'path': path,
            'estimatedTime': estimated_time,
            'prerequisites': prerequisites,
            'totalNodes': len(graph.nodes),
        })
    
    # 回退
    return jsonify({
        'path': [current_node, goal_node] if goal_node else [current_node],
        'estimatedTime': 30,
        'prerequisites': [],
    })


@app.route('/api/ai/assess', methods=['POST'])
def assess_understanding():
    """评估理解程度"""
    data = request.json
    concept_id = data.get('conceptId', '')
    user_explanation = data.get('userExplanation', '')
    
    # 简单评估：基于长度和关键词
    score = min(100, len(user_explanation) * 2)
    
    # 检查关键词
    keywords = ['因为', '所以', '例如', '如果', '那么']
    keyword_count = sum(1 for kw in keywords if kw in user_explanation)
    score = min(100, score + keyword_count * 5)
    
    gaps = []
    if len(user_explanation) < 50:
        gaps.append('解释太短，需要更多细节')
    if keyword_count < 2:
        gaps.append('缺少逻辑连接词')
    
    return jsonify({
        'score': score,
        'gaps': gaps,
        'suggestions': ['尝试举例说明', '使用类比帮助理解'],
        'nextSteps': ['继续学习相关概念'],
    })


@app.route('/api/ai/analogy', methods=['POST'])
def generate_analogy():
    """生成类比解释"""
    data = request.json
    concept = data.get('concept', '')
    context = data.get('context', '')
    
    prompt = f"""
请为以下概念生成一个生动的类比解释：
概念：{concept}
上下文：{context}

以 JSON 格式返回：
{{"analogy": "类比内容", "explanation": "解释说明"}}
"""
    
    response_text = call_llm_api(prompt)
    
    try:
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        data = json.loads(json_match.group() if json_match else response_text)
        return jsonify(data)
    except:
        return jsonify({
            'analogy': f"{concept}就像...",
            'explanation': '这个类比帮助理解...'
        })


@app.route('/api/ai/examples', methods=['POST'])
def generate_examples():
    """生成示例"""
    data = request.json
    concept = data.get('concept', '')
    count = data.get('count', 3)
    
    prompt = f"""
请为以下概念生成{count}个具体示例：
概念：{concept}

以 JSON 格式返回：
{{"examples": ["示例 1", "示例 2", "示例 3"]}}
"""
    
    response_text = call_llm_api(prompt)
    
    try:
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        data = json.loads(json_match.group() if json_match else response_text)
        return jsonify(data)
    except:
        return jsonify({'examples': [f"示例{i+1}" for i in range(count)]})


@app.route('/api/ai/quiz', methods=['POST'])
def generate_quiz():
    """生成测验题目"""
    data = request.json
    content = data.get('content', '')
    count = data.get('count', 5)
    difficulty = data.get('difficulty', 'medium')
    
    prompt = f"""
请根据以下内容生成{count}道{difficulty}难度的测验题：
{content[:2000]}

以 JSON 格式返回：
{{"questions": [
  {{"question": "题目", "options": ["A", "B", "C", "D"], "correctAnswer": 0, "explanation": "解析"}}
]}}
"""
    
    response_text = call_llm_api(prompt, max_tokens=3000)
    
    try:
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        data = json.loads(json_match.group() if json_match else response_text)
        return jsonify(data)
    except:
        return jsonify({'questions': []})


if __name__ == '__main__':
    print("🤖 AI 内容生成服务 v2 启动中...")
    print(f"LLM 提供商：{DEFAULT_PROVIDER}")
    print("✨ 新功能：多 LLM 支持 | 增量更新 | 学习路径优化")
    app.run(host='0.0.0.0', port=5002, debug=True)
