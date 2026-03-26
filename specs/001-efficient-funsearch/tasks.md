# Tasks: Behavioral Deduplication and Diversity-Guided Selection

**Input**: Design documents from `/specs/001-efficient-funsearch/`  
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: 本特性在 plan.md 中明确采用 TDD，因此每个用户故事均包含先失败后实现的测试任务。  
**Organization**: 任务按用户故事组织，保证每个故事可独立实现与独立验证。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行执行（不同文件、无未完成依赖）
- **[Story]**: 所属用户故事标签（US1, US2, US3）
- 所有任务描述均包含精确文件路径

---

## Phase 1: Setup（项目初始化）

**Purpose**: 同步 v1 规格后的任务基线，准备开发与测试入口。

- [x] T001 Update module export baseline in src/__init__.py
- [x] T002 [P] Verify pytest/running config in tests/conftest.py
- [x] T003 [P] Align feature-level task references in specs/001-efficient-funsearch/plan.md

---

## Phase 2: Foundational（阻塞前置）

**Purpose**: 建立所有用户故事共享的配置与模型基础。  
**⚠️ CRITICAL**: 本阶段完成前，不开始任何用户故事实现。

- [x] T004 [P] Add v1 behavioral config fields in src/similarity/models.py
- [x] T005 [P] Add aligned archive/detector config defaults in src/config.py
- [x] T006 [P] Create config model tests in tests/unit/test_similarity_models.py
- [x] T007 Add foundational fixture support for behavioral probes in tests/fixtures/sample_programs.py

**Checkpoint**: v1 配置字段（probe 范围、行为阈值、多样性权重）可被测试读取。

---

## Phase 3: User Story 1 - 去除行为重复候选 (Priority: P1) 🎯 MVP

**Goal**: 在完整评估前识别并过滤行为重复候选，降低冗余评估。  
**Independent Test**: 固定迭代预算下，对比无去重/行为去重流程，验证完整评估候选数量明显下降。

### Tests for User Story 1 (TDD)

- [x] T008 [P] [US1] Add behavioral fingerprint stability test in tests/unit/test_behavioral_probe.py
- [x] T009 [P] [US1] Add behavior similarity threshold test in tests/unit/test_hybrid_detector.py
- [x] T010 [P] [US1] Add duplicate archive behavior test in tests/unit/test_archive.py
- [x] T011 [US1] Add adapter pre-evaluation filtering integration test in tests/integration/test_funsearch_adapter.py

### Implementation for User Story 1

- [x] T012 [P] [US1] Implement behavioral probe builder in src/similarity/behavioral_probe.py
- [x] T013 [P] [US1] Implement behavior similarity computation in src/similarity/hybrid.py
- [x] T014 [US1] Integrate behavioral duplicate decision path in src/archive/program_archive.py
- [x] T015 [US1] Enforce pre-evaluation behavioral filtering in src/integration/funsearch_adapter.py
- [x] T016 [US1] Export behavioral dedup interfaces in src/similarity/__init__.py

**Checkpoint**: 满足 FR-001/FR-002/FR-004/FR-005 与 AC-001/AC-003。

---

## Phase 4: User Story 2 - 维持探索多样性 (Priority: P2)

**Goal**: 在候选选择中联合考虑性能与多样性，避免策略塌缩。  
**Independent Test**: 同预算下比较“仅性能”与“性能+多样性”，后者保留更多差异化候选。

### Tests for User Story 2 (TDD)

- [x] T017 [P] [US2] Add combined ranking unit test in tests/unit/test_diversity_selection.py
- [x] T018 [US2] Add selection-path integration test in tests/integration/test_funsearch_adapter.py

### Implementation for User Story 2

- [x] T019 [P] [US2] Implement diversity ranking utility in src/similarity/diversity.py
- [x] T020 [US2] Integrate performance+diversity scoring in src/integration/funsearch_adapter.py
- [x] T021 [US2] Record selection metadata for analysis in src/metrics/efficiency_logger.py

**Checkpoint**: 满足 FR-006 与 AC-004（联合选择原则部分）。

---

## Phase 5: User Story 3 - 用统一口径完成评估与消融 (Priority: P3)

