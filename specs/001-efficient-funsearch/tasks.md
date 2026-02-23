# Tasks: Efficient FunSearch

**Input**: Design documents from `/specs/001-efficient-funsearch/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: 按照 TDD 原则，每个功能模块先写测试。

**Organization**: 任务按用户故事组织，每个故事可独立实现和测试。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行执行（不同文件，无依赖）
- **[Story]**: 所属用户故事（US1, US2, US3, US4）
- 描述中包含精确文件路径

---

## Phase 1: Setup（项目初始化）

**Purpose**: 项目结构创建和基础配置

- [ ] T001 创建项目目录结构：src/, tests/, notebooks/
- [ ] T002 初始化 Python 项目：pyproject.toml, requirements.txt
- [ ] T003 [P] 配置 pytest 测试框架在 tests/conftest.py
- [ ] T004 [P] 配置 ruff/black 代码格式化工具
- [ ] T005 [P] 创建 src/__init__.py 导出公共 API
- [ ] T006 创建测试固件 tests/fixtures/sample_programs.py（示例程序数据）

**Checkpoint**: 项目结构就绪，可以开始开发

---

## Phase 2: Foundational（阻塞前置任务）

**Purpose**: 所有用户故事依赖的核心基础设施

**⚠️ CRITICAL**: 用户故事实现必须等待此阶段完成

### 数据模型（所有故事共享）

- [ ] T007 [P] 创建 NormalizedProgram 数据类在 src/normalizer/models.py
- [ ] T008 [P] 创建 Program 数据类在 src/archive/models.py
- [ ] T009 [P] 创建 SimilarityResult 数据类在 src/similarity/models.py
- [ ] T010 [P] 创建 EfficiencyMetrics 数据类在 src/metrics/models.py
- [ ] T011 创建 ArchiveConfig 和 DetectorConfig 配置类在 src/config.py

### 测试固件

- [ ] T012 [P] 创建程序标准化测试固件在 tests/fixtures/normalizer_fixtures.py
- [ ] T013 [P] 创建相似度检测测试固件在 tests/fixtures/similarity_fixtures.py
- [ ] T014 [P] 创建存档测试固件在 tests/fixtures/archive_fixtures.py

**Checkpoint**: 基础模型就绪，用户故事可并行开始

---

## Phase 3: User Story 1 - 运行带重复检测的 FunSearch (Priority: P1) 🎯 MVP

**Goal**: 实现核心功能 - 自动检测并过滤功能重复的程序

**Independent Test**: 运行带和不带重复检测的 FunSearch，比较评估的唯一程序数量

### Tests for User Story 1 (TDD)

- [ ] T015 [P] [US1] 单元测试：代码标准化在 tests/unit/test_normalizer.py
- [ ] T016 [P] [US1] 单元测试：变量重命名在 tests/unit/test_variable_renamer.py
- [ ] T017 [P] [US1] 单元测试：嵌入相似度计算在 tests/unit/test_embedding.py
- [ ] T018 [P] [US1] 单元测试：AST 相似度比较在 tests/unit/test_ast_compare.py
- [ ] T019 [P] [US1] 单元测试：混合检测器在 tests/unit/test_hybrid_detector.py
- [ ] T020 [P] [US1] 单元测试：程序存档在 tests/unit/test_archive.py
- [ ] T021 [US1] 集成测试：FunSearch 适配器在 tests/integration/test_funsearch_adapter.py

### Implementation for User Story 1

#### 代码标准化模块

- [ ] T022 [P] [US1] 实现 VariableRenamer AST 转换器在 src/normalizer/variable_renamer.py
- [ ] T023 [P] [US1] 实现文档字符串移除在 src/normalizer/ast_normalizer.py
- [ ] T024 [US1] 实现 ProgramNormalizer 主类在 src/normalizer/ast_normalizer.py
- [ ] T025 [US1] 创建 src/normalizer/__init__.py 导出公共接口

#### 相似度检测模块

- [ ] T026 [P] [US1] 实现代码嵌入计算在 src/similarity/embedding.py
- [ ] T027 [P] [US1] 实现 AST 结构比较在 src/similarity/ast_compare.py
- [ ] T028 [US1] 实现 HybridSimilarityDetector 主类在 src/similarity/hybrid.py
- [ ] T029 [US1] 创建 src/similarity/__init__.py 导出公共接口

#### 程序存档模块

- [ ] T030 [P] [US1] 实现哈希存储在 src/archive/hash_store.py
- [ ] T031 [US1] 实现 ProgramArchive 主类在 src/archive/program_archive.py
- [ ] T032 [US1] 创建 src/archive/__init__.py 导出公共接口

#### FunSearch 集成

- [ ] T033 [US1] 实现 FunSearchAdapter 适配器在 src/integration/funsearch_adapter.py
- [ ] T034 [US1] 创建 src/integration/__init__.py 导出公共接口

**Checkpoint**: User Story 1 完成，核心重复检测功能可用

---

## Phase 4: User Story 2 - 评估样本效率改进 (Priority: P2)

**Goal**: 衡量重复检测对 FunSearch 效率的改进

**Independent Test**: 运行实验，比较 LLM 查询次数和收敛速度

### Tests for User Story 2 (TDD)

- [ ] T035 [P] [US2] 单元测试：效率追踪器在 tests/unit/test_efficiency_logger.py
- [ ] T036 [US2] 集成测试：完整实验流程在 tests/integration/test_experiment.py

### Implementation for User Story 2

- [ ] T037 [US2] 实现 EfficiencyTracker 效率追踪器在 src/metrics/efficiency_logger.py
- [ ] T038 [US2] 实现 ExperimentRunner 实验运行器在 src/experiments/runner.py
- [ ] T039 [US2] 实现 ResultAnalyzer 结果分析器在 src/experiments/analyzer.py
- [ ] T040 [US2] 创建 src/metrics/__init__.py 导出公共接口

**Checkpoint**: User Story 2 完成，可测量效率改进

---

## Phase 5: User Story 3 - 保持解决方案质量 (Priority: P3)

**Goal**: 确保重复检测不过滤有价值的程序

**Independent Test**: 比较原始版和增强版 FunSearch 的最终解决方案质量

### Tests for User Story 3 (TDD)

- [ ] T041 [P] [US3] 测试：语义不同但语法相似的程序在 tests/unit/test_quality_preservation.py
- [ ] T042 [US3] 集成测试：质量对比实验在 tests/integration/test_quality_comparison.py

### Implementation for User Story 3

- [ ] T043 [US3] 实现质量保证检查器在 src/quality/checker.py
- [ ] T044 [US3] 实现阈值调优器在 src/quality/threshold_tuner.py
- [ ] T045 [US3] 创建 src/quality/__init__.py 导出公共接口

**Checkpoint**: User Story 3 完成，解决方案质量有保障

---

## Phase 6: User Story 4 - 准备课程提交物 (Priority: P2)

**Goal**: 按要求格式准备所有里程碑交付物

**Independent Test**: 验证每个交付物符合提交要求

### Implementation for User Story 4

- [ ] T046 [P] [US4] 准备 ICLR '24 格式提案模板在 docs/proposal/
- [ ] T047 [P] [US4] 创建项目提案文档（1页）在 docs/proposal/proposal.pdf
- [ ] T048 [US4] 准备里程碑报告草稿在 docs/milestone/report_draft.pdf
- [ ] T049 [US4] 准备里程碑代码（带初步结果）在 milestone/
- [ ] T050 [US4] 创建 Google Colab Notebook 在 notebooks/efficient_funsearch.ipynb
- [ ] T051 [US4] 准备最终报告（4-6页）在 docs/final_report/report.pdf

**Checkpoint**: User Story 4 完成，所有交付物就绪

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: 改进和优化

- [ ] T052 [P] 添加类型注解到所有模块
- [ ] T053 [P] 完善 docstrings 和代码注释
- [ ] T054 性能优化：嵌入计算缓存
- [ ] T055 [P] 性能优化：批量检测并行化
- [ ] T056 添加错误处理和边界情况处理
- [ ] T057 创建 README.md 使用说明
- [ ] T058 运行 quickstart.md 验证流程
- [ ] T059 代码清理和重构

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 无依赖 - 立即开始
- **Foundational (Phase 2)**: 依赖 Setup 完成 - 阻塞所有用户故事
- **User Stories (Phase 3-6)**: 都依赖 Foundational 完成
  - US1 可独立开始
  - US2 依赖 US1 的核心模块（用于实验）
  - US3 依赖 US1 的检测器（用于质量检查）
  - US4 可与 US1-3 并行（文档工作）
- **Polish (Phase 7)**: 依赖所需用户故事完成

### User Story Dependencies

- **User Story 1 (P1)**: Foundational 后可开始 - 无其他故事依赖
- **User Story 2 (P2)**: 依赖 US1 核心模块用于实验
- **User Story 3 (P3)**: 依赖 US1 检测器用于质量验证
- **User Story 4 (P2)**: 可与 US1-3 并行进行

### Within Each User Story

- 测试先行（TDD）：测试必须先失败再实现
- 模型 → 服务 → 集成
- 核心实现 → 边界处理

### Parallel Opportunities

- Setup 阶段所有 [P] 任务可并行
- Foundational 阶段所有 [P] 任务可并行
- US1 内的测试可并行编写
- US1 内各模块可并行开发（normalizer, similarity, archive）
- US4 可与其他用户故事并行

---

## Parallel Example: User Story 1

```bash
# 并行运行所有 US1 测试：
Task T015: "单元测试：代码标准化"
Task T016: "单元测试：变量重命名"
Task T017: "单元测试：嵌入相似度计算"
Task T018: "单元测试：AST 相似度比较"
Task T019: "单元测试：混合检测器"
Task T020: "单元测试：程序存档"

