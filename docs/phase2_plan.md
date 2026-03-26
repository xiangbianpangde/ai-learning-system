# Phase 2 個性化學習開發計劃

**任務 ID**: JJC-20260325-001-PHASE2  
**版本**: v1.0  
**起草**: 中書省  
**日期**: 2026-03-26

---

## 一、功能詳細設計

### 1.1 學習風格識別（P0）

**目標**: 識別用戶學習風格（視覺型/聽覺型/動手型/閱讀型），提供個性化內容推薦

**實現細節**:
- **VARK 問卷**: 12 題標準化評估，每題 4 選項對應 V/A/R/K 四維度
- **行為分析**: 追蹤內容類型點擊率、停留時長、互動深度
- **評分算法**: 問卷 60% + 行為 40% 加權計算
- **推薦引擎**: 根據主導風格推薦圖文/視頻/實踐/閱讀內容

**數據結構**:
```python
class LearningStyle:
    user_id: str
    v_score: float  # Visual 0-100
    a_score: float  # Auditory 0-100
    r_score: float  # Read/Write 0-100
    k_score: float  # Kinesthetic 0-100
    dominant_style: str  # V/A/R/K
    confidence: float  # 0-1
    last_updated: datetime
```

---

### 1.2 動態難度調整（P0）

**目標**: 根據用戶實時表現自動調整題目/解釋難度（L1-L5）

**實現細節**:
- **IRT 模型**: 使用三參數 Logistic 模型 (3PL)
  - 難度參數 (b): -3 到 +3
  - 區分度參數 (a): 0.5 到 2.0
  - 猜測參數 (c): 0 到 0.25
- **實時追蹤**: 正確率、響應時間、嘗試次數
- **難度分級**:
  - L1: 基礎概念 (b < -1.5)
  - L2: 簡單應用 (-1.5 ≤ b < -0.5)
  - L3: 標準難度 (-0.5 ≤ b < 0.5)
  - L4: 進階應用 (0.5 ≤ b < 1.5)
  - L5: 挑戰題 (b ≥ 1.5)
- **調整策略**: 連續 3 題正確→升級；連續 2 題錯誤→降級

**數據結構**:
```python
class ItemResponse:
    item_id: str
    difficulty: float  # b parameter
    discrimination: float  # a parameter
    guessing: float  # c parameter
    user_ability: float  # theta estimate
    response_time: float  # seconds
    correct: bool
```

---

### 1.3 遺忘曲線校準（P1）

**目標**: 基於用戶數據校準復習時間，優化長期記憶保留

**實現細節**:
- **基礎模型**: Ebbinghaus 遺忘曲線 R = e^(-t/S)
- **個體校準**: 記憶衰減係數 S 根據用戶歷史數據調整
- **SM-2 改進**:
  - 初始間隔：1 天、3 天、7 天
  - 質量評分 0-5 調整間隔係數
  - 遺忘閾值：保留率 < 70% 觸發復習
- **推送提醒**: 復習時間前 1 小時推送通知

**數據結構**:
```python
class ForgettingCurve:
    user_id: str
    item_id: str
    learned_at: datetime
    decay_coefficient: float  # S parameter
    reviews: List[ReviewRecord]
    next_review: datetime
    retention_rate: float  # 0-1
```

---

### 1.4 學習路徑自適應（P1）

**目標**: 根據用戶進度和掌握程度動態調整學習順序

**實現細節**:
- **知識圖譜**: DAG 結構表示知識點依賴關係
- **前置檢查**: 學習新知識點前驗證前置掌握度 ≥ 80%
- **跳過機制**: 預測試正確率 ≥ 90% 可跳過已掌握內容
- **路徑算法**: Dijkstra 最短路徑 + 掌握度加權
- **推薦策略**: 最小依賴數優先 + 難度梯度平緩

**數據結構**:
```python
class KnowledgeGraph:
    nodes: Dict[str, KnowledgePoint]
    edges: List[Dependency]  # (prerequisite, dependent)

class KnowledgePoint:
    id: str
    mastery: float  # 0-1
    prerequisites: List[str]
    difficulty: float
    estimated_time: int  # minutes
```

---

