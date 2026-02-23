# Data Model: Efficient FunSearch

**Date**: 2026-02-23
**Feature**: 001-efficient-funsearch

---

## 核心实体

### 1. Program (程序)

表示一个由 LLM 生成的启发式函数。

```
Program
├── id: str                 # 唯一标识符 (UUID)
├── source_code: str        # 原始 Python 代码
├── normalized_code: str    # 标准化后的代码
├── score: float | None     # 评估分数 (None 表示未评估)
├── created_at: datetime    # 创建时间
├── generation: int         # 第几代生成
└── parent_ids: list[str]   # 父程序 ID (用于进化追踪)
```

**验证规则**:
- `source_code` 必须是有效的 Python 语法
- `normalized_code` 由 normalizer 自动生成
- `score` 在评估后设置

**状态转换**:
```
[新建] → [标准化] → [检测重复] → [评估] → [存档]
         ↓
    [标记为重复，跳过评估]
```

---

### 2. NormalizedProgram (标准化程序)

程序的标准化表示，用于相似度比较。

```
NormalizedProgram
├── canonical_code: str     # 规范化代码字符串
├── ast_hash: str           # AST 结构哈希
├── embedding: list[float]  # 代码嵌入向量 (可选)
└── token_count: int        # Token 数量
```

**生成规则**:
- 所有变量名重命名为 `var_0`, `var_1`, ...
- 移除所有注释和文档字符串
- 标准化空白和缩进

---

### 3. ProgramArchive (程序存档)

存储所有已评估程序及其标准化形式。

```
ProgramArchive
├── programs: dict[str, Program]           # id → Program
├── ast_index: dict[str, str]              # ast_hash → program_id
├── embedding_index: EmbeddingIndex        # 向量索引
├── stats: ArchiveStats                    # 统计信息
└── config: ArchiveConfig                  # 配置
```

**操作**:
- `add(program)`: 添加程序到存档
- `is_duplicate(normalized) → bool`: 检查是否重复
- `get_similar(normalized, k) → list[Program]`: 获取相似程序
- `get_best(k) → list[Program]`: 获取最佳程序

---

### 4. SimilarityResult (相似度结果)

表示两个程序的相似度检测结果。

```
SimilarityResult
├── program_a_id: str
├── program_b_id: str
├── embedding_similarity: float    # 0-1，嵌入相似度
├── ast_similarity: float          # 0-1，AST 相似度
├── is_duplicate: bool             # 综合判定结果
└── detection_time: float          # 检测耗时 (秒)
```

**判定规则**:
```
is_duplicate = (
    embedding_similarity >= embedding_threshold AND
    ast_similarity >= ast_threshold
)
```

---

### 5. EfficiencyMetrics (效率指标)

记录增强 FunSearch 的效率改进。

```
EfficiencyMetrics
├── total_programs_generated: int
├── duplicates_detected: int
├── duplicates_filtered: int
├── programs_evaluated: int
├── llm_queries_saved: int
├── evaluation_time_saved: float    # 秒
├── detection_time_total: float     # 检测总耗时
└── session_id: str                  # 实验会话 ID
```

**关键比率**:
- 重复检测率 = `duplicates_detected / total_programs_generated`
- LLM 节省率 = `llm_queries_saved / total_programs_generated`
- 时间节省比 = `evaluation_time_saved / (evaluation_time_saved + detection_time_total)`

---

## 实体关系图

```
┌─────────────┐     标准化      ┌──────────────────┐
│   Program   │ ──────────────▶ │ NormalizedProgram │
└─────────────┘                 └──────────────────┘
       │                                │
       │ 存储                           │ 查找
       ▼                                ▼
┌─────────────────────────────────────────────────┐
│              ProgramArchive                      │
│  ┌─────────────┐  ┌──────────────┐              │
│  │ programs    │  │ embedding_   │              │
│  │ dict        │  │ index        │              │
│  └─────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────┘
       │
       │ 生成
       ▼
┌─────────────────┐
│ SimilarityResult │
└─────────────────┘
       │
       │ 累计
       ▼
┌──────────────────┐
│ EfficiencyMetrics │
└──────────────────┘
```

---

## 配置实体

### ArchiveConfig

```
ArchiveConfig
├── embedding_threshold: float = 0.95   # 嵌入相似度阈值
├── ast_threshold: float = 0.98         # AST 相似度阈值
├── max_archive_size: int = 10000       # 最大存档大小
├── use_embedding: bool = True          # 是否使用嵌入预筛选
├── cache_embeddings: bool = True       # 是否缓存嵌入
└── persistence_path: str | None        # 持久化路径
```

### DetectorConfig

```
DetectorConfig
├── embedding_model: str = "codebert-base"
├── max_workers: int = 4                # 并行检测线程数
├── timeout_seconds: float = 1.0        # 单次检测超时
└── fallback_to_ast: bool = True        # 嵌入失败时回退到 AST
```
