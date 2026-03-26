# Phase 1 自动化增强服务文档

## 概述

Phase 1 实现了两个核心功能：
1. **网页资源抓取** - 自动聚合 B 站/YouTube/技术博客教学资源
2. **扫描版 OCR** - 支持图片型 PDF 解析

---

## 服务架构

```
edict/backend/app/services/
├── web_scraper.py      # 网页抓取服务
├── ocr_parser.py       # OCR 解析服务
└── resource_ranker.py  # 资源质量评分
```

---

## 1. 网页抓取服务 (web_scraper.py)

### 功能特性

- ✅ B 站搜索 API 集成
- ✅ YouTube Data API 集成
- ✅ 通用网页内容提取 (trafilatura + readability-lxml)
- ✅ 资源去重和质量评分

### 安装依赖

```bash
pip install trafilatura readability-lxml beautifulsoup4 lxml httpx
```

### API 文档

#### WebScraperService

主服务类，提供统一的资源搜索接口。

```python
from edict.backend.app.services.web_scraper import WebScraperService

service = WebScraperService()

# 搜索资源
resources = await service.search(
    keyword="Python 教程",
    sources=["bilibili", "youtube", "web"]  # 可选：bilibili/youtube/web
)

# 从 URL 提取资源
resource = await service.extract_from_url("https://example.com/article")

# 关闭服务
await service.close()
```

#### Resource 数据结构

```python
@dataclass
class Resource:
    title: str                    # 资源标题
    url: str                      # 资源 URL
    resource_type: ResourceType   # 资源类型
    duration: Optional[int]       # 时长（秒）
    description: str              # 描述
    author: str                   # 作者
    publish_date: Optional[datetime]  # 发布日期
    quality_score: float          # 质量评分 (0-1)
    tags: List[str]               # 标签
    metadata: Dict[str, Any]      # 元数据
```

#### ResourceType 枚举

```python
class ResourceType(Enum):
    VIDEO_BILIBILI = "bilibili_video"
    VIDEO_YOUTUBE = "youtube_video"
    ARTICLE = "article"
    BLOG = "blog"
    DOCUMENTATION = "documentation"
    OTHER = "other"
```

### 配置说明

#### YouTube API Key

通过环境变量配置：

```bash
export YOUTUBE_API_KEY=your_api_key_here
```

获取 API Key: https://console.cloud.google.com/apis/credentials

#### B 站 API

使用非官方 API，可能需要 Cookie（可选）：

```python
api = BilibiliSearchAPI()
api.session.headers["Cookie"] = "your_cookie_here"
```

### 使用示例

#### 示例 1: 搜索教学资源

```python
import asyncio
from edict.backend.app.services.web_scraper import search_resources_sync

# 同步调用
resources = search_resources_sync("Python 入门", sources=["bilibili"])

for res in resources:
    print(f"{res.title} - {res.url}")
    print(f"  时长：{res.duration}秒")
    print(f"  质量评分：{res.quality_score}")
```

#### 示例 2: 异步调用

```python
import asyncio
from edict.backend.app.services.web_scraper import WebScraperService

async def main():
    service = WebScraperService()
    
    try:
        resources = await service.search("机器学习教程")
        
        # 打印前 5 个资源
        for res in resources[:5]:
            print(f"[{res.resource_type.value}] {res.title}")
            print(f"  URL: {res.url}")
            print(f"  作者：{res.author}")
            print()
    finally:
        await service.close()

asyncio.run(main())
```

#### 示例 3: 提取网页内容

```python
from edict.backend.app.services.web_scraper import extract_webpage_sync

resource = extract_webpage_sync("https://docs.python.org/3/tutorial/")

if resource:
    print(f"标题：{resource.title}")
    print(f"描述：{resource.description[:200]}")
    print(f"阅读时间：{resource.duration}秒")
```

---

## 2. OCR 解析服务 (ocr_parser.py)

### 功能特性

- ✅ 中文 OCR 识别
- ✅ 英文 OCR 识别
- ✅ 混合排版支持
- ✅ 表格结构识别

### 安装依赖

```bash
pip install paddlepaddle paddleocr opencv-python Pillow PyMuPDF
```

**注意**: PaddlePaddle 安装可能需要根据系统选择合适版本：
- CPU 版本：`pip install paddlepaddle`
- GPU 版本：`pip install paddlepaddle-gpu`

### API 文档

#### OCRParserService

主服务类，提供图片和 PDF 的 OCR 识别。

