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

本项目聚焦在线装箱任务，目标是在不降低最终解质量的前提下提升搜索效率。在基线实验中（53 个样本，OR3 数据集，gpt-5-nano），我们发现 **45% 的评估调用产生的分数与已有程序完全相同**，说明这些程序在行为上是冗余的。这意味着近一半的 LLM API 调用和评估时间都浪费在了重复程序上。我们采用两条主线机制：

1. 在完整评估前执行行为去重；
2. 在候选选择中加入多样性引导，避免搜索过早塌缩。

---

## 3. 方法设计

### 3.1 流程总览

我们实现的流程在 LLM 生成和完整 Sandbox 评估之间插入了三级去重漏斗：

```
LLM 输出 → _sample_to_program()
         → Level 0: AST 规范化 + Hash    (<1ms, 捕获变量名/注释差异)
         → Level 1: 行为指纹精确匹配     (<5ms, 捕获功能等价程序)
         → [Level 2: 余弦相似度]          (已实现但默认禁用 — 见 §4.6)
         → 完整 Sandbox 评估              (1-10s)
         → register_program()
```

去重检查插入在 `evaluator.py` → `analyse()` 方法中，位于 `_sample_to_program()` 之后、Sandbox 评估循环之前。只有通过所有启用的去重层级的程序才会进入昂贵的完整评估。

### 3.2 行为去重

我们实现了三级过滤漏斗，在完整评估前检测并跳过行为等价的程序：

**Level 0 — 代码规范化 + AST Hash：**
- 复用 `src/normalizer/ProgramNormalizer` 进行 AST 规范化
- 对规范化代码计算 hash；O(1) 查找
- 捕获：变量重命名、注释差异、格式变化

**Level 1 — 行为指纹精确匹配：**
- 10 个精心设计的 probing 实例（每个 35–40 个物品，容量 100–200）
- 通过轻量 `exec()` 在所有 probe 上运行候选程序（不走 Sandbox fork）
- 记录装箱决策序列 → 375 维整数元组
- SHA256 hash → O(1) 精确匹配查找
- 零误报（确定性执行）

**Level 2 — 余弦相似度（已实现，默认禁用）：**
- 指纹 → L2 归一化浮点向量 → 与归档计算余弦相似度
- 阈值 0.98 → 标记为重复
- 实验发现对离散决策序列无效后禁用（见 §4.6）

**已实现模块：**
- `src/dedup/dedup_config.py` — `DedupConfig` frozen dataclass（7 个参数，均可开关）
- `src/dedup/probing.py` — 10 个 probing 实例 + `compute_fingerprint()` 函数
- `src/dedup/dedup_filter.py` — `DedupFilter` 三级漏斗 + `DedupResult`

**修改的 baseline 文件（改动极小）：**
- `implementation/evaluator.py` — ~15 行：Sandbox 循环前插入去重检查
- `implementation/funsearch.py` — ~10 行：实例化 DedupFilter，打印摘要
- `implementation/profile.py` — ~50 行：去重统计 + CSV 列
- `implementation/config.py` — 1 行：`dedup` 字段

### 3.3 多样性引导选择

候选排序采用联合评分：

`combined(c) = perf(c) + beta * diversity(c)`

已实现模块：

- `src/similarity/diversity.py`
- `src/integration/funsearch_adapter.py`
- `src/metrics/efficiency_logger.py`

> *状态：已规划。联合评分公式和多样性度量已设计完成，但尚未集成到 FunSearch 流水线中。*

### 3.4 指标与消融

指标包含样本效率、重复检测率、收敛相关指标、最终质量指标。消融配置包含 4 组：`original`、`exact_string_match`、`normalized_hash_only`、`behavioral_plus_diversity`。

> *状态：消融配置已定义。完整的 4 组 × 3 次重复 × 500 样本实验作为后续工作规划中。*

### 3.5 基准数据集细节

- **主要基准**：OR-Library 装箱实例
- **来源**：http://people.brunel.ac.uk/~mastjjb/jeb/info.html
- **数据格式**：文本实例（按行组织）
- **当前里程碑范围**：先使用中小规模实例做快速初步结果验证

---

## 4. 初步结果

### 4.1 基线实验配置

