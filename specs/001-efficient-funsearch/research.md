# Research: Efficient FunSearch

**Date**: 2026-02-23
**Feature**: 001-efficient-funsearch

---

## R-001: FunSearch 基础代码研究

### 研究来源
- GitHub: https://github.com/RayZhhh/funsearch
- 相关论文: Romera-Paredes et al. (2023), "Mathematical discoveries from program search with large language models", Nature

### 关键发现

#### 1. FunSearch 主要迭代循环

FunSearch 的核心循环在 `funsearch/run_funsarch.py` 中：

```python
# 简化的迭代循环结构
def run_evolution(sampler, evaluator, iterations):
    programs_database = ProgramsDatabase()
    for i in range(iterations):
        # LLM 生成新程序
        new_programs = sampler.sample(programs_database)
        # 评估每个程序
        for program in new_programs:
            score = evaluator.evaluate(program)
            programs_database.register(program, score)
    return programs_database.best()
```

#### 2. 注入过滤逻辑的位置

**最佳注入点**: 在 `evaluator.evaluate()` 调用之前

```python
# 增强后的循环
def run_evolution_with_filter(sampler, evaluator, iterations, archive):
    for i in range(iterations):
        new_programs = sampler.sample(programs_database)
        for program in new_programs:
            normalized = normalizer.normalize(program)
            if not archive.is_duplicate(normalized):
                score = evaluator.evaluate(program)
                archive.add(normalized, score)
```

#### 3. 程序格式

- **输入**: Python 函数字符串，包含特定签名（如 `def priority(item, bins)`）
- **输出**: 标量值或排序索引

### 决策

**选择**: 使用适配器模式包装 FunSearch 的评估流程

**理由**: 
- 不修改 FunSearch 核心代码
- 便于切换原始版本和增强版本进行对比实验
- 保持向后兼容性

---

## R-002: Python AST 标准化最佳实践

### 研究来源
- Python AST 官方文档
- 相关论文: "Detecting Code Clones with Graph Neural Networks" (2019)

### 关键发现

#### 1. 变量名标准化

使用 AST 遍历重命名所有变量：

```python
import ast

class VariableRenamer(ast.NodeTransformer):
    def __init__(self):
        self.name_map = {}
        self.counter = 0
    
    def _get_canonical_name(self, name):
        if name not in self.name_map:
            self.name_map[name] = f"var_{self.counter}"
            self.counter += 1
        return self.name_map[name]
    
    def visit_Name(self, node):
        node.id = self._get_canonical_name(node.id)
        return node
    
    def visit_arg(self, node):
        node.arg = self._get_canonical_name(node.arg)
        return node
```

#### 2. 处理注释和文档字符串

```python
def remove_docstrings(tree):
    """移除所有文档字符串"""
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
            if node.body and isinstance(node.body[0], ast.Expr):
                if isinstance(node.body[0].value, ast.Constant):
                    node.body = node.body[1:]
    return tree
```

#### 3. 语义等价变换处理

需要处理的变换：
- 常量折叠: `1 + 2` → `3`
- 死代码消除: 不可达代码移除
- 表达式规范化: `a + b` vs `b + a`（需特殊处理）

### 决策

**选择**: 实现完整的 AST 标准化管道

**实现步骤**:
1. 解析代码为 AST
2. 移除文档字符串和注释
3. 标准化变量名
4. 可选：常量折叠
5. 序列化回代码字符串

**备选方案考虑并拒绝**:
- 纯字符串匹配：太不精确
- Token 序列匹配：无法处理变量重命名

---

## R-003: 代码嵌入模型选择

### 候选模型评估

| 模型 | 大小 | Colab 可用 | Python 效果 | 推理速度 |
|------|------|-----------|-------------|----------|
| CodeBERT | ~500MB | ✅ HuggingFace | 优秀 | 中等 |
| StarCoder Embeddings | ~1GB | ✅ | 优秀 | 慢 |
| sentence-transformers/codebert-base | ~500MB | ✅ | 良好 | 快 |
| OpenAI Embeddings API | N/A | ✅ | 优秀 | 快（API） |

### 决策

**选择**: 混合策略

1. **首选**: `sentence-transformers/codebert-base` 
   - 轻量，适合 Colab
   - 无需 API 调用，节省配额

2. **备选**: OpenAI `text-embedding-3-small`
   - 如果本地模型不可用
   - API 调用，计入配额

**理由**: 
- 本地模型避免额外 API 调用
- sentence-transformers 在 Colab 上有良好支持
- CodeBERT 对 Python 代码效果经过验证

---

## R-004: 在线装箱问题基准

### 数据集

#### OR-Library (主要)
- URL: http://people.brunel.ac.uk/~mastjjb/jeb/info.html
- 格式: 文本文件，每行一个实例
- 包含: 最优解已知的标准实例

#### Weibull 数据集
- 用于在线装箱的变体
- 模拟真实物品到达分布

### 评估指标

| 指标 | 定义 |
|------|------|
| 箱子数量 | 使用的箱子总数（越少越好） |
| 浪费率 | (使用空间 - 物品总体积) / 使用空间 |
| 首次适应下降 | 与 First-Fit-Decreasing 的差距 |

### 基线算法

1. **First-Fit (FF)**: 放入第一个能容纳的箱子
2. **Best-Fit (BF)**: 放入剩余空间最小的箱子
3. **First-Fit Decreasing (FFD)**: 排序后 First-Fit
4. **原始 FunSearch**: 无重复检测

### 决策

**选择**: 使用 OR-Library 中小型实例进行主要实验

**理由**:
- 中小型实例评估快，适合迭代开发
- 已知最优解便于比较
- 最终可在大型实例上验证

---

## 总结

| 研究项 | 决策 | 关键考量 |
|--------|------|----------|
| FunSearch 集成 | 适配器模式 | 不修改核心代码 |
| AST 标准化 | 完整管道 | 处理变量重命名 |
| 嵌入模型 | sentence-transformers/codebert-base | Colab 友好 |
| 基准数据集 | OR-Library | 已知最优解 |