```python
from edict.backend.app.services.ocr_parser import OCRParserService

service = OCRParserService(use_gpu=False)  # 可选：使用 GPU

# 识别图片
result = service.parse_image("/path/to/image.png")

# 识别 PDF（扫描版）
results = service.parse_pdf("/path/to/scanned.pdf")

# 获取 Markdown 格式
markdown = result.markdown
```

#### OCRResult 数据结构

```python
@dataclass
class OCRResult:
    success: bool                    # 是否成功
    text_blocks: List[TextBlock]     # 文字块列表
    table_blocks: List[TableBlock]   # 表格块列表
    full_text: str                   # 完整文本
    markdown: str                    # Markdown 格式
    page: int                        # 页码
    error: Optional[str]             # 错误信息
    metadata: Dict[str, Any]         # 元数据
```

#### TextBlock 数据结构

```python
@dataclass
class TextBlock:
    text: str                        # 识别的文字
    confidence: float                # 置信度 (0-1)
    bbox: Tuple[int, int, int, int]  # 边界框 (x1, y1, x2, y2)
    language: str                    # 语言 (zh/en/mixed)
    direction: TextDirection         # 文字方向
    block_type: str                  # 块类型 (text/table/etc.)
```

### 使用示例

#### 示例 1: 识别图片

```python
from edict.backend.app.services.ocr_parser import parse_image_ocr

result = parse_image_ocr("test_image.png")

if result.success:
    print(f"识别成功，共 {len(result.text_blocks)} 个文字块")
    print(f"完整文本：{result.full_text}")
    print(f"Markdown:\n{result.markdown}")
else:
    print(f"识别失败：{result.error}")
```

#### 示例 2: 识别扫描版 PDF

```python
from edict.backend.app.services.ocr_parser import parse_pdf_ocr

results = parse_pdf_ocr("scanned_document.pdf")

for page_result in results:
    if page_result.success:
        print(f"=== 第{page_result.page}页 ===")
        print(page_result.markdown)
```

#### 示例 3: 转换为 Markdown

```python
from edict.backend.app.services.ocr_parser import image_to_markdown, pdf_to_markdown

# 图片转 Markdown
markdown = image_to_markdown("notes.png")
print(markdown)

# PDF 转 Markdown
markdown = pdf_to_markdown("textbook.pdf", pages=[1, 2, 3])  # 指定页码
print(markdown)
```

#### 示例 4: 处理混合语言

```python
service = OCRParserService()
result = service.parse_image("mixed_lang.png")

for block in result.text_blocks:
    print(f"[{block.language}] {block.text} (置信度：{block.confidence:.2f})")
```

---

## 3. 资源质量评分服务 (resource_ranker.py)

### 功能特性

- ✅ 多维度质量评分
- ✅ 资源去重
- ✅ 智能排序
- ✅ 个性化推荐

### API 文档

#### ResourceRankerService

主服务类，提供资源评分和排序。

```python
from edict.backend.app.services.resource_ranker import ResourceRankerService

service = ResourceRankerService()

# 评分排序
ranked = service.rank_resources(resources, top_n=10)

# 个性化推荐
recommendations = service.get_recommendations(
    resources,
    preferences={"prefer_fresh": True},
    top_n=10
)
```

#### 质量评估维度

1. **内容质量** (35%) - 标题、描述、元数据质量
2. **权威性** (25%) - 域名权威性、作者可信度
3. **时效性** (15%) - 发布时间新鲜度
4. **参与度** (15%) - 播放量、点赞、评论
5. **完整性** (10%) - 时长、系列内容、配套资源

#### QualityMetrics 数据结构

```python
@dataclass
class QualityMetrics:
    content_quality: float    # 内容质量 (0-1)
    authority: float          # 权威性 (0-1)
    freshness: float          # 时效性 (0-1)
    engagement: float         # 参与度 (0-1)
    completeness: float       # 完整性 (0-1)
    
    def weighted_score(self, weights=None) -> float:
        """计算加权总分"""
```

#### ResourceQualityTier 枚举

```python
class ResourceQualityTier(Enum):
    EXCELLENT = "excellent"  # 90-100 分
    GOOD = "good"            # 70-89 分
    FAIR = "fair"            # 50-69 分
    POOR = "poor"            # < 50 分
```

### 使用示例

#### 示例 1: 基础评分排序

```python
from edict.backend.app.services.resource_ranker import rank_resources

resources = [
    {
        "title": "Python 教程",
        "url": "https://bilibili.com/video/python",
        "type": "bilibili_video",
        "description": "详细内容" * 100,
        "metadata": {"play_count": 500000}
    },
    # ... 更多资源
]

ranked = rank_resources(resources, top_n=5)

for res in ranked:
    print(f"[{res.quality_tier.value}] {res.title}")
    print(f"  评分：{res.quality_score:.2f}")
    print(f"  各项指标：{res.metrics.to_dict()}")
```

