# CS5491 Project Milestone Report Draft（中英文对照）

> 对应课程要求 / Aligned with course milestone requirements:  
> 1) Problem description & motivation  
> 2) Design of method/approach  
> 3) Preliminary results

---

## 1. Project Information / 项目信息

- **Course / 课程**: CS5491
- **Project / 题目**: Sample-Efficient FunSearch via Behavioral Deduplication and Diversity-Guided Selection  
  基于行为去重与多样性引导选择的高样本效率 FunSearch
- **Team members / 团队成员**: `<填写姓名与学号>`
- **Date / 日期**: `<提交日期>`

---

## 2. Problem Description and Motivation / 问题描述与动机

### EN
LLM-driven program search (e.g., FunSearch) often generates many behaviorally redundant candidates. Although these candidates may look syntactically different, they can make equivalent decisions on the target task. Evaluating such duplicates wastes API calls and compute, reducing sample efficiency.

Our project focuses on online bin packing and aims to improve search efficiency without sacrificing final solution quality. We introduce two mechanisms:

1. Behavioral deduplication before full evaluation;
2. Diversity-guided selection to avoid early strategy collapse.

### 中文
在 LLM 驱动的程序搜索（如 FunSearch）中，常出现大量“语法不同但行为等价”的候选程序。若这些候选都进入完整评估，会显著浪费 API 调用与算力预算，导致样本效率下降。

本项目聚焦在线装箱任务，目标是在不降低最终解质量的前提下提升搜索效率。我们采用两条主线机制：

1. 在完整评估前执行行为去重；
2. 在候选选择中加入多样性引导，避免搜索过早塌缩。

---

## 3. Design of Method / Approach / 方法设计

### 3.1 Pipeline Overview / 流程总览

### EN
Current v1 pipeline:

1. Candidate generation
2. Behavioral probing (5–15 probes)
3. Behavioral duplicate filtering (threshold > 0.95)
4. Full evaluation for non-duplicates
5. Archive update
6. Diversity-guided candidate selection

### 中文
当前 v1 主流程：

1. 候选生成
2. 行为探测（5–15 个探测样例）
3. 行为重复过滤（阈值 > 0.95）
4. 对未过滤候选执行完整评估
5. 更新归档
6. 进行多样性引导选择

### 3.2 Behavioral Deduplication / 行为去重

### EN
We build deterministic behavioral fingerprints and compare them with archive fingerprints. Candidates above similarity threshold are filtered before expensive evaluation.

### 中文
我们构建确定性的行为指纹，并与归档候选进行相似度比较。超过阈值的候选在高成本评估前被过滤。

Implemented modules / 已实现模块：

- `src/similarity/behavioral_probe.py`
- `src/similarity/hybrid.py`
- `src/archive/program_archive.py`
- `src/integration/funsearch_adapter.py`

### 3.3 Diversity-Guided Selection / 多样性引导选择

### EN
Candidate ranking uses a combined score:

\[
\text{combined}(c)=\text{perf}(c)+\beta\cdot\text{diversity}(c)
\]

### 中文
候选排序采用联合评分：

\[
\text{combined}(c)=\text{perf}(c)+\beta\cdot\text{diversity}(c)
\]

Implemented modules / 已实现模块：

- `src/similarity/diversity.py`
- `src/integration/funsearch_adapter.py`
- `src/metrics/efficiency_logger.py`

### 3.4 Metrics and Ablation / 指标与消融

### EN
Metrics include sample efficiency, duplicate detection rate, convergence, and final quality. We also define 4 ablation settings (`original`, `exact_string_match`, `normalized_hash_only`, `behavioral_plus_diversity`).

### 中文
指标包含样本效率、重复检测率、收敛相关指标、最终质量指标。消融配置包含 4 组：`original`、`exact_string_match`、`normalized_hash_only`、`behavioral_plus_diversity`。

---

## 4. Preliminary Results / 初步结果

### 4.1 Current Engineering Evidence / 当前工程证据

### EN
- `ruff check .` passed
- `pytest -q -rs` passed: **65 passed, 0 skipped**
- US1/US2/US3 paths are covered by unit/integration tests

### 中文
- `ruff check .` 已通过
- `pytest -q -rs` 已通过：**65 passed, 0 skipped**
- US1/US2/US3 主线路径均已由单元与集成测试覆盖

### 4.2 Preliminary Table Template / 初步结果表模板

> 可直接复制下表到最终提交文档。  
> You can directly copy this table into your milestone submission.

| Setting | N_total | N_unique | Sample Efficiency η | Duplicate Rate | Convergence Proxy | Final Quality Proxy | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| original | 待填 / TBF | 待填 / TBF | 待填 / TBF | 待填 / TBF | 待填 / TBF | 待填 / TBF | Config ready |
| exact_string_match | 待填 / TBF | 待填 / TBF | 待填 / TBF | 待填 / TBF | 待填 / TBF | 待填 / TBF | Config ready |
| normalized_hash_only | 待填 / TBF | 待填 / TBF | 待填 / TBF | 待填 / TBF | 待填 / TBF | 待填 / TBF | Config ready |
| behavioral_plus_diversity | 待填 / TBF | 待填 / TBF | 待填 / TBF | 待填 / TBF | 待填 / TBF | 待填 / TBF | Mainline implemented |

### 4.3 How to Fill the Preliminary Table / 怎么填 preliminary result 表格

### EN (Practical mapping)

For each run/setting:

1. **N_total** = `total_programs_generated`
2. **N_unique** = `programs_evaluated` (current implementation uses this as unique evaluated candidates)
3. **Sample Efficiency η** = `N_unique / N_total` (or directly `sample_efficiency`)
4. **Duplicate Rate** = `duplicates_detected / total_programs_generated` (or directly `duplicate_detection_rate`)
5. **Convergence Proxy** = metric you define consistently (e.g., generation index reaching target score)
6. **Final Quality Proxy** = final bin-packing quality metric (e.g., best score / bins used)

Fields are provided by:

- `src/metrics/models.py` (`sample_efficiency`, `duplicate_detection_rate`)
- `src/metrics/efficiency_logger.py` (`metadata.summary.convergence`, `metadata.summary.final_quality`)

### 中文（可执行填表步骤）

每个 setting 跑一次实验后，按下面映射填：

1. **N_total**：填 `total_programs_generated`
2. **N_unique**：填 `programs_evaluated`（当前实现中它对应“实际进入评估的唯一候选”）
3. **Sample Efficiency η**：填 `N_unique / N_total`（或直接填 `sample_efficiency`）
4. **Duplicate Rate**：填 `duplicates_detected / total_programs_generated`（或直接填 `duplicate_detection_rate`）
5. **Convergence Proxy**：你们统一定义一个可比口径（例如达到目标分数的 generation）
6. **Final Quality Proxy**：填最终质量指标（例如 best score 或 bins used）

如果 milestone 时间不够做全量 benchmark，可以：

- 先在表中标注 “TBF（to be filled）”；
- 同时保留 4.1 的工程证据表（65 passed, 0 skipped），说明“实现与验证已完成，数值实验在跑”。

---

## 5. Reproducibility / 可复现性

```bash
ruff check .
pytest -q -rs
```

Expected / 预期：

- lint pass
- tests pass (currently 65 passed, 0 skipped)

---

## 6. What to Fill Before Submission / 提交前你要补什么

1. Team members / 团队成员
2. Benchmark details / benchmark 细节（数据集、规模、预算）
3. Preliminary numeric table / 初步数值表（至少一版）
4. Optional figures / 可选图表（1–2 张）