**Goal**: 将指标与消融配置对齐 proposal_v1，确保实验可复现、可比。  
**Independent Test**: 根据 tasks 执行后生成实验配置，覆盖四项指标与四组基线/消融。

### Tests for User Story 3 (TDD)

- [x] T022 [P] [US3] Add sample efficiency formula test in tests/unit/test_metrics.py
- [x] T023 [P] [US3] Add required ablation variants test in tests/integration/test_ablation_configs.py
- [x] T024 [US3] Add docs alignment integration test in tests/integration/test_doc_alignment.py

### Implementation for User Story 3

- [x] T025 [P] [US3] Implement sample efficiency property in src/metrics/models.py
- [x] T026 [US3] Implement v1 ablation config registry in src/integration/ablation_configs.py
- [x] T027 [US3] Update experiment metric emission in src/metrics/efficiency_logger.py
- [x] T028 [US3] Align detector contract doc for v1 in specs/001-efficient-funsearch/contracts/detector.md
- [x] T029 [US3] Align data model doc for behavioral entities in specs/001-efficient-funsearch/data-model.md
- [x] T030 [US3] Align quickstart usage to v1 flow in specs/001-efficient-funsearch/quickstart.md

**Checkpoint**: 满足 FR-003/FR-007/FR-008/FR-009/FR-010 与 AC-002/AC-004/AC-005。

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 整体验证、文档一致性、发布前收口。

- [ ] T031 [P] Run full unit suite for feature modules in tests/unit/
- [ ] T032 [P] Run full integration suite for feature flows in tests/integration/
- [ ] T033 Run end-to-end test command in repository root with pytest -v
- [ ] T034 [P] Run lint verification with ruff check .
- [ ] T035 Update final execution notes and traceability in specs/001-efficient-funsearch/plan.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: 无依赖，可立即开始
- **Phase 2 (Foundational)**: 依赖 Phase 1，阻塞所有用户故事
- **Phase 3 (US1)**: 依赖 Phase 2，MVP 主线
- **Phase 4 (US2)**: 依赖 US1 的过滤与适配器能力
- **Phase 5 (US3)**: 依赖 US1+US2 的实现结果用于统一评估
- **Phase 6 (Polish)**: 依赖目标用户故事完成

### User Story Dependencies

- **US1 (P1)**: 独立起步故事，完成后可演示 MVP
- **US2 (P2)**: 依赖 US1 的候选流转路径
- **US3 (P3)**: 依赖 US1/US2 输出以完成指标与消融闭环

### Within Each User Story

- 测试任务先执行并应先失败
- 模块实现后立即回跑对应测试
- 故事检查点通过后再进入下一个故事

---

## Parallel Execution Examples

### User Story 1

```bash
# Parallel test authoring
T008 tests/unit/test_behavioral_probe.py
T009 tests/unit/test_hybrid_detector.py
T010 tests/unit/test_archive.py

# Parallel implementation across distinct files
T012 src/similarity/behavioral_probe.py
T013 src/similarity/hybrid.py
```

### User Story 2

```bash
# Parallelizable pair
T017 tests/unit/test_diversity_selection.py
T019 src/similarity/diversity.py
```

### User Story 3

```bash
# Parallel doc+code updates
T025 src/metrics/models.py
T028 specs/001-efficient-funsearch/contracts/detector.md
T029 specs/001-efficient-funsearch/data-model.md
```

---

## Implementation Strategy

### MVP First

1. 完成 Phase 1 + Phase 2
2. 完成 Phase 3 (US1)
3. 执行 US1 独立验证（行为去重有效）

### Incremental Delivery

1. US1 交付行为去重主路径
2. US2 增量交付多样性选择
3. US3 完成交付口径统一（指标+消融）

### Suggested MVP Scope

- **仅 US1 (Phase 3)** 为最小可交付范围；可证明 v1 主线中的“行为去重”已生效。

---

## Notes

- 所有任务已遵循严格 checklist 格式：`- [ ] Txxx [P] [USx] 描述 + 文件路径`
- 任务组织已按用户故事优先级（P1 → P2 → P3）
- 每个用户故事均包含独立测试标准与检查点
