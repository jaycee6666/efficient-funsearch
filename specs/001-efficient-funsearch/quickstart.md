# Quickstart: Efficient FunSearch

**Date**: 2026-02-23
**Feature**: 001-efficient-funsearch

---

## 5 分钟快速开始

### 环境准备

```bash
# 克隆仓库
git clone https://github.com/RayZhhh/funsearch.git
cd funsearch

# 安装依赖
pip install -r requirements.txt

# 安装 Efficient FunSearch 扩展
pip install -e ../efficient_funsearch
```

### Google Colab 快速开始

```python
# 在 Colab 中运行
!pip install git+https://github.com/YOUR_REPO/efficient_funsearch.git

from efficient_funsearch import run_with_filter

# 运行带重复检测的 FunSearch
result = run_with_filter(
    problem="bin_packing",
    iterations=100,
    similarity_threshold=0.95
)

print(f"Best solution: {result.best_program}")
print(f"LLM queries saved: {result.metrics.llm_queries_saved}")
```

---

## 完整使用示例

> v1 默认流程：**behavioral deduplication → full evaluation → diversity-guided selection**。

### 1. 基础用法

```python
from efficient_funsearch import (
    ProgramNormalizer,
    HybridSimilarityDetector,
    ProgramArchive,
    EfficiencyTracker
)

# 初始化组件
normalizer = ProgramNormalizer()
detector = HybridSimilarityDetector(
    embedding_threshold=0.95,
    ast_threshold=0.98
)
archive = ProgramArchive()
tracker = EfficiencyTracker()

# 处理新程序
def process_program(source_code: str) -> tuple[bool, float | None]:
    """处理一个新程序，返回 (是否新程序, 分数)"""
    # 1. 标准化
    normalized = normalizer.normalize(source_code)
    
    # 2. 检查重复
    if archive.is_duplicate(normalized):
        tracker.record_duplicate()
        return False, None
    
    # 3. 评估 (模拟)
    score = evaluate_program(source_code)  # 用户自定义
    
    # 4. 存档
    archive.add(source_code, normalized, score)
    tracker.record_evaluation()
    
    return True, score
```

### 2. 与 FunSearch 集成

```python
from funsearch import FunSearch
from efficient_funsearch import FunSearchAdapter

# 创建带过滤的 FunSearch
funsearch = FunSearch(problem="bin_packing")
enhanced = FunSearchAdapter(
    funsearch=funsearch,
    enable_filtering=True,
    similarity_threshold=0.95
)

# 运行
result = enhanced.run(iterations=100)

# 查看效率指标
print(result.metrics.summary())
```

### 3. 行为去重与多样性权重

```python
from efficient_funsearch import HybridSimilarityDetector

# v1 配置示例
detector_v1 = HybridSimilarityDetector()

print(detector_v1.config.behavior_probe_count_min)   # 5
print(detector_v1.config.behavior_probe_count_max)   # 15
print(detector_v1.config.behavior_similarity_threshold)  # 0.95
print(detector_v1.config.diversity_weight)           # 0.2
```

### 4. 离线模式 (无需 GPU)

```python
from efficient_funsearch import HybridSimilarityDetector

# 禁用嵌入，仅使用 AST 比较
detector_offline = HybridSimilarityDetector(
    use_embedding=False,
    ast_threshold=0.98
)
```

---

## API 参考

### ProgramNormalizer

```python
class ProgramNormalizer:
    def normalize(self, source_code: str) -> NormalizedProgram:
        """将 Python 代码标准化为规范形式"""
        
    def normalize_batch(self, programs: list[str]) -> list[NormalizedProgram]:
        """批量标准化"""
```

### HybridSimilarityDetector

```python
class HybridSimilarityDetector:
    def __init__(
        self,
        embedding_threshold: float = 0.95,
        ast_threshold: float = 0.98,
        use_embedding: bool = True,
        embedding_model: str = "codebert-base"
    ): ...
    
    def is_similar(
        self, 
        program_a: NormalizedProgram,
        program_b: NormalizedProgram
    ) -> SimilarityResult:
        """检测两个程序是否相似"""
        
    def find_similar(
        self,
        program: NormalizedProgram,
        archive: ProgramArchive,
        k: int = 5
    ) -> list[SimilarityResult]:
        """在存档中查找相似程序"""
```

### ProgramArchive

```python
class ProgramArchive:
    def __init__(self, config: ArchiveConfig | None = None): ...
    
    def add(
        self, 
        source_code: str,
        normalized: NormalizedProgram,
        score: float
    ) -> str:
        """添加程序到存档，返回程序 ID"""
        
    def is_duplicate(self, normalized: NormalizedProgram) -> bool:
        """检查是否为重复程序"""
        
    def get_best(self, k: int = 10) -> list[Program]:
        """获取评分最高的 k 个程序"""
        
    def save(self, path: str) -> None:
        """持久化存档"""
        
    @classmethod
    def load(cls, path: str) -> "ProgramArchive":
        """加载存档"""
```

### EfficiencyTracker

```python
class EfficiencyTracker:
    def record_generation(self) -> None:
        """记录生成了一个新程序"""
        
    def record_duplicate(self) -> None:
        """记录检测到重复"""
        
    def record_evaluation(self, time_seconds: float) -> None:
        """记录完成一次评估"""
        
    def summary(self) -> dict:
        """返回效率统计摘要"""
        
    def compare_baseline(self, baseline: "EfficiencyTracker") -> dict:
        """与基线对比"""
```

---

## 常见问题

### Q: 嵌入模型下载慢怎么办？

```python
# 使用镜像
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from efficient_funsearch import HybridSimilarityDetector
detector = HybridSimilarityDetector()
```

### Q: 内存不够怎么办？

```python
# 限制存档大小
from efficient_funsearch import ProgramArchive, ArchiveConfig

config = ArchiveConfig(
    max_archive_size=1000,  # 最多存储 1000 个程序
    cache_embeddings=False   # 不缓存嵌入向量
)
archive = ProgramArchive(config)
```

### Q: 如何切换到仅 AST 模式？

```python
# 禁用嵌入检测
detector = HybridSimilarityDetector(use_embedding=False)
```

---

## 下一步

1. 查看完整 [API 文档](./contracts/)
2. 阅读 [实验指南](./experiments.md)
3. 了解 [性能调优](./performance.md)
