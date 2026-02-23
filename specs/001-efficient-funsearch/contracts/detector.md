# Similarity Detector Interface Contract

**Version**: 1.0
**Date**: 2026-02-23

---

## 概述

`HybridSimilarityDetector` 使用混合方法检测程序相似度：第一阶段使用代码嵌入进行快速预筛选，第二阶段使用 AST 进行精确验证。

---

## 接口定义

```python
from dataclasses import dataclass
from typing import Protocol
from .normalizer import NormalizedProgram

@dataclass
class SimilarityResult:
    """相似度检测结果"""
    program_a_id: str
    program_b_id: str
    embedding_similarity: float    # 0-1，嵌入相似度
    ast_similarity: float          # 0-1，AST 相似度
    is_duplicate: bool             # 综合判定结果
    detection_time: float          # 检测耗时 (秒)
    detection_method: str          # "embedding_only" | "ast_only" | "hybrid"

@dataclass
class DetectorConfig:
    """检测器配置"""
    embedding_threshold: float = 0.95
    ast_threshold: float = 0.98
    use_embedding: bool = True
    embedding_model: str = "codebert-base"
    max_workers: int = 4
    timeout_seconds: float = 1.0
    fallback_to_ast: bool = True

class HybridSimilarityDetector(Protocol):
    """混合相似度检测器接口"""
    
    def __init__(self, config: DetectorConfig | None = None): ...
    
    def is_similar(
        self, 
        program_a: NormalizedProgram,
        program_b: NormalizedProgram
    ) -> SimilarityResult:
        """
        检测两个程序是否相似
        
        Args:
            program_a: 第一个程序
            program_b: 第二个程序
            
        Returns:
            SimilarityResult: 相似度检测结果
        """
        ...
    
    def find_similar(
        self,
        program: NormalizedProgram,
        candidates: list[NormalizedProgram],
        k: int = 5
    ) -> list[SimilarityResult]:
        """
        在候选程序中查找相似的程序
        
        Args:
            program: 目标程序
            candidates: 候选程序列表
            k: 返回的最大结果数
            
        Returns:
            相似度最高的 k 个结果，按相似度降序排列
        """
        ...
    
    def check_duplicate(
        self,
        program: NormalizedProgram,
        archive: "ProgramArchive"
    ) -> SimilarityResult | None:
        """
        检查程序是否与存档中的程序重复
        
        Args:
            program: 待检查程序
            archive: 程序存档
            
        Returns:
            如果找到重复，返回 SimilarityResult；否则返回 None
        """
        ...
```

---

## 检测流程

```
┌─────────────────┐
│   输入程序对    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  阶段1: 嵌入筛选 │
│ (可选，可跳过)  │
└────────┬────────┘
         │
    embedding_similarity >= threshold?
         │
    ┌────┴────┐
    │ No      │ Yes
    ▼         ▼
┌─────────┐ ┌─────────────────┐
│ 不重复   │ │ 阶段2: AST 验证 │
└─────────┘ └────────┬────────┘
                     │
                ast_similarity >= threshold?
                     │
                ┌────┴────┐
                │ No      │ Yes
                ▼         ▼
            ┌─────────┐ ┌─────────┐
            │ 不重复   │ │ 重复    │
            └─────────┘ └─────────┘
```

---

## 相似度计算

### 嵌入相似度

```python
import numpy as np

def compute_embedding_similarity(a: list[float], b: list[float]) -> float:
    """余弦相似度"""
    vec_a = np.array(a)
    vec_b = np.array(b)
    return np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))
```

### AST 相似度

```python
def compute_ast_similarity(a: NormalizedProgram, b: NormalizedProgram) -> float:
    """AST 结构相似度"""
    # 方法1: 树编辑距离
    # 方法2: 结构哈希比较 (快速但粗糙)
    if a.ast_hash == b.ast_hash:
        return 1.0
    # 更精细的比较...
```

---

## 配置建议

| 场景 | embedding_threshold | ast_threshold | 说明 |
|------|---------------------|---------------|------|
| 保守 (少误报) | 0.98 | 0.99 | 确保不过滤有价值程序 |
| 平衡 (推荐) | 0.95 | 0.98 | 平衡效率和质量 |
| 激进 (多过滤) | 0.90 | 0.95 | 最大化资源节省 |
| 仅 AST | N/A | 0.98 | 无 GPU 或离线场景 |

---

## 性能保证

| 操作 | 时间复杂度 | 目标延迟 |
|------|-----------|----------|
| 嵌入相似度 | O(d) | < 10ms |
| AST 相似度 | O(n²) | < 500ms |
| 批量检测 (k个候选) | O(k×d + k×n²) | < 1s |

*d = 嵌入维度, n = AST 节点数*

---

## 错误处理

```python
try:
    result = detector.is_similar(program_a, program_b)
except TimeoutError:
    # 检测超时，回退到 AST 模式
    result = detector.is_similar_ast_only(program_a, program_b)
except RuntimeError as e:
    # 嵌入模型加载失败
    print(f"Embedding model error: {e}")
    result = detector.is_similar_ast_only(program_a, program_b)
```

---

## 依赖

- `numpy`: 向量计算
- `sentence_transformers`: 代码嵌入 (可选)
- Python 标准库: `ast`, `asyncio`
