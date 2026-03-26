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

本项目聚焦在线装箱任务，目标是在不降低最终解质量的前提下提升搜索效率。我们采用两条主线机制：

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

### 4.1 当前工程证据

- `ruff check .` 已通过
- `pytest -q -rs` 已通过：**65 passed, 0 skipped**
- US1/US2/US3 主线路径均已由单元与集成测试覆盖

### 4.2 初步结果表

本表对应的 benchmark 口径：OR-Library `binpack1.txt` 前 3 个实例（`u120_00`、`u120_01`、`u120_02`），单代（1-generation）初步运行。
`Final Quality Proxy` 取 3 个实例上 `(best_known_bins / bins_used)` 的平均值（越高越好）。

| Setting | N_total | N_unique | Sample Efficiency η | Duplicate Rate | Convergence Proxy | Final Quality Proxy | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| original | 4 | 4 | 1.0000 | 0.0000 | OR-Library prelim (1 generation) | 0.9861 | OR-Library preliminary measured |
| exact_string_match | 4 | 4 | 1.0000 | 0.0000 | OR-Library prelim (1 generation) | 0.9861 | OR-Library preliminary measured |
| normalized_hash_only | 4 | 4 | 1.0000 | 0.0000 | OR-Library prelim (1 generation) | 0.9861 | OR-Library preliminary measured |
| behavioral_plus_diversity | 4 | 4 | 1.0000 | 0.0000 | OR-Library prelim (1 generation) | 0.9861 | OR-Library preliminary measured |

### 4.3 填表口径说明

每个 setting 跑一次实验后，按下面映射填：

1. **N_total**：`total_programs_generated`
2. **N_unique**：`programs_evaluated`
3. **Sample Efficiency η**：`N_unique / N_total`（或 `sample_efficiency`）
4. **Duplicate Rate**：`duplicates_detected / total_programs_generated`（或 `duplicate_detection_rate`）
5. **Convergence Proxy**：统一定义可比口径
6. **Final Quality Proxy**：最终质量指标（如 best score）

---

## 5. 可复现性

```bash
ruff check .
pytest -q -rs
```

预期：

- lint pass
- tests pass（currently 65 passed, 0 skipped）
