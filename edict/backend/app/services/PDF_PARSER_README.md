# PDF 解析服务使用文档

## 概述

PDF 解析服务支持 5 类 PDF 文档的智能解析：

1. **纯文本 PDF** - 直接提取文本（使用 pypdf）
2. **扫描版 PDF** - OCR 识别（使用 PaddleOCR）
3. **表格 PDF** - 表格结构提取（使用启发式方法）
4. **公式 PDF** - LaTeX 公式识别（使用 pix2tex）
5. **混合 PDF** - 智能切换解析器

## 快速开始

### 基本用法

```python
from edict.backend.app.services.pdf_parser import (
    PDFParserService,
    parse_pdf,
    extract_knowledge_points,
    extract_latex_formulas,
)

# 方法 1：使用服务类
service = PDFParserService()
result = service.parse("document.pdf")

# 方法 2：使用便捷函数
result = parse_pdf("document.pdf")

# 提取知识点
points = extract_knowledge_points("document.pdf")

# 提取 LaTeX 公式
formulas = extract_latex_formulas("math_book.pdf")
```

### 解析结果

```python
from edict.backend.app.services.pdf_parser import PDFType

result = parse_pdf("document.pdf")

print(f"成功：{result.success}")
print(f"类型：{result.pdf_type}")  # PDFType.TEXT/SCANNED/TABLE/FORMULA/MIXED
print(f"页数：{result.pages}")
print(f"文本长度：{len(result.text)}")
print(f"知识点数量：{len(result.knowledge_points)}")
print(f"公式数量：{len(result.latex_formulas)}")

# 访问知识点
for kp in result.knowledge_points:
    print(f"标题：{kp.title}")
    print(f"内容：{kp.content[:100]}...")
    print(f"页码：{kp.page}")
    print(f"置信度：{kp.confidence}")
    print(f"标签：{kp.tags}")
    print(f"公式：{kp.latex_formulas}")
```

## 支持的 PDF 类型

### 1. 纯文本 PDF

**特点**：
- 可直接提取文本
- 无需 OCR
- 解析速度快

**示例**：
```python
result = parse_pdf("technical_doc.pdf")
# 自动检测为 PDFType.TEXT
```

**预期性能**：
- 文本提取准确率 ≥ 95%
- 解析时间 < 2 秒

### 2. 扫描版 PDF

**特点**：
- 需要 OCR 识别
- 支持中英文混合
- 使用 PaddleOCR

**示例**：
```python
# 使用 GPU 加速（如有）
service = PDFParserService(use_gpu=True)
result = service.parse("scanned_book.pdf", pdf_type=PDFType.SCANNED)

# 或使用便捷函数
result = parse_pdf("scanned_book.pdf", use_gpu=False)
```

**预期性能**：
- OCR 识别准确率 ≥ 80%
- 解析时间 < 10 秒/页
- 中文识别准确率 ≥ 85%

### 3. 表格 PDF

**特点**：
- 自动检测表格结构
- 输出 Markdown 格式
- 支持多表格

**示例**：
```python
result = parse_pdf("financial_report.pdf", pdf_type=PDFType.TABLE)

# 访问表格
for kp in result.knowledge_points:
    if "表格" in kp.title:
        print(kp.content)  # Markdown 表格
```

**预期性能**：
- 表格检测准确率 ≥ 80%
- 结构还原准确率 ≥ 75%

### 4. 公式 PDF

**特点**：
- 提取 LaTeX 公式
- 支持行内和块级公式
- 使用 pix2tex 识别

**示例**：
```python
# 提取公式
formulas = extract_latex_formulas("math_textbook.pdf")

for formula in formulas:
    print(f"页码：{formula['page']}")
    print(f"类型：{formula['type']}")  # inline/block
    print(f"LaTeX: {formula['latex']}")
```

**预期性能**：
- 公式识别准确率 ≥ 75%
- 支持印刷体和手写体

### 5. 混合 PDF

**特点**：
- 智能切换解析器
- 自动检测内容类型
- 综合处理

**示例**：
```python
# 自动检测和处理
result = parse_pdf("textbook.pdf")
# 解析器会根据内容自动选择 TEXT/SCANNED/MIXED
```

## 高级用法

### 批量解析

```python
from pathlib import Path

service = PDFParserService()
pdf_files = [Path("doc1.pdf"), Path("doc2.pdf"), Path("doc3.pdf")]

results = service.parse_batch(pdf_files)

for result in results:
    print(f"{result.pdf_type}: {len(result.knowledge_points)} 知识点")
```

### 指定 PDF 类型

```python
# 如果已知 PDF 类型，可指定以跳过检测
result = parse_pdf("document.pdf", pdf_type=PDFType.TEXT)
```

### GPU 加速

```python
# 使用 GPU 加速 OCR
service = PDFParserService(use_gpu=True)
result = service.parse("scanned.pdf", pdf_type=PDFType.SCANNED)
```

### 自定义知识点提取

```python
from edict.backend.app.services.pdf_parser import TextPDFParser

parser = TextPDFParser()
points = parser._extract_knowledge_points(text, page=1)

# 自定义提取逻辑
# 修改 _extract_knowledge_points 方法
```

## 数据结构

### ParseResult

```python
@dataclass
class ParseResult:
    success: bool              # 是否成功
    pdf_type: PDFType          # PDF 类型
    text: str                  # 完整文本
    knowledge_points: List[KnowledgePoint]  # 知识点列表
    pages: int                 # 页数
    error: Optional[str]       # 错误信息
    metadata: Dict             # 元数据
    ocr_results: Optional[List]  # OCR 结果（扫描版）
    latex_formulas: List[Dict]  # LaTeX 公式列表
```

