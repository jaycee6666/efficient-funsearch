# CS5491 项目里程碑报告草稿（中文版）

> 对应课程里程碑要求：
> 1) Problem description & motivation
> 2) Design of method/approach
> 3) Preliminary results

---

## 1. 项目信息

- **课程**: CS5491
- **项目题目**: 基于行为去重与多样性引导选择的高样本效率 FunSearch
- **团队成员**: CHEN Sijie (59872908) & BIAN Wenbo (59872472)
- **日期**: 2026-03-27

---

## 2. 问题描述与动机

在 LLM 驱动的程序搜索（如 FunSearch）中，常出现大量“语法不同但行为等价”的候选程序。若这些候选都进入完整评估，会显著浪费 API 调用与算力预算，导致样本效率下降。

本项目聚焦在线装箱任务，目标是在不降低最终解质量的前提下提升搜索效率。在 Phase 1 基线实验中（53 个样本，OR3 数据集，gpt-5-nano），我们发现 **45% 的评估调用产生的分数与已有程序完全相同**，说明这些程序在行为上是冗余的。这意味着近一半的 LLM API 调用和评估时间都浪费在了重复程序上。我们采用两条主线机制：

1. 在完整评估前执行行为去重；
2. 在候选选择中加入多样性引导，避免搜索过早塌缩。

---

## 3. 方法设计

### 3.1 流程总览

当前 v1 主流程：

1. 候选生成
2. 行为探测（5–15 个探测样例）
3. 行为重复过滤（阈值 > 0.95）
4. 对未过滤候选执行完整评估
5. 更新归档
6. 进行多样性引导选择

### 3.2 行为去重

我们构建确定性的行为指纹，并与归档候选进行相似度比较。超过阈值的候选在高成本评估前被过滤。

已实现模块：

- `src/similarity/behavioral_probe.py`
- `src/similarity/hybrid.py`
- `src/archive/program_archive.py`
- `src/integration/funsearch_adapter.py`

### 3.3 多样性引导选择

候选排序采用联合评分：

`combined(c) = perf(c) + beta * diversity(c)`

已实现模块：

- `src/similarity/diversity.py`
- `src/integration/funsearch_adapter.py`
- `src/metrics/efficiency_logger.py`

### 3.4 指标与消融

指标包含样本效率、重复检测率、收敛相关指标、最终质量指标。消融配置包含 4 组：`original`、`exact_string_match`、`normalized_hash_only`、`behavioral_plus_diversity`。

### 3.5 基准数据集细节

- **主要基准**：OR-Library 装箱实例
- **来源**：http://people.brunel.ac.uk/~mastjjb/jeb/info.html
- **数据格式**：文本实例（按行组织）
- **当前里程碑范围**：先使用中小规模实例做快速初步结果验证

---

## 4. 初步结果

### 4.1 基线实验配置

我们运行了 Phase 1 基线实验，用于量化原始 FunSearch 在在线装箱任务上的自然重复率与收敛行为。

**实验配置：**

| 参数 | 值 |
|------|-----|
| LLM 模型 | gpt-5-nano（reasoning model）|
| 数据集 | OR3（20 个在线装箱实例）|
| 总样本数 | 53（10 个 seed + 43 个 LLM 生成）|
| Island 数量 | 10 |
| 每次 prompt 采样数 | 4 |
| 评估超时 | 30 秒 |
| 总墙钟时间 | ~40 分钟 |

### 4.2 关键发现

**发现 1：45% 自然重复率** — 仅 53 个样本中，45% 的评估结果与已有程序完全相同。近一半 API 调用和评估时间浪费在行为冗余的程序上，直接支撑了 Phase 2 行为去重方案的必要性。

**发现 2：搜索提前收敛** — 约在第 8 个样本时发现了接近最优的策略（分数 ≈ −212.1），之后 45+ 个样本的提升不足 0.1 分。这支撑了 Phase 3 多样性引导选择的动机。

**发现 3：100% 成功率** — 全部 53 个程序均成功执行并获得有效评分，基础设施运行可靠。

### 4.3 基线指标

| 指标 | 值 |
|------|-----|
| N_total（总程序数）| 53 |
| N_unique（唯一分数数）| 29 |
| 样本效率 η | 0.55 |
| 自然重复率 | 0.45 |
| 最佳分数 | −212.0 |
| 均值 ± 标准差 | −345.79 ± 122.02 |
| 收敛（第 8 个样本后改进）| < 0.1 分 |
| 平均评估时间 | 4.14 秒/样本 |
| 平均采样时间 | 42.50 秒/样本 |

### 4.4 工程验证

- `pytest -q -rs` 已通过：**65 passed, 0 skipped**
- `ruff check .` 已通过：**All checks passed!**
- US1/US2/US3 主线路径均已由单元与集成测试覆盖

---

## 5. 可复现性与 Colab 提交对齐（Course Instruction 1.2）

课程 1.2 要求代码以 Google Colab 形式可直接运行并带有清晰说明。当前对应路径：

- `notebooks/efficient_funsearch_colab.ipynb`

该 Colab notebook 提供：

1. 高层任务摘要（代码目标与任务背景）
2. 从克隆、安装到运行验证的完整流程
3. 关键单元注释（每段代码用途说明）
4. 可直接运行的 milestone 风格输出（`N_total/N_unique/sample_efficiency/duplicate_rate/...`）

```bash
ruff check .
pytest -q -rs
```

预期：

- tests pass（currently 65 passed, 0 skipped）
- lint pass

### 5.1 提交前质量门禁快照（2026-03-30）

- `ruff check .` → **All checks passed!**
- `pytest -q -rs` → **65 passed in 0.29s**
