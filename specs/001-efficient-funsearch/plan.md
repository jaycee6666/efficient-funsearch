# Behavioral Deduplication + Diversity Selection Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将当前 v0 风格的“embedding+AST 主线”实现，升级为与最新 spec 对齐的 v1 双机制主线（行为去重 + 多样性引导选择），并补齐可验证的指标与消融实验。

**Architecture:** 先在候选进入完整评估前进行行为探测，基于 5–15 个探测样例生成行为指纹并做相似性过滤；再在候选选择阶段引入“性能 + 多样性”联合评分，避免搜索过早塌缩。指标层统一记录 `η = N_unique / N_total`、重复检测率、收敛速度与最终装箱质量，并用四组基线/消融进行对比。

**Tech Stack:** Python 3.10+, pytest, ruff, existing src/* modules (normalizer/similarity/archive/integration/metrics)

## Task Reference Alignment (with tasks.md)

为避免 `plan.md` 的“Task 1..8”与 `tasks.md` 的 `T001..T035` 编号歧义，建立如下对齐关系：

- Plan Task 1 → `T004~T006`（并与 `T005` 联动）
- Plan Task 2 → `T008` + `T012`
- Plan Task 3 → `T009` + `T013` + `T016`
- Plan Task 4 → `T010` + `T011` + `T014` + `T015`
- Plan Task 5 → `T017` + `T018` + `T019` + `T020` + `T021`
- Plan Task 6 → `T022` + `T025` + `T027`
- Plan Task 7 → `T023` + `T026`
- Plan Task 8 → `T024` + `T028` + `T029` + `T030`

Phase/执行收口项：

- Setup: `T001~T003`
- Foundational补充: `T007`
- Polish & Cross-Cutting: `T031~T035`

---

### Task 1: 引入 v1 配置与数据模型（行为指纹/多样性）

**Files:**
- Modify: `src/config.py`
- Modify: `src/similarity/models.py`
- Test: `tests/unit/test_similarity_models.py` (Create)

**Step 1: Write the failing test**

```python
from src.similarity.models import DetectorConfig


def test_detector_config_supports_behavioral_and_diversity_fields():
    cfg = DetectorConfig()
    assert cfg.behavior_probe_count_min == 5
    assert cfg.behavior_probe_count_max == 15
    assert cfg.behavior_similarity_threshold == 0.95
    assert 0.0 <= cfg.diversity_weight <= 1.0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_similarity_models.py::test_detector_config_supports_behavioral_and_diversity_fields -v`  
Expected: FAIL with missing attributes in `DetectorConfig`

**Step 3: Write minimal implementation**

```python
@dataclass
class DetectorConfig:
    behavior_probe_count_min: int = 5
    behavior_probe_count_max: int = 15
    behavior_similarity_threshold: float = 0.95
    diversity_weight: float = 0.2
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_similarity_models.py::test_detector_config_supports_behavioral_and_diversity_fields -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add tests/unit/test_similarity_models.py src/similarity/models.py src/config.py
git commit -m "feat: add v1 behavioral and diversity config fields"
```

---

### Task 2: 实现行为探测与行为指纹构建

**Files:**
- Create: `src/similarity/behavioral_probe.py`
- Test: `tests/unit/test_behavioral_probe.py` (Create)

**Step 1: Write the failing test**

```python
from src.similarity.behavioral_probe import build_behavior_fingerprint


def test_build_behavior_fingerprint_returns_stable_signature():
    code = "def solve(x): return x + 1"
    probes = [1, 2, 3, 4, 5]
    sig1 = build_behavior_fingerprint(code, probes)
    sig2 = build_behavior_fingerprint(code, probes)
    assert sig1 == sig2
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_behavioral_probe.py::test_build_behavior_fingerprint_returns_stable_signature -v`  
Expected: FAIL with module/function not found

**Step 3: Write minimal implementation**

```python
def build_behavior_fingerprint(source_code: str, probes: list[object]) -> list[str]:
    # 最小实现：基于可执行结果序列构建稳定指纹
    return [str(p) for p in probes]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_behavioral_probe.py::test_build_behavior_fingerprint_returns_stable_signature -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add tests/unit/test_behavioral_probe.py src/similarity/behavioral_probe.py
git commit -m "feat: add behavioral probing fingerprint builder"
```

---

### Task 3: 用行为相似度替代主线混合检测

**Files:**
- Modify: `src/similarity/hybrid.py`
- Modify: `src/similarity/__init__.py`
- Test: `tests/unit/test_hybrid_detector.py`

**Step 1: Write the failing test**

```python
def test_behavior_similarity_threshold_applied_for_duplicate_decision():
    from src.similarity.hybrid import HybridSimilarityDetector
    detector = HybridSimilarityDetector()
    score = detector.compute_behavior_similarity(["1","2"], ["1","2"])
    assert score > 0.95
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_hybrid_detector.py::test_behavior_similarity_threshold_applied_for_duplicate_decision -v`  
Expected: FAIL with missing `compute_behavior_similarity`

**Step 3: Write minimal implementation**

```python
def compute_behavior_similarity(self, fp_a: list[str], fp_b: list[str]) -> float:
    # 最小实现：相同位置一致比例
    if not fp_a or not fp_b:
        return 0.0
    n = min(len(fp_a), len(fp_b))
    return sum(1 for i in range(n) if fp_a[i] == fp_b[i]) / n
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_hybrid_detector.py::test_behavior_similarity_threshold_applied_for_duplicate_decision -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add tests/unit/test_hybrid_detector.py src/similarity/hybrid.py src/similarity/__init__.py
git commit -m "refactor: switch duplicate decision to behavioral similarity mainline"
```

---

### Task 4: 在 Adapter 中接入“先行为去重后评估”流程

**Files:**
- Modify: `src/integration/funsearch_adapter.py`
- Modify: `src/archive/program_archive.py`
- Test: `tests/integration/test_funsearch_adapter.py`

**Step 1: Write the failing test**

```python
def test_adapter_filters_behavioral_duplicates_before_evaluation(monkeypatch):
    from src.integration.funsearch_adapter import FunSearchAdapter
    adapter = FunSearchAdapter()
    code_a = "def solve(x): return x+1"
    code_b = "def solve(y): return y+1"
    assert adapter.record_result(code_a, 1.0) is True
    assert adapter.record_result(code_b, 2.0) is False
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_funsearch_adapter.py::test_adapter_filters_behavioral_duplicates_before_evaluation -v`  
Expected: FAIL because second candidate is not yet treated as behavioral duplicate

**Step 3: Write minimal implementation**

```python
# in record_result / is_duplicate
# 1) build behavioral fingerprint
# 2) compare with archive fingerprints
# 3) filter when similarity > config.behavior_similarity_threshold
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_funsearch_adapter.py::test_adapter_filters_behavioral_duplicates_before_evaluation -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add tests/integration/test_funsearch_adapter.py src/integration/funsearch_adapter.py src/archive/program_archive.py
git commit -m "feat: enforce behavioral dedup before full evaluation"
```

---

### Task 5: 引入多样性引导选择评分

**Files:**
- Modify: `src/integration/funsearch_adapter.py`
- Create: `src/similarity/diversity.py`
- Test: `tests/unit/test_diversity_selection.py` (Create)

**Step 1: Write the failing test**

```python
from src.similarity.diversity import rank_candidates


def test_rank_candidates_combines_performance_and_diversity():
    ranked = rank_candidates(
        candidates=["a", "b"],
        perf_scores={"a": 0.8, "b": 0.79},
        diversity_scores={"a": 0.1, "b": 0.6},
        beta=0.2,
    )
    assert ranked[0] == "b"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_diversity_selection.py::test_rank_candidates_combines_performance_and_diversity -v`  
Expected: FAIL with module/function not found

**Step 3: Write minimal implementation**

```python
def rank_candidates(candidates, perf_scores, diversity_scores, beta=0.2):
    return sorted(
        candidates,
        key=lambda c: perf_scores[c] + beta * diversity_scores[c],
        reverse=True,
    )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_diversity_selection.py::test_rank_candidates_combines_performance_and_diversity -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add tests/unit/test_diversity_selection.py src/similarity/diversity.py src/integration/funsearch_adapter.py
git commit -m "feat: add diversity-guided candidate ranking"
```

---

### Task 6: 指标体系升级到 v1（η + 四类指标）

**Files:**
- Modify: `src/metrics/models.py`
- Modify: `src/metrics/efficiency_logger.py`
- Test: `tests/unit/test_metrics.py` (Create)

**Step 1: Write the failing test**

```python
from src.metrics.models import EfficiencyMetrics


def test_sample_efficiency_eta_computed_from_unique_over_total():
    m = EfficiencyMetrics(total_programs_generated=10, programs_evaluated=4)
    assert m.sample_efficiency == 0.4
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_metrics.py::test_sample_efficiency_eta_computed_from_unique_over_total -v`  
Expected: FAIL with missing `sample_efficiency`

**Step 3: Write minimal implementation**

```python
@property
def sample_efficiency(self) -> float:
    if self.total_programs_generated == 0:
        return 0.0
    return self.programs_evaluated / self.total_programs_generated
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_metrics.py::test_sample_efficiency_eta_computed_from_unique_over_total -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add tests/unit/test_metrics.py src/metrics/models.py src/metrics/efficiency_logger.py
git commit -m "feat: add v1 sample efficiency and metric reporting"
```

---

### Task 7: 固化四组基线/消融实验配置

**Files:**
- Create: `src/integration/ablation_configs.py`
- Test: `tests/integration/test_ablation_configs.py` (Create)

**Step 1: Write the failing test**

```python
from src.integration.ablation_configs import get_v1_ablation_configs


def test_v1_ablation_configs_have_four_required_variants():
    names = [c.name for c in get_v1_ablation_configs()]
    assert names == [
        "original",
        "exact_string_match",
        "normalized_hash_only",
        "behavioral_plus_diversity",
    ]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_ablation_configs.py::test_v1_ablation_configs_have_four_required_variants -v`  
Expected: FAIL with module/function not found

**Step 3: Write minimal implementation**

```python
def get_v1_ablation_configs():
    return [
        AblationConfig(name="original"),
        AblationConfig(name="exact_string_match"),
        AblationConfig(name="normalized_hash_only"),
        AblationConfig(name="behavioral_plus_diversity"),
    ]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_ablation_configs.py::test_v1_ablation_configs_have_four_required_variants -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add tests/integration/test_ablation_configs.py src/integration/ablation_configs.py
git commit -m "feat: define proposal-v1 ablation baselines"
```

---

### Task 8: 端到端验证与文档对齐

**Files:**
- Modify: `specs/001-efficient-funsearch/tasks.md`
- Modify: `specs/001-efficient-funsearch/contracts/detector.md`
- Modify: `specs/001-efficient-funsearch/data-model.md`
- Modify: `specs/001-efficient-funsearch/quickstart.md`

**Step 1: Write the failing test**

```python
def test_documentation_mentions_behavioral_and_diversity_mainline():
    # 文档一致性检查脚本应在此断言关键短语
    assert False
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_doc_alignment.py::test_documentation_mentions_behavioral_and_diversity_mainline -v`  
Expected: FAIL (占位)

**Step 3: Write minimal implementation**

```python
# 新增 tests/integration/test_doc_alignment.py
# 读取 docs/spec artifacts 并断言：
# - 包含 behavioral dedup + diversity-guided selection
# - 不把 embedding+AST 写作主线
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_doc_alignment.py -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add specs/001-efficient-funsearch/tasks.md specs/001-efficient-funsearch/contracts/detector.md specs/001-efficient-funsearch/data-model.md specs/001-efficient-funsearch/quickstart.md tests/integration/test_doc_alignment.py
git commit -m "docs: align contracts and tasks with v1 behavioral+density plan"
```

---

## Verification Checklist (must pass before merge)

1. `pytest tests/unit -v` 全通过
2. `pytest tests/integration -v` 全通过
3. `pytest -v` 全通过
4. `ruff check .` 通过
5. `python -m pytest tests/integration/test_ablation_configs.py -v` 覆盖四组基线
6. 指标输出包含：`sample_efficiency`、`duplicate_detection_rate`、`convergence`、`final_quality`

---

## Requirement Traceability (Spec → Plan)

- **FR-001/FR-002** → Task 3 + Task 4
- **FR-003** → Task 6
- **FR-004/FR-005** → Task 2 + Task 3
- **FR-006** → Task 5
- **FR-007/FR-008** → Task 6 + Task 7
- **FR-009/FR-010** → Task 8
- **AC-001..AC-005** → Task 3/4/6/7/8 的测试与文档一致性检查
- **SC-002..SC-004** → Task 6 + Task 7 + Verification Checklist

---

## Execution Notes & Traceability (T035)

本轮按 `tasks.md` 顺序逐任务执行，且每个阶段均执行“先失败测试 → 实现 → 回归验证”：

- Phase 1/2（T001~T007）已完成，配置字段与基础夹具已就绪。
- US1（T008~T016）已完成：行为指纹、行为相似度、Archive 行为去重、Adapter 预评估过滤与导出均已落地。
- US2（T017~T021）已完成：多样性排序、选择路径与选择元数据记录已落地。
- US3（T022~T030）已完成：样本效率 η 指标、四组消融配置注册、文档一致性校验已落地。

关键验证记录（可复现命令）：

- `pytest tests/unit/test_similarity_models.py -v`
- `pytest tests/unit/test_behavioral_probe.py::test_build_behavior_fingerprint_returns_stable_signature -v`
- `pytest tests/unit/test_hybrid_detector.py::test_behavior_similarity_threshold_applied_for_duplicate_decision -v`
- `pytest tests/unit/test_archive.py::TestProgramArchive::test_behavioral_duplicate_detection -v`
- `pytest tests/unit/test_diversity_selection.py::test_rank_candidates_combines_performance_and_diversity -v`
- `pytest tests/unit/test_metrics.py::test_sample_efficiency_eta_computed_from_unique_over_total -v`
- `pytest tests/integration/test_funsearch_adapter.py::TestFunSearchAdapter::test_adapter_filters_behavioral_duplicates_before_evaluation -v`
- `pytest tests/integration/test_funsearch_adapter.py::TestFunSearchAdapter::test_adapter_selection_path_uses_diversity_ranking -v`
- `pytest tests/integration/test_ablation_configs.py::test_v1_ablation_configs_have_four_required_variants -v`
- `pytest tests/integration/test_doc_alignment.py::test_documentation_mentions_behavioral_and_diversity_mainline -v`

Phase 6 收口（T031~T034）在最终交付前统一执行完整 unit / integration / full-suite 与 lint。

风险收敛补充（后续执行约束）：

- 环境一致性：本地与 CI 统一使用 Python 3.9 解释器与工具链目标（pyproject 已对齐）。
- 依赖隔离：对 `sentence-transformers` 的单测覆盖采用 monkeypatch 方式，避免因外部依赖缺失导致主线跳测。
- 变更范围控制：提交前执行 `git diff --name-only` 审核，仅保留本任务相关文件；文档/笔记本改动按需独立处理。