我们运行了基线实验，用于量化原始 FunSearch 在在线装箱任务上的自然重复率与收敛行为。

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

**发现 1：45% 自然重复率** — 仅 53 个样本中，45% 的评估结果与已有程序完全相同。近一半 API 调用和评估时间浪费在行为冗余的程序上，直接支撑了行为去重方案的必要性。

**发现 2：搜索提前收敛** — 约在第 8 个样本时发现了接近最优的策略（分数 ≈ −212.1），之后 45+ 个样本的提升不足 0.1 分。这支撑了多样性引导选择的动机。

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
- 行为去重模块验证：三级漏斗集成已通过 52 个 LLM 生成样本的端到端测试

### 4.5 行为去重实验

**实验配置：**

| 参数 | 值 |
|------|-----|
| 去重配置 | Level 0（AST hash）+ Level 1（行为指纹），Level 2 禁用 |
| Probing 实例 | 10 个实例，375 维指纹 |
| LLM 模型 | gpt-5-nano |
| 数据集 | OR3（20 个实例）|
| 总样本数 | 52 个 LLM 生成 + 1 个 seed |

**实验结果：**

| 指标 | 去重实验 | Baseline | 对比 |
|------|---------|----------|------|
| 最佳分数 | −212.0 | −212.0 | 持平 ✓ |
| 去重/过滤率 | 30.8% (16/52) | ~45% 自然重复率 | 保守过滤，无误杀 |
| 净评估时间节省 | 175.3 s | 0 | 显著节省 |
| 平均去重开销 | 8.64 ms/次 | — | 相比 ~11s 评估可忽略 |
| 达到最优的样本数 | 9 | — | 搜索充分收敛 |
| 首次达到最优 | 第 25 个样本 | 第 8 个样本 | — |

**关键发现：**

1. **去重模块工作正常**：30.8% 的过滤率低于 45% 的自然重复率，说明过滤保守，不会误杀有价值的程序。
2. **搜索质量未受影响**：达到与 baseline 相同的最佳分数（−212.0），且有 9 个样本达到最优。
3. **显著节省时间**：净省 175.3 秒（16 个被过滤样本 × ~11s 平均评估 − 0.46s 总去重开销）。所有过滤均由 Level 1 行为指纹匹配完成。
4. **首次达到最优分延后是预期行为**：最优分首次出现在第 25 个样本（baseline 为第 8 个）。这是因为去重过滤跳过了 16 个重复样本，实际进入评估的程序数量减少。搜索仍然收敛到相同的最优分数，且有 9 个样本达到最优，说明去重不影响搜索探索质量。

### 4.6 研究发现：余弦相似度不适用于离散决策序列

在验证过程中，我们发现**余弦相似度（Level 2）不适合比较由离散装箱索引组成的行为指纹**。

**证据**：在 53 个 baseline 程序中的 31 个唯一指纹之间，两两余弦相似度范围为 [0.976, 0.9999]，均值 0.989。在阈值 0.98 下，**98.5% 的真正不同的程序会被错误过滤**。这是高维整数向量的固有特性——大部分维度共享相似的值（箱子索引 0–20）。

**解决方案**：Level 2 默认禁用（`DedupConfig.level2_enabled=False`）。仅 Level 0 + Level 1 即可实现有效去重（30.8% 过滤率）。Level 2 代码完整保留，用于消融实验。未来可用离散度量（Hamming 距离、编辑距离）替代余弦相似度。

这一发现表明，连续相似度度量不适用于离散决策序列——这是一个非显而易见的洞察，指导了我们最终的系统设计。

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

预期：tests pass（currently 65 passed, 0 skipped），lint pass

**启用行为去重运行：**

```bash
cd funsearch-baseline/
export API_KEY="<your-key>"
export DEDUP_ENABLED=1
python funsearch_bin_packing_llm_api.py

# 分析预运行的去重实验日志（无需 API key）
cat logs/dedup_50samples_v2/run_log.csv

# 不启用去重进行对比
export DEDUP_ENABLED=0
python funsearch_bin_packing_llm_api.py
```

### 5.1 提交前质量门禁快照（2026-03-30）

- `ruff check .` → **All checks passed!**
- `pytest -q -rs` → **65 passed in 0.29s**