## 二、技術架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React/Vue)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ VARK 問卷 │ │ 難度調整 │ │ 復習提醒 │ │ 路徑推薦 │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
                            │ HTTP/WebSocket
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway                             │
│                    (FastAPI / Flask)                         │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ Learning     │   │ Adaptive     │   │ Forgetting   │
│ Style Service│   │ Difficulty   │   │ Curve        │
│              │   │ Service      │   │ Service      │
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ PostgreSQL   │  │ Redis Cache  │  │ TimescaleDB  │      │
│  │ (用戶/題目)   │  │ (實時狀態)   │  │ (行為日誌)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## 三、數據模型設計

### 3.1 核心表結構

```sql
-- 用戶學習風格
CREATE TABLE user_learning_styles (
    user_id UUID PRIMARY KEY,
    v_score DECIMAL(5,2),
    a_score DECIMAL(5,2),
    r_score DECIMAL(5,2),
    k_score DECIMAL(5,2),
    dominant_style VARCHAR(1),
    confidence DECIMAL(3,2),
    questionnaire_completed BOOLEAN,
    last_updated TIMESTAMP
);

-- 題目難度參數
CREATE TABLE item_parameters (
    item_id UUID PRIMARY KEY,
    difficulty DECIMAL(5,3),  -- b
    discrimination DECIMAL(5,3),  -- a
    guessing DECIMAL(5,3),  -- c
    difficulty_level INT,  -- L1-L5
    knowledge_point_id UUID
);

-- 用戶作答記錄
CREATE TABLE user_responses (
    id UUID PRIMARY KEY,
    user_id UUID,
    item_id UUID,
    correct BOOLEAN,
    response_time INT,  -- seconds
    attempted_at TIMESTAMP,
    ability_estimate DECIMAL(5,3)  -- theta
);

-- 遺忘曲線記錄
CREATE TABLE forgetting_curves (
    user_id UUID,
    item_id UUID,
    learned_at TIMESTAMP,
    decay_coefficient DECIMAL(5,3),
    next_review TIMESTAMP,
    retention_rate DECIMAL(5,3),
    PRIMARY KEY (user_id, item_id)
);

-- 知識圖譜
CREATE TABLE knowledge_points (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    mastery DECIMAL(5,3),
    difficulty DECIMAL(5,3),
    estimated_time INT
);

CREATE TABLE knowledge_dependencies (
    prerequisite_id UUID,
    dependent_id UUID,
    PRIMARY KEY (prerequisite_id, dependent_id)
);
```

---

## 四、API 接口定義

### 4.1 學習風格

```
POST /api/v1/learning-style/assess
  Body: { user_id, answers: [{question_id, selected_option}] }
  Response: { style_scores, dominant_style, confidence }

GET /api/v1/learning-style/{user_id}
  Response: { v_score, a_score, r_score, k_score, dominant_style }

POST /api/v1/learning-style/recommend
  Body: { user_id, content_pool: [{id, type, tags}] }
  Response: { recommended_content: [{id, score, reason}] }
```

### 4.2 動態難度

```
POST /api/v1/adaptive/next-item
  Body: { user_id, current_ability, last_responses: [...] }
  Response: { item_id, difficulty_level, estimated_success_rate }

PUT /api/v1/adaptive/update-ability
  Body: { user_id, item_id, correct, response_time }
  Response: { new_ability, confidence_interval }

GET /api/v1/adaptive/user-progress/{user_id}
  Response: { current_level, ability_estimate, accuracy_rate }
```

### 4.3 遺忘曲線

```
POST /api/v1/forgetting/learn
  Body: { user_id, item_id, quality_score }
  Response: { next_review_time, retention_rate }

GET /api/v1/forgetting/due/{user_id}
  Response: { due_items: [{item_id, due_at, priority}] }

PUT /api/v1/forgetting/review
  Body: { user_id, item_id, quality_score }
  Response: { next_review_time, updated_decay_coefficient }
```

### 4.4 學習路徑

```
GET /api/v1/path/recommend/{user_id}
  Response: { path: [{knowledge_point_id, order, estimated_time}], total_time }

POST /api/v1/path/check-prerequisites
  Body: { user_id, target_knowledge_id }
  Response: { can_start: bool, missing_prerequisites: [...] }

POST /api/v1/path/skip
  Body: { user_id, knowledge_point_id, test_score }
  Response: { skipped: bool, reason }
```

---

