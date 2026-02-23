# Program Archive Interface Contract

**Version**: 1.0
**Date**: 2026-02-23

---

## 概述

`ProgramArchive` 存储所有已评估的程序及其标准化形式，提供高效的重复检测和程序检索功能。

---

## 接口定义

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, Iterator
from .normalizer import NormalizedProgram

@dataclass
class Program:
    """存储的程序记录"""
    id: str                     # UUID
    source_code: str            # 原始代码
    normalized_code: str        # 标准化代码
    ast_hash: str               # AST 哈希
    score: float | None         # 评估分数
    created_at: datetime        # 创建时间
    generation: int             # 第几代
    parent_ids: list[str]       # 父程序 ID

@dataclass
class ArchiveStats:
    """存档统计信息"""
    total_programs: int
    unique_programs: int        # 去重后
    duplicate_count: int
    avg_score: float | None
    best_score: float | None
    memory_usage_mb: float

@dataclass
class ArchiveConfig:
    """存档配置"""
    max_archive_size: int = 10000       # 最大程序数
    embedding_threshold: float = 0.95   # 重复检测阈值
    ast_threshold: float = 0.98
    use_embedding_index: bool = True    # 是否使用嵌入索引
    cache_embeddings: bool = True       # 是否缓存嵌入
    persistence_path: str | None = None # 持久化路径

class ProgramArchive(Protocol):
    """程序存档接口"""
    
    def __init__(self, config: ArchiveConfig | None = None): ...
    
    # ==================== 写入操作 ====================
    
    def add(
        self, 
        source_code: str,
        normalized: NormalizedProgram,
        score: float | None = None,
        generation: int = 0,
        parent_ids: list[str] | None = None
    ) -> str:
        """
        添加程序到存档
        
        Args:
            source_code: 原始代码
            normalized: 标准化后的程序
            score: 评估分数 (可选)
            generation: 第几代
            parent_ids: 父程序 ID
            
        Returns:
            str: 程序 ID
            
        Raises:
            ValueError: 如果存档已满
        """
        ...
    
    def update_score(self, program_id: str, score: float) -> None:
        """更新程序分数"""
        ...
    
    def remove(self, program_id: str) -> bool:
        """移除程序"""
        ...
    
    # ==================== 查询操作 ====================
    
    def get(self, program_id: str) -> Program | None:
        """通过 ID 获取程序"""
        ...
    
    def is_duplicate(self, normalized: NormalizedProgram) -> bool:
        """
        检查程序是否为重复
        
        Args:
            normalized: 标准化后的程序
            
        Returns:
            True 如果存档中存在相似程序
        """
        ...
    
    def find_similar(
        self, 
        normalized: NormalizedProgram, 
        k: int = 5
    ) -> list[tuple[Program, float]]:
        """
        查找相似程序
        
        Args:
            normalized: 目标程序
            k: 返回数量
            
        Returns:
            (程序, 相似度) 元组列表，按相似度降序
        """
        ...
    
    def get_best(self, k: int = 10) -> list[Program]:
        """获取评分最高的 k 个程序"""
        ...
    
    def get_by_generation(self, generation: int) -> list[Program]:
        """获取指定代的所有程序"""
        ...
    
    # ==================== 统计与持久化 ====================
    
    def stats(self) -> ArchiveStats:
        """获取存档统计"""
        ...
    
    def save(self, path: str | None = None) -> None:
        """持久化存档"""
        ...
    
    @classmethod
    def load(cls, path: str) -> "ProgramArchive":
        """加载存档"""
        ...
    
    def clear(self) -> None:
        """清空存档"""
        ...
    
    def __len__(self) -> int:
        """返回存档中的程序数量"""
        ...
    
    def __iter__(self) -> Iterator[Program]:
        """迭代所有程序"""
        ...
```

---

## 数据结构

### 内存布局

```
ProgramArchive
├── programs: dict[str, Program]        # O(1) ID 查找
├── ast_index: dict[str, str]           # O(1) AST 哈希查找
├── embedding_index: EmbeddingIndex     # 向量相似度搜索
│   ├── embeddings: np.ndarray          # (N, D) 嵌入矩阵
│   └── ids: list[str]                  # 对应的程序 ID
├── score_heap: MaxHeap[str]            # O(log N) 最佳程序查询
└── config: ArchiveConfig
```

### 向量索引

```python
class EmbeddingIndex:
    """简化的向量索引 (不依赖外部库)"""
    
    def __init__(self, dimension: int = 768):
        self.embeddings = []  # list[np.ndarray]
        self.ids = []
    
    def add(self, program_id: str, embedding: list[float]) -> None:
        self.embeddings.append(np.array(embedding))
        self.ids.append(program_id)
    
    def search(self, query: list[float], k: int) -> list[tuple[str, float]]:
        """暴力搜索最近邻"""
        query_vec = np.array(query)
        similarities = [
            (id_, np.dot(query_vec, emb) / (np.linalg.norm(query_vec) * np.linalg.norm(emb)))
            for id_, emb in zip(self.ids, self.embeddings)
        ]
        return sorted(similarities, key=lambda x: -x[1])[:k]
```

---

## 性能保证

| 操作 | 时间复杂度 | 目标延迟 |
|------|-----------|----------|
| 添加程序 | O(1) + O(d) | < 10ms |
| ID 查找 | O(1) | < 1ms |
| AST 哈希查找 | O(1) | < 1ms |
| 嵌入相似度搜索 | O(N×d) | < 500ms |
| 获取最佳程序 | O(log N) | < 1ms |
| 持久化 | O(N) | < 5s |

*N = 存档大小, d = 嵌入维度*

---

## 持久化格式

```json
{
  "version": "1.0",
  "config": {
    "max_archive_size": 10000,
    "embedding_threshold": 0.95
  },
  "programs": [
    {
      "id": "uuid-1",
      "source_code": "def heuristic(...): ...",
      "normalized_code": "def heuristic(var_0, var_1): ...",
      "ast_hash": "sha256...",
      "score": 0.85,
      "created_at": "2026-02-23T10:00:00",
      "generation": 5,
      "parent_ids": ["uuid-parent-1"]
    }
  ],
  "embeddings": {
    "uuid-1": [0.1, 0.2, ...]
  }
}
```

---

## 容量管理

```python
# 达到容量限制时的策略
class ArchiveEvictionPolicy(Enum):
    REMOVE_WORST = "remove_worst"        # 移除评分最低的
    REMOVE_OLDEST = "remove_oldest"      # 移除最早的
    NO_EVICTION = "no_eviction"          # 拒绝新程序

config = ArchiveConfig(
    max_archive_size=1000,
    eviction_policy=ArchiveEvictionPolicy.REMOVE_WORST
)
```

---

## 错误处理

```python
try:
    program_id = archive.add(source_code, normalized, score)
except ValueError as e:
    if "archive full" in str(e):
        # 存档已满，执行清理
        archive.remove_worst(10)
        program_id = archive.add(source_code, normalized, score)
except IOError as e:
    # 持久化失败
    print(f"Failed to persist: {e}")
```

---

## 依赖

- Python 标准库: `json`, `uuid`, `datetime`, `heapq`
- `numpy`: 向量计算