# 并行开发各模块：
Task T022-T025: "normalizer 模块"
Task T026-T029: "similarity 模块"
Task T030-T032: "archive 模块"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. 完成 Phase 1: Setup
2. 完成 Phase 2: Foundational
3. 完成 Phase 3: User Story 1
4. **停止并验证**: 独立测试 User Story 1
5. 如果需要，可演示 MVP

### Incremental Delivery

1. Setup + Foundational → 基础就绪
2. 添加 US1 → 独立测试 → MVP 完成
3. 添加 US2 → 独立测试 → 可展示效率改进
4. 添加 US3 → 独立测试 → 质量保证完成
5. 添加 US4 → 所有交付物就绪
6. Polish → 最终优化

### 课程里程碑对齐

| 课程里程碑 | 截止日期 | 对应任务 |
|-----------|----------|----------|
| Project Proposal | Feb 24, 2026 | T046-T047 |
| Project Milestone | Mar 31, 2026 | T001-T049 (US1-3 + 初步结果) |
| Final Project | Apr 26, 2026 | T001-T059 (全部完成) |

---

## Notes

- [P] 任务 = 不同文件，无依赖
- [Story] 标签将任务映射到特定用户故事
- 每个用户故事应独立完成和测试
- 测试先失败再实现（TDD）
- 每个任务或逻辑组完成后提交
- 在任何检查点停止以独立验证故事
- 避免：模糊任务、同文件冲突、破坏独立性的跨故事依赖