## 五、測試計劃

### 5.1 單元測試（覆蓋率 ≥ 85%）

| 模組 | 測試文件 | 關鍵測試用例 |
|------|----------|--------------|
| learning_style | test_learning_style.py | VARK 評分計算、風格分類、推薦排序 |
| adaptive_difficulty | test_adaptive_difficulty.py | IRT 參數估計、難度調整邏輯、邊界條件 |
| forgetting_curve | test_forgetting_curve.py | 衰減係數計算、復習時間預測、SM-2 算法 |
| learning_path | test_learning_path.py | 依賴檢查、路徑規劃、跳過邏輯 |

### 5.2 集成測試

- **端到端流程**: 問卷→風格識別→內容推薦→作答→難度調整→復習提醒
- **性能測試**: 單用戶 API 延遲 < 100ms, 併發 1000 QPS
- **數據一致性**: 用戶狀態在各服務間同步

### 5.3 用戶測試

- **樣本量**: 30 名用戶，為期 2 周
- **指標**:
  - 風格識別準確率 ≥ 75% (用戶自評對比)
  - 難度調整滿意度 ≥ 4/5
  - 復習提醒準時率 ≥ 95%
  - 學習效率提升 ≥ 20% (前後測對比)

---

## 六、時間表

| 階段 | 時間 | 任務 | 負責人 | 產出 |
|------|------|------|--------|------|
| **計劃** | Week 0 | 中書省起草、門下省審議 | 中書省 | 本計劃文檔 |
| **執行 W1** | Day 1-3 | 學習風格識別開發 | 工部 | learning_style.py + 測試 |
| **執行 W1** | Day 4-7 | 動態難度調整開發 | 工部 | adaptive_difficulty.py + 測試 |
| **執行 W2** | Day 8-10 | 遺忘曲線校準開發 | 工部 | forgetting_curve.py + 測試 |
| **執行 W2** | Day 11-14 | 學習路徑自適應開發 | 工部 | learning_path.py + 測試 |
| **執行 W3** | Day 15-17 | API 集成 + 前端對接 | 工部 + 前端 | 完整 API + UI |
| **執行 W4** | Day 18-21 | 數據庫遷移 + 性能優化 | 工部 | 數據庫腳本 + 壓測報告 |
| **測試 W5** | Day 22-25 | 集成測試 + 用戶測試 | 測試組 | 測試報告 + Bug 修復 |
| **上線** | Day 26-28 | 灰度發布 + 監控 | 运维 | 上線報告 |

---

## 七、風險與緩解

| 風險 | 概率 | 影響 | 緩解措施 |
|------|------|------|----------|
| IRT 模型收斂慢 | 中 | 高 | 預先標定題目參數，使用貝葉斯估計 |
| 用戶行為數據不足 | 高 | 中 | 冷啟動使用問卷結果，逐步過渡到行為分析 |
| 知識圖譜構建複雜 | 高 | 高 | 先覆蓋核心 20% 知識點，迭代擴充 |
| 復習提醒推送延遲 | 中 | 中 | 使用消息隊列 + 重試機制 |

---

## 八、驗收標準對照

| 功能 | 驗收指標 | 目標 | 驗證方法 |
|------|----------|------|----------|
| 學習風格 | VARK 問卷完整 | 12 題 | 代碼審查 |
| 學習風格 | 行為數據收集 | 完整 | 日誌檢查 |
| 學習風格 | 識別準確率 | ≥ 75% | 用戶測試 |
| 動態難度 | 題目難度標定 | 完整 | 數據庫檢查 |
| 動態難度 | 追蹤延遲 | < 1 秒 | 性能測試 |
| 動態難度 | 調整準確率 | ≥ 80% | 用戶測試 |
| 遺忘曲線 | 基礎模型正確 | ✅ | 單元測試 |
| 遺忘曲線 | 個體校準誤差 | < 20% | 數據分析 |
| 遺忘曲線 | 復習提醒準時 | ✅ | 日誌檢查 |
| 學習路徑 | 知識依賴完整 | ✅ | 代碼審查 |
| 學習路徑 | 前置檢查準確 | ✅ | 集成測試 |
| 學習路徑 | 效率提升 | ≥ 20% | 用戶測試 |

---

**中書省起草完成，提交門下省審議。**
