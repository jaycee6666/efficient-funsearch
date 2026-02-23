# Normalizer Interface Contract

**Version**: 1.0
**Date**: 2026-02-23

---

## 概述

`ProgramNormalizer` 负责将 Python 源代码转换为标准化的规范形式，用于后续的相似度检测。

---

## 接口定义

```python
from dataclasses import dataclass
from typing import Protocol

@dataclass
class NormalizedProgram:
    """标准化后的程序"""
    canonical_code: str       # 规范化代码字符串
    ast_hash: str             # AST 结构哈希 (SHA256)
    embedding: list[float]    # 代码嵌入向量 (可选，延迟计算)
    token_count: int          # Token 数量
    original_source: str      # 原始源代码 (用于调试)

class ProgramNormalizer(Protocol):
    """程序标准化器接口"""
    
    def normalize(self, source_code: str) -> NormalizedProgram:
        """
        将 Python 源代码标准化
        
        Args:
            source_code: Python 函数源代码字符串
            
        Returns:
            NormalizedProgram: 标准化后的程序
            
        Raises:
            SyntaxError: 如果源代码包含语法错误
        """
        ...
    
    def normalize_batch(
        self, 
        source_codes: list[str]
    ) -> list[NormalizedProgram]:
        """
        批量标准化多个程序
        
        Args:
            source_codes: Python 源代码列表
            
        Returns:
            标准化后的程序列表
            
        Note:
            如果任一程序有语法错误，返回列表中对应位置为 None
        """
        ...
    
    def compute_embedding(
        self, 
        normalized: NormalizedProgram
    ) -> list[float]:
        """
        计算代码嵌入向量
        
        Args:
            normalized: 标准化后的程序
            
        Returns:
            嵌入向量 (维度取决于嵌入模型)
        """
        ...
```

---

## 输入格式

### 支持的输入

```python
# 有效的 Python 函数
source = '''
def priority(item, bins):
    """计算物品放入箱子的优先级"""
    remaining = [b - item for b in bins]
    return min(range(len(remaining)), key=lambda i: remaining[i])
'''
```

### 不支持的输入

```python
# 语法错误
invalid = 'def foo(:\n    return 1'  # 缺少括号

# 非函数代码
invalid = 'x = 1 + 2'  # 不是函数定义

# 多个函数
invalid = '''
def foo(): pass
def bar(): pass
'''  # 只支持单个函数
```

---

## 输出格式

### 标准化规则

| 变换 | 示例 |
|------|------|
| 变量重命名 | `remaining` → `var_0` |
| 参数重命名 | `item, bins` → `var_0, var_1` |
| 移除文档字符串 | `"""doc"""` → (移除) |
| 移除注释 | `# comment` → (移除) |
| 标准化缩进 | 统一为 4 空格 |

### 输出示例

**输入**:
```python
def heuristic(items, capacity):
    """贪心启发式"""
    bins = []
    for item in items:  # 按顺序处理
        best_bin = find_best(item, bins)
        if best_bin:
            bins[best_bin] += item
        else:
            bins.append(item)
    return len(bins)
```

**标准化输出**:
```python
def heuristic(var_0, var_1):
    var_2 = []
    for var_3 in var_0:
        var_4 = find_best(var_3, var_2)
        if var_4:
            var_2[var_4] += var_3
        else:
            var_2.append(var_3)
    return len(var_2)
```

---

## 性能保证

| 操作 | 时间复杂度 | 目标延迟 |
|------|-----------|----------|
| 标准化 | O(n) | < 100ms |
| 批量标准化 | O(n×m) | < 1s / 100个 |
| 嵌入计算 | O(n) | < 500ms |

*n = 代码长度, m = 批量大小*

---

## 错误处理

```python
try:
    normalized = normalizer.normalize(source_code)
except SyntaxError as e:
    # 语法错误
    print(f"Invalid Python: {e}")
except ValueError as e:
    # 非函数代码
    print(f"Expected function: {e}")
```

---

## 依赖

- Python 标准库: `ast`, `hashlib`
- 可选: `sentence_transformers` (嵌入计算)
