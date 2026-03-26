# 性能優化指南

**版本**: 1.0  
**更新日期**: 2026-03-26  
**適用範圍**: 48 小時 AI 導師系統

---

## 概述

本文檔提供系統性能優化的詳細指南，涵蓋 PDF 解析、知識圖譜加載和公式渲染三個核心模塊。

---

## 目錄

1. [PDF 解析優化](#pdf-解析優化)
2. [知識圖譜優化](#知識圖譜優化)
3. [公式渲染優化](#公式渲染優化)
4. [最佳實踐](#最佳實踐)
5. [故障排查](#故障排查)

---

## PDF 解析優化

### 問題場景

- 大文件 PDF（>50MB）解析時間過長
- 內存使用過高導致 OOM
- 用戶等待體驗差

### 優化方案

#### 1. 使用優化版解析器

```python
from edict.backend.app.services.pdf_parser_optimized import parse_pdf_optimized

# 基本用法
result = parse_pdf_optimized("large_file.pdf")

# 帶進度回調
def on_progress(progress):
    print(f"進度：{progress.percentage:.1f}%")

result = parse_pdf_optimized(
    "large_file.pdf",
    progress_callback=on_progress
)
```

#### 2. 配置參數調優

```python
from edict.backend.app.services.pdf_parser_optimized import OptimizedPDFParser

parser = OptimizedPDFParser(
    use_gpu=False,           # GPU 加速（需要 CUDA）
    use_cache=False,         # 使用檢查點而非緩存
    max_workers=4,           # 並發工作線程數
    page_batch_size=10,      # 每批處理頁數
    max_memory_mb=500.0,     # 最大內存限制
    enable_checkpoint=True   # 啟用斷點續傳
)
```

#### 3. 斷點續傳

```python
# 第一次解析（可能中斷）
try:
    result = parser.parse(Path("large.pdf"))
except KeyboardInterrupt:
    print("解析中斷，檢查點已保存")

# 恢復解析
result = parser.parse(
    Path("large.pdf"),
    resume_checkpoint_id="pdf_<hash>"
)
```

### 性能基準

| 文件大小 | 目標時間 | 內存限制 |
|----------|----------|----------|
| 10MB | < 5 秒 | < 200MB |
| 50MB | < 15 秒 | < 300MB |
| 100MB | < 30 秒 | < 500MB |
| 200MB | < 60 秒 | < 500MB |

### 注意事項

1. **並發度選擇**: `max_workers` 建議設置為 CPU 核心數的 1-2 倍
2. **批量大小**: `page_batch_size` 過大會增加內存使用，過小會影響並發效率
3. **檢查點清理**: 解析完成後檢查點會自動刪除

---

## 知識圖譜優化

### 問題場景

- 大型圖譜（>1000 節點）加載卡頓
- 頁面 FPS 低於 30
- 滾動時延遲明顯

### 優化方案

#### 1. 前端組件配置

```tsx
import { KnowledgeGraph } from './components/KnowledgeGraph';

<KnowledgeGraph
  nodes={nodes}
  maxDepth={5}                    // 限制加載深度
  enableVirtualScroll={true}      // 啟用虛擬滾動
  enableLazyLoad={true}           // 啟用惰性加載
  onNodeExpand={handleExpand}     // 按需加載子樹
/>
```

#### 2. 後端數據優化

```python
from edict.backend.app.services.knowledge_graph import KnowledgeGraphService

service = KnowledgeGraphService()

# 加載圖譜
graph = service.load_from_pdf("graph_id", knowledge_points)

# 獲取子樹（分層加載）
subtree = service.get_node_tree(
    "graph_id",
    root_id="node_001",
    depth=2  # 只加載 2 層
)

# 獲取可見節點（虛擬滾動）
visible = service.get_visible_nodes(
    "graph_id",
    expanded_nodes=["node_001", "node_002"],
    scroll_offset=0,
    viewport_size=50
)
```

#### 3. Web Worker 集成

```typescript
// 自動檢測並使用 Web Worker
// 當節點數 > 100 時自動啟用

const graph = new KnowledgeGraph({
  enableWorker: true,  // 默認開啟
  workerThreshold: 100  // 觸發 Worker 的節點數閾值
});
```

### 性能基準

| 節點數 | 目標加載時間 | 目標 FPS |
|--------|--------------|----------|
| 100 | < 0.5 秒 | 60 |
| 500 | < 1 秒 | 60 |
| 1000 | < 2 秒 | 55+ |
| 2000 | < 3 秒 | 50+ |

### 注意事項

1. **虛擬滾動**: 確保節點高度固定（默认 40px）
2. **惰性加載**: 配合 `onNodeExpand` 回調實現按需加載
3. **數據扁平化**: 使用 `to_flat_dict()` 減少傳輸數據量

---

## 公式渲染優化

### 問題場景

- LaTeX 公式渲染失敗
- 顯示錯亂或亂碼
- 加載時閃爍

### 優化方案

#### 1. 使用 Formula 組件

```tsx
import Formula from './components/FormulaRenderer';

// 行內公式
<Formula latex="E = mc^2" />

// 塊級公式
<Formula latex="\int_0^\infty e^{-x^2} dx" displayMode={true} />

// 帶錯誤處理
<Formula
  latex={complexFormula}
  onError={(err) => console.error('渲染失敗:', err)}
  onRender={() => console.log('渲染成功')}
/>
```

#### 2. 批量預加載

```tsx
import { preloadFormulas, FormulaList } from './components/FormulaRenderer';

// 預加載公式（避免閃爍）
await preloadFormulas([
  'E = mc^2',
  'F = ma',
  '\\nabla \\cdot E = \\rho/\\epsilon_0'
]);

// 批量渲染（支持虛擬滾動）
const formulas = [
  { id: '1', latex: 'E = mc^2', displayMode: true },
  { id: '2', latex: 'F = ma', displayMode: true },
  // ...
];

<FormulaList formulas={formulas} batchSize={10} />
```

#### 3. 錯誤降級

```tsx
// 渲染失敗時自動顯示 LaTeX 源碼
<Formula
  latex={potentiallyInvalidFormula}
  className="custom-formula"
/>

// 自定義降級樣式
.custom-formula.formula-fallback {
  background: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 4px;
}
```

### 性能基準

| 指標 | 目標值 |
|------|--------|
| 渲染成功率 | ≥ 99% |
| 平均渲染時間 | < 50ms |
| 預加載時間（10 公式） | < 200ms |

### 注意事項

1. **MathJax 加載**: 首次使用時會自動加載 MathJax（約 100KB）
2. **公式長度**: 超過 5000 字符的公式會被截斷
3. **特殊字符**: 自動轉義 &, %, _ 等字符

---

## 最佳實踐

### 1. PDF 解析

```python
# ✅ 推薦：異步解析 + 進度回調
async def parse_large_pdf(file_path: str):
    async def on_progress(progress):
        update_ui_progress(progress.percentage)
    
    result = await parse_pdf_async_optimized(
        file_path,
        progress_callback=on_progress
    )
    return result

# ❌ 不推薦：同步阻塞解析
result = parse_pdf(file_path)  # 會阻塞 UI
```

### 2. 知識圖譜

```tsx
// ✅ 推薦：分層加載 + 虛擬滾動
<KnowledgeGraph
  nodes={largeNodeList}
  maxDepth={3}
  enableVirtualScroll={true}
  onNodeExpand={loadChildrenOnDemand}
/>

// ❌ 不推薦：一次性加載所有節點
<KnowledgeGraph nodes={allNodes} />  // 會卡頓
```

### 3. 公式渲染

```tsx
// ✅ 推薦：預加載 + 批量渲染
useEffect(() => {
  preloadFormulas(formulas.map(f => f.latex));
}, [formulas]);

<FormulaList formulas={formulas} batchSize={20} />

// ❌ 不推薦：逐个渲染
{formulas.map(f => <Formula key={f.id} latex={f.latex} />)}
```

---

## 故障排查

### PDF 解析問題

#### 問題：解析時間過長

**排查步驟**:
1. 檢查文件大小和頁數
2. 確認 `max_workers` 配置合理
3. 查看內存使用情況

```python
result = parse_pdf_optimized("file.pdf")
print(f"時間：{result.parse_time_ms:.1f}ms")
print(f"內存：{result.peak_memory_mb:.1f}MB")
```

#### 問題：內存溢出

**解決方案**:
1. 降低 `max_memory_mb` 限制
2. 減小 `page_batch_size`
3. 啟用檢查點（自動釋放內存）

```python
parser = OptimizedPDFParser(
    max_memory_mb=300.0,      # 降低內存限制
    page_batch_size=5         # 減小批量大小
)
```

### 知識圖譜問題

#### 問題：頁面卡頓

**排查步驟**:
1. 確認啟用虛擬滾動
2. 檢查節點數量
3. 查看瀏覽器 FPS

```tsx
// 開啟開發者工具的性能監控
<KnowledgeGraph
  nodes={nodes}
  enableVirtualScroll={true}
  onPerformanceReport={(fps) => console.log('FPS:', fps)}
/>
```

#### 問題：子樹加載失敗

**解決方案**:
1. 檢查 `children_ids` 是否正確設置
2. 確認 `maxDepth` 參數合理
3. 查看網絡請求（如果使用 API）

### 公式渲染問題

#### 問題：公式顯示亂碼

**排查步驟**:
1. 檢查 LaTeX 語法
2. 查看瀏覽器控制台錯誤
3. 確認 MathJax 加載成功

```tsx
<Formula
  latex={formula}
  onError={(err) => {
    console.error('公式錯誤:', err);
    console.log('LaTeX:', formula);
  }}
/>
```

#### 問題：渲染閃爍

**解決方案**:
1. 使用 `preloadFormulas()` 預加載
2. 添加加載狀態指示器
3. 使用 `FormulaList` 批量渲染

---

## 相關文檔

- [性能 Bug 修復報告](./PERFORMANCE_BUGFIX_REPORT.md)
- [PDF 解析服務文檔](../edict/backend/app/services/PDF_PARSER_README.md)
- [前端組件文檔](./FRONTEND_COMPONENTS.md)

---

**維護團隊**: 尚書省 · 工部  
**最後更新**: 2026-03-26
