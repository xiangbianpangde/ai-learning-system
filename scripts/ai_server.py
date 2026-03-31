#!/usr/bin/env python3
"""
AI 内容生成服务
- 降阶法内容生成 (将复杂概念简化为易懂内容)
- 知识图谱提取
"""

import os
import re
import json
import time
import uuid
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 配置
BAICHUAN_API_KEY = os.environ.get('BAICHUAN_API_KEY', '')
BAICHUAN_MODEL = os.environ.get('BAICHUAN_MODEL', 'Baichuan4')


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


def call_llm_api(prompt: str, max_tokens: int = 2000) -> str:
    """调用大语言模型 API"""
    import requests
    
    if BAICHUAN_API_KEY:
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
        
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        if response.status_code == 200:
            data = response.json()
            return data['choices'][0]['message']['content']
        else:
            print(f"API error: {response.text}")
    
    # Fallback: 简单规则生成 (演示用)
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


def simplify_content_llm(content: str, level: str, style: str) -> SimplifiedContent:
    """使用 LLM 进行降阶法内容生成"""
    
    level_descriptions = {
        'elementary': '小学水平，使用最简单的词汇和短句',
        'middle': '初中水平，适当使用专业术语但要解释',
        'high': '高中水平，可以使用较复杂的概念',
        'college': '大学水平，深入讲解原理和推导',
    }
    
    style_instructions = {
        'explanation': '清晰解释每个概念',
        'story': '用故事的方式讲述',
        'analogy': '多用类比和比喻',
        'example': '通过具体例子说明',
    }
    
    prompt = f"""
请将以下内容简化为{level_descriptions.get(level, '中等水平')}，采用{style_instructions.get(style, '解释说明')}的风格。

原始内容：
{content}

请以 JSON 格式返回，包含以下字段：
- simplified: 简化后的内容
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
        # 返回简化版本
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
{text[:3000]}  # 限制长度

请识别关键概念、术语、人物、事件等，并建立它们之间的关系。

以 JSON 格式返回，包含：
- nodes: 节点列表，每个节点包含 id, label, type(concept/term/person/event/theory/example), description, importance(0-1)
- edges: 关系列表，每个关系包含 id, source(源节点 id), target(目标节点 id), type(is-a/part-of/related-to/causes/example-of/prerequisite), label, strength(0-1)
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
        
        nodes = [
            KnowledgeNode(
                id=n.get('id', str(i)),
                label=n.get('label', ''),
                type=n.get('type', 'concept'),
                description=n.get('description'),
                importance=n.get('importance', 0.5),
            )
            for i, n in enumerate(data.get('nodes', []))
        ]
        
        edges = [
            KnowledgeRelation(
                id=e.get('id', str(i)),
                source=e.get('source', ''),
                target=e.get('target', ''),
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
        )
    except Exception as e:
        print(f"Parse error: {e}")
        # 返回示例图谱
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


@app.route('/api/ai/extract-graph', methods=['POST'])
def extract_graph():
    """提取知识图谱"""
    data = request.json
    
    text = data.get('text', '')
    domain = data.get('domain', '')
    max_nodes = data.get('maxNodes', 20)
    max_relations = data.get('maxRelations', 30)
    
    if not text:
        return jsonify({'error': '文本为空'}), 400
    
    result = extract_knowledge_graph_llm(text, domain, max_nodes)
    
    return jsonify(asdict(result))


@app.route('/api/ai/course-graph/<course_id>', methods=['GET'])
def extract_from_course(course_id: str):
    """从课程提取知识图谱"""
    # TODO: 从数据库获取课程内容
    return jsonify({
        'nodes': [],
        'edges': [],
        'summary': '课程知识图谱',
        'rootConcepts': [],
    })


@app.route('/api/ai/node/<node_id>', methods=['GET'])
def query_node(node_id: str):
    """查询节点信息"""
    return jsonify({
        'node': {'id': node_id, 'label': '概念', 'type': 'concept'},
        'relatedNodes': [],
        'resources': [],
    })


@app.route('/api/ai/learning-path', methods=['POST'])
def recommend_path():
    """推荐学习路径"""
    data = request.json
    current_node = data.get('currentNodeId', '')
    goal_node = data.get('goalNodeId', '')
    
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
    explanation = data.get('userExplanation', '')
    
    # 简单评估：基于长度和关键词
    score = min(100, len(explanation) * 2)
    
    return jsonify({
        'score': score,
        'gaps': ['需要更多细节'],
        'suggestions': ['尝试举例说明'],
        'nextSteps': ['继续学习相关概念'],
    })


if __name__ == '__main__':
    print("🤖 AI 内容生成服务启动中...")
    app.run(host='0.0.0.0', port=5002, debug=True)