### KnowledgePoint

```python
@dataclass
class KnowledgePoint:
    title: str                 # 标题
    content: str               # 内容
    page: int                  # 页码
    confidence: float          # 置信度 (0-1)
    tags: List[str]            # 标签
    metadata: Dict             # 元数据
    latex_formulas: List[str]  # 相关公式
```

## 错误处理

```python
result = parse_pdf("document.pdf")

if not result.success:
    print(f"解析失败：{result.error}")
    
    # 常见错误：
    # - "文件不存在"
    # - "OCR 解析失败"
    # - "PDF 损坏"
```

## 性能优化

### 1. 使用 GPU 加速 OCR

```python
service = PDFParserService(use_gpu=True)
```

### 2. 批量处理

```python
# 批量解析比逐个解析更高效
results = service.parse_batch(pdf_list)
```

### 3. 指定类型

```python
# 跳过类型检测
result = parse_pdf("known_text.pdf", pdf_type=PDFType.TEXT)
```

### 4. 限制页数

```python
# OCR 时只处理前 N 页
from edict.backend.app.services.ocr_parser import OCRParserService
ocr_service = OCRParserService()
results = ocr_service.parse_pdf("large.pdf", pages=[1, 2, 3])
```

## 测试

### 运行测试

```bash
cd /root/edict

# 运行所有 PDF 测试
pytest tests/test_pdf_parser.py -v
pytest tests/test_pdf_real_files.py -v

# 运行特定类型测试
pytest tests/test_pdf_real_files.py::TestTextPDFRealFiles -v
pytest tests/test_pdf_real_files.py::TestScannedPDFRealFiles -v

# 生成覆盖率报告
pytest tests/test_pdf_parser.py --cov=edict.backend.app.services.pdf_parser
```

### 添加测试文件

将测试 PDF 放入 `tests/pdf_samples/` 目录：

```
tests/pdf_samples/
├── text_*.pdf      # 纯文本型
├── scanned_*.pdf   # 扫描版
├── mixed_*.pdf     # 混合型
├── formula_*.pdf   # 公式型
└── table_*.pdf     # 表格型
```

## 已知限制

### 1. OCR 限制

- 手写体识别准确率较低
- 复杂排版可能识别错误
- 低分辨率扫描件效果差
- 建议分辨率 ≥ 300 DPI

### 2. LaTeX 识别限制

- 需要安装 pix2tex（首次使用下载模型 ~200MB）
- 复杂公式可能识别不完整
- 不支持化学方程式
- 手写公式识别率较低

### 3. 表格识别限制

- 无线表格识别效果差
- 跨页表格可能拆分
- 合并单元格可能丢失
- 复杂嵌套表格支持有限

### 4. 性能限制

- 大文件（>100 页）处理较慢
- OCR 处理需要较长时间
- 批量处理建议分批进行

## 依赖安装

### 基础依赖

```bash
pip install pypdf pypdfium2 --break-system-packages
```

### OCR 依赖（扫描版支持）

```bash
# PaddleOCR（已安装）
pip install paddlepaddle paddleocr --break-system-packages
```

### LaTeX OCR 依赖（公式识别）

```bash
# pix2tex
pip install pix2tex[gui] --break-system-packages
```

### 完整安装

```bash
cd /root/edict
pip install -r requirements.txt --break-system-packages
```

## 最佳实践

### 1. 选择合适的解析器

```python
# 已知是纯文本 PDF
result = parse_pdf("text.pdf", pdf_type=PDFType.TEXT)

# 不确定类型，让系统自动检测
result = parse_pdf("unknown.pdf")
```

### 2. 处理大文件

```python
# 分批处理
service = PDFParserService()
for pdf_path in large_pdf_list:
    result = service.parse(pdf_path)
    # 处理结果
```

### 3. 错误重试

```python
from tenacity import retry, stop_after_attempt

@retry(stop=stop_after_attempt(3))
def parse_with_retry(pdf_path):
    return parse_pdf(pdf_path)
```

### 4. 结果缓存

```python
import hashlib
import pickle

def get_cache_key(pdf_path):
    with open(pdf_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def parse_with_cache(pdf_path):
    cache_key = get_cache_key(pdf_path)
    cache_file = Path(f"/tmp/pdf_cache/{cache_key}.pkl")
    
    if cache_file.exists():
        with open(cache_file, 'rb') as f:
            return pickle.load(f)
    
    result = parse_pdf(pdf_path)
    
    with open(cache_file, 'wb') as f:
        pickle.dump(result, f)
    
    return result
```

## 版本历史

- **v1.0** (2026-03-26): 初始版本，支持 5 类 PDF 解析
- **v1.1** (2026-03-26): 集成 OCR 和 LaTeX 识别

## 常见问题

### Q: 扫描版 PDF 解析很慢？

A: OCR 是计算密集型操作。建议：
- 使用 GPU 加速
- 限制处理页数
- 批量处理时控制并发

### Q: LaTeX 公式识别不准确？

A: 可能原因：
- 公式图片质量差
- 公式过于复杂
- 模型未正确加载

建议检查 pix2tex 安装和模型下载。

### Q: 如何提取特定页面的内容？

A: 使用 OCR 服务的 pages 参数：
```python
ocr_service = OCRParserService()
results = ocr_service.parse_pdf("book.pdf", pages=[1, 2, 3])
```

### Q: 知识点提取太少？

A: 调整 `_extract_knowledge_points` 方法中的阈值：
- 降低最小段落长度（默认 20 字符）
- 修改分割正则表达式
- 添加自定义提取规则

## 联系方式

问题反馈：@taizi 或提交 Issue
