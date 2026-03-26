# 48 小时 AI 私人导师系统

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

> 🎯 **快速系统掌握一个科目** - 基于 AI 的个性化学习系统，融合费曼技巧、知识图谱、渐进式教学法

---

## 📖 项目简介

本系统是一个 AI 驱动的学习辅助平台，帮助学习者在 48 小时内快速掌握一个新科目的核心知识。系统基于 edict 框架开发，包含以下核心功能：

- 📄 **PDF 智能解析** - 支持公式、表格、图表的深度学习材料解析
- 🧠 **知识图谱构建** - 自动生成知识点关联网络
- 📋 **个性化学习计划** - 基于学习目标和时间约束生成学习路径
- 🎓 **费曼检测** - 通过教学式对话检测理解程度
- 📊 **学习预测** - 预测学习进度和掌握程度
- 📉 **降阶法教学** - 根据理解水平动态调整讲解难度
- 🔍 **LaTeX OCR** - 数学公式识别与渲染

---

## 🚀 快速开始

### 前置条件

本系统作为 edict 框架的扩展模块运行，需要先部署 edict 框架：

```bash
# 1. 克隆 edict 框架
git clone https://github.com/xiangbianpangde/edict.git
cd edict

# 2. 安装依赖
pip install -r edict/backend/requirements.txt

# 3. 复制本系统代码
cp -r /path/to/ai-learning-system/src/* edict/backend/app/services/
cp -r /path/to/ai-learning-system/components/* edict/frontend/src/components/
```

### 配置

编辑 `edict/backend/.env` 添加必要配置：

```bash
# 学习系统配置
LEARNING_MODEL=qwen3.5-plus
OCR_ENGINE=paddleocr
CACHE_TTL=3600
```

### 运行测试

```bash
cd edict
pytest tests/test_pdf_parser.py
pytest tests/test_knowledge_graph.py
pytest tests/integration/test_full_pipeline.py
```

---

## 🏗 架构说明

```
┌─────────────────────────────────────────────────────────┐
│                    前端 (React/TypeScript)               │
│  ┌──────────────────┐  ┌────────────────────────────┐   │
│  │ FormulaRenderer  │  │ KnowledgeGraph Visualization│   │
│  └──────────────────┘  └────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│              后端服务 (FastAPI/Python)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ PDF Parser   │  │ Knowledge    │  │ Learning     │   │
│  │              │  │ Graph        │  │ Plan         │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Feynman      │  │ Learning     │  │ Progressive  │   │
│  │ Assessment   │  │ Prediction   │  │ Teaching     │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│  ┌──────────────┐  ┌──────────────┐                     │
│  │ LaTeX OCR    │  │ Cache        │                     │
│  │              │  │ Manager      │                     │
│  └──────────────┘  └──────────────┘                     │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                  数据存储 (PostgreSQL/Redis)             │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 测试报告摘要

### 性能测试结果

| 测试项 | 指标 | 结果 |
|--------|------|------|
| PDF 解析速度 | 10 页文档 | < 5 秒 |
| 知识图谱构建 | 100 个知识点 | < 3 秒 |
| 费曼检测响应 | 单次对话 | < 2 秒 |
| 学习预测准确率 | 测试集 | 85%+ |

### 用户测试反馈

- ✅ 90% 用户认为系统有效帮助理解复杂概念
- ✅ 85% 用户表示学习计划合理可行
- ✅ 降阶法教学法显著提升理解深度

详细报告见 [`docs/user_test_report.md`](docs/user_test_report.md)

---

## 📝 核心功能详解

### 1. PDF 智能解析
- 支持文字、公式、表格、图表混合解析
- 自动识别 LaTeX 公式并渲染
- 优化版支持大文件流式处理

### 2. 知识图谱
- 自动提取知识点及关联关系
- 可视化展示知识结构
- 支持动态更新和扩展

### 3. 费曼检测
- 通过对话检测理解程度
- 识别知识盲点
- 生成针对性改进建议

### 4. 降阶法教学
- 5 级难度自适应调整
- 从通俗到专业渐进讲解
- 基于理解水平动态切换

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 👤 作者

- GitHub: [@xiangbianpangde](https://github.com/xiangbianpangde)

---

## 🙏 致谢

本项目基于 [edict 框架](https://github.com/xiangbianpangde/edict) 开发，感谢框架提供的强大基础设施。
