# Implementation Plan: Efficient FunSearch

**Branch**: `001-efficient-funsearch` | **Date**: 2026-02-23 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-efficient-funsearch/spec.md`

## Summary

实现一个 Sample-efficient FunSearch 系统，通过添加代码相似度检测机制来减少冗余程序的评估。系统使用两阶段混合方法（嵌入预筛选 + AST 精确验证）来识别功能重复的程序，从而节省 LLM API 调用和评估时间。

---

## Technical Context

**Language/Version**: Python 3.10+（与 FunSearch 兼容）
**Primary Dependencies**: 
- OpenAI API（LLM 调用）
- Python AST 模块（代码解析）
- Sentence-Transformers / CodeBERT（代码嵌入）
- NumPy（向量计算）
- pytest（测试框架）

**Storage**: 
- 内存哈希表（程序存档）
- 可选文件持久化（检查点）

**Testing**: pytest + unittest
**Target Platform**: Google Colab（最终提交）/ 本地开发环境
**Project Type**: 算法研究库 + Google Colab Notebook
**Performance Goals**: 
- 单次相似度检测 < 1秒
- 存档查找 O(1) 平均时间

**Constraints**: 
- ChatGPT API 配额约 20,000 次查询
- Google Colab 自包含运行
- 最终报告 4-6 页

**Scale/Scope**: 
- 单问题领域（在线装箱问题）
- 2 人团队
- 8 周开发周期

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

项目尚未定义 constitution，以下为默认检查项：

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 测试优先 (TDD) | ✅ | 所有功能模块需先写测试 |
| 代码自包含 | ✅ | Google Colab 要求无外部依赖 |
| 文档完整 | ✅ | 每个单元格需有注释 |
| 可复现性 | ✅ | 固定随机种子，记录实验参数 |

---

## Project Structure

### Documentation (this feature)

```text
specs/001-efficient-funsearch/
├── spec.md              # 功能规范（英文版）
├── spec_zh.md           # 功能规范（中文版）
├── plan.md              # 本文件
├── research.md          # Phase 0 研究结果
├── data-model.md        # Phase 1 数据模型
├── quickstart.md        # Phase 1 快速开始
├── contracts/           # Phase 1 接口定义
│   └── normalizer.md    # 标准化接口
│   └── detector.md      # 检测器接口
│   └── archive.md       # 存档接口
└── tasks.md             # Phase 2 任务列表
```

### Source Code (repository root)

```text
src/
├── __init__.py
├── normalizer/
│   ├── __init__.py
│   ├── ast_normalizer.py    # AST 标准化器
│   └── variable_renamer.py  # 变量重命名
├── similarity/
│   ├── __init__.py
│   ├── embedding.py         # 代码嵌入
│   ├── ast_compare.py       # AST 比较
│   └── hybrid.py            # 混合检测器
├── archive/
│   ├── __init__.py
│   ├── program_archive.py   # 程序存档
│   └── hash_store.py        # 哈希存储
├── integration/
│   ├── __init__.py
│   └── funsearch_adapter.py # FunSearch 适配器
└── metrics/
    ├── __init__.py
    └── efficiency_logger.py # 效率日志

tests/
├── unit/
│   ├── test_normalizer.py
│   ├── test_similarity.py
│   └── test_archive.py
├── integration/
│   └── test_funsearch_integration.py
└── fixtures/
    └── sample_programs.py   # 测试用程序样本

notebooks/
└── efficient_funsearch.ipynb # Google Colab 最终版本
```

**Structure Decision**: 采用单项目结构，因为这是一个独立的算法增强库。核心模块分为 normalizer（标准化）、similarity（相似度检测）、archive（存档）和 integration（集成）。最终在 notebooks/ 中提供 Google Colab 版本。

---

## Complexity Tracking

无违规项需要说明。

---

## Phase 0: Research Tasks

### R-001: FunSearch 基础代码研究

**目标**: 理解 RayZhhh/funsearch 的代码结构和接口

**研究问题**:
1. FunSearch 的主要迭代循环在哪里？
2. 如何注入候选程序评估前的过滤逻辑？
3. 程序生成的输入输出格式是什么？

### R-002: Python AST 标准化最佳实践

**目标**: 确定代码规范化的具体实现方案

**研究问题**:
1. 如何将变量名标准化为规范形式？
2. 如何处理注释、文档字符串？
3. 如何处理语义等价的代码变换？

### R-003: 代码嵌入模型选择

**目标**: 选择适合的代码嵌入模型

**候选模型**:
- CodeBERT (Microsoft)
- StarCoder Embeddings
- Sentence-Transformers (code-specific)

**评估标准**:
- 在 Google Colab 上的可用性
- 模型大小和推理速度
- 对 Python 代码的效果

### R-004: 在线装箱问题基准

**目标**: 确定实验评估的数据集和基线

**研究问题**:
1. OR-Library 数据集格式？
2. 已知最优解或基线算法？
3. 评估指标定义？

---

## Phase 1: Design Artifacts

详见后续生成的 `data-model.md`、`quickstart.md` 和 `contracts/` 目录。