#### 示例 2: 个性化推荐

```python
from edict.backend.app.services.resource_ranker import get_recommendations

# 偏好设置
preferences = {
    "prefer_fresh": True,        # 偏好新资源
    "prefer_authoritative": False,  # 不特别要求权威
    "prefer_complete": True      # 偏好完整内容
}

recommendations = get_recommendations(resources, preferences, top_n=10)
```

#### 示例 3: 自定义权重

```python
from edict.backend.app.services.resource_ranker import ResourceRankerService

service = ResourceRankerService()

# 自定义权重（强调时效性）
weights = {
    "content_quality": 0.2,
    "authority": 0.15,
    "freshness": 0.4,      # 时效性权重提高
    "engagement": 0.15,
    "completeness": 0.1
}

ranked = service.rank_resources(resources, weights=weights)
```

---

## 集成使用示例

### 完整工作流：搜索并排序教学资源

```python
import asyncio
from edict.backend.app.services.web_scraper import WebScraperService
from edict.backend.app.services.resource_ranker import ResourceRankerService

async def search_and_rank(keyword: str):
    """搜索资源并排序。"""
    scraper = WebScraperService()
    ranker = ResourceRankerService()
    
    try:
        # 1. 搜索资源
        resources = await scraper.search(keyword, sources=["bilibili", "youtube"])
        
        # 2. 转换为字典格式
        resource_dicts = [r.to_dict() for r in resources]
        
        # 3. 评分排序
        ranked = ranker.rank_resources(resource_dicts, top_n=10)
        
        # 4. 输出结果
        print(f"找到 {len(ranked)} 个优质资源：\n")
        for i, res in enumerate(ranked, 1):
            print(f"{i}. [{res.quality_tier.value}] {res.title}")
            print(f"   URL: {res.url}")
            print(f"   评分：{res.quality_score:.2f}")
            print(f"   时长：{res.duration}秒" if res.duration else "")
            print()
        
        return ranked
        
    finally:
        await scraper.close()

# 运行
results = asyncio.run(search_and_rank("Python 数据分析"))
```

### 完整工作流：OCR 解析并提取知识点

```python
from edict.backend.app.services.ocr_parser import OCRParserService
from edict.backend.app.services.pdf_parser import PDFParserService

def parse_and_extract(pdf_path: str):
    """解析扫描版 PDF 并提取知识点。"""
    ocr_service = OCRParserService()
    
    # 1. OCR 识别
    results = ocr_service.parse_pdf(pdf_path)
    
    # 2. 合并所有页面文本
    full_text = "\n\n".join(r.full_text for r in results if r.success)
    
    # 3. 使用 PDF 解析器提取知识点
    pdf_service = PDFParserService()
    # ... 进一步处理
    
    return full_text

# 运行
text = parse_and_extract("scanned_textbook.pdf")
print(text[:500])  # 预览前 500 字
```

---

## 测试

### 运行测试

```bash
cd /root/edict
pytest tests/test_web_scraper.py -v
pytest tests/test_ocr_parser.py -v
pytest tests/test_resource_ranker.py -v
```

### 测试覆盖率

```bash
pytest tests/ --cov=edict.backend.app.services --cov-report=html
```

---

## 常见问题

### Q: YouTube API 返回 403 错误

A: 检查 API Key 是否有效，确保已启用 YouTube Data API v3。

### Q: PaddleOCR 识别速度慢

A: 
1. 使用 GPU 加速：`OCRParserService(use_gpu=True)`
2. 降低图片分辨率
3. 只识别指定页面

### Q: 网页提取乱码

A: 检查网页编码，trafilatura 通常能自动检测，但某些网站可能需要手动指定。

### Q: 表格识别不准确

A: 表格识别是预留功能，当前使用备用方案。建议：
1. 确保表格区域清晰
2. 表格线明显
3. 未来会集成专门的表格识别模型

---

## 更新日志

### v1.0.0 (2026-03-26)
- ✅ 初始版本
- ✅ 网页抓取服务（B 站/YouTube/通用网页）
- ✅ OCR 解析服务（PaddleOCR）
- ✅ 资源质量评分服务
- ✅ 完整测试覆盖
- ✅ API 文档

---

## 贡献指南

1. 遵循 PEP8 代码风格
2. 所有函数必须有 docstring
3. 关键功能必须有单元测试
4. 使用 Conventional Commits 提交

---

## 许可证

与主项目保持一致。
