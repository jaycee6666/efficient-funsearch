# Feature Specification: Behavioral Deduplication and Diversity-Guided Selection for Sample-Efficient FunSearch

**Feature Branch**: `001-efficient-funsearch`  
**Created**: 2026-02-23  
**Updated**: 2026-03-26  
**Status**: Draft  
**Input**: proposal aligned to `proposal_v1.tex`

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 去除行为重复候选 (Priority: P1)

作为项目成员，我希望在完整评估前识别并剔除行为上等价的候选程序，以减少冗余评估与无效 API 调用。

**Why this priority**: 这是提升样本效率的首要能力，直接决定资源消耗与迭代速度。

**Independent Test**: 固定迭代次数下，对比“无去重”和“行为去重”流程，验证被完整评估的重复候选显著减少。

**Acceptance Scenarios**:

1. **Given** 生成了一批新候选程序，**When** 执行行为探测，**Then** 行为指纹高度相似的候选会在完整评估前被剔除。
2. **Given** 候选仅在变量命名或表面形式不同，**When** 进行标准化和行为对比，**Then** 它们会被识别为重复行为候选。

---

### User Story 2 - 维持探索多样性 (Priority: P2)

作为项目成员，我希望候选选择同时考虑性能与多样性，避免搜索过早陷入单一策略。

**Why this priority**: 仅做去重会降低冗余，但不能保证持续探索新策略；多样性引导用于补足这一点。

**Independent Test**: 在相同预算下，对比“仅性能选择”和“性能+多样性选择”，验证后者保留更多差异化候选策略。

**Acceptance Scenarios**:

1. **Given** 两个候选性能接近，**When** 执行选择，**Then** 多样性更高的候选可获得更高综合优先级。
2. **Given** 搜索进入中后期，**When** 应用多样性引导，**Then** 候选策略不会快速塌缩到单一路径。

---

### User Story 3 - 用统一口径完成评估与消融 (Priority: P3)

作为项目成员，我希望评估指标与基线/消融设计和 proposal_v1 一致，以便结果可直接用于里程碑和最终报告。

**Why this priority**: 评估口径不一致会导致结论不可比，影响项目交付可信度。

**Independent Test**: 根据 spec 生成实验清单，检查指标与基线项是否完整覆盖 proposal_v1 要求。

**Acceptance Scenarios**:

1. **Given** 需要制定实验计划，**When** 参考 spec，**Then** 指标包含样本效率、重复检测率、收敛速度与最终装箱质量。
2. **Given** 需要设计消融，**When** 参考 spec，**Then** 基线集合完整覆盖 proposal_v1 定义的四组配置。

---

### Edge Cases

- 行为探测样本较少时，需避免误删潜在高质量但边界行为不同的候选。
- 搜索早期候选数量不足时，多样性引导不应过度削弱基本性能导向。
- 候选大量相似时，流程必须保持“先去重后完整评估”的顺序一致性。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系统 MUST 采用“行为去重 + 多样性引导选择”的双机制作为主线框架。
- **FR-002**: 系统 MUST 在完整评估前执行行为去重流程，减少冗余候选进入高成本评估。
- **FR-003**: 系统 MUST 将样本效率定义为 `η = N_unique / N_total` 并按该口径统计实验结果。
- **FR-004**: 系统 MUST 使用 5–15 个覆盖边界情况的探测实例构建候选行为指纹。
- **FR-005**: 系统 MUST 将行为指纹高相似候选（阈值 > 0.95）判定为重复并过滤。
- **FR-006**: 系统 MUST 在候选选择时同时考虑性能与多样性贡献，并支持既定的多样性权重设置。
- **FR-007**: 系统 MUST 采用 proposal_v1 的评估指标集合：样本效率相关 API 调用、重复检测率、收敛速度、最终装箱质量。
- **FR-008**: 系统 MUST 采用 proposal_v1 的基线/消融集合：原始方法、精确字符串匹配、标准化+仅哈希去重、双机制组合。
- **FR-009**: 规范 MUST 移除 v0 中“混合相似度（嵌入+AST）作为主线”的描述，避免与 v1 冲突。
- **FR-010**: 文档 MUST 保持技术无关表述，聚焦需求与验收结果，不绑定具体实现技术栈。

### Functional Requirement Acceptance Criteria

- **AC-001 (FR-001/FR-002)**: 评审可从规范中明确识别双机制主线，且流程顺序为“行为去重 → 完整评估”。
- **AC-002 (FR-003/FR-007)**: 评估章节明确列出 η 定义与四项指标，无缺失项。
- **AC-003 (FR-004/FR-005)**: 规范中明确行为探测规模（5–15）与重复判定阈值（>0.95）。
- **AC-004 (FR-006/FR-008)**: 规范中明确性能+多样性联合选择原则与四组基线/消融配置。
- **AC-005 (FR-009/FR-010)**: 规范不再包含 v0 主线冲突描述，且无语言/框架/API 级实现细节。

### Key Entities

- **Candidate Program**: 由搜索过程生成、待评估的启发式候选程序。
- **Behavioral Fingerprint**: 候选在探测实例上的决策行为摘要，用于判定行为相似性。
- **Sample Efficiency Record**: 每轮搜索中的 `N_unique`、`N_total` 及其比值记录。
- **Ablation Configuration**: 用于对比实验的配置分组定义。

### Milestone Submission Requirements

- **Deadline**: 2026-03-31 23:59 HKT
- **Deliverables**:
  - **Code**: 包含核心实现代码与可运行的命令/脚本（至少能复现初步结果）。
  - **Evaluation**: 针对选定数据集/基准的初步评估结果（表格或摘要），需明确指标定义（如 η、重复率等）。
  - **Programs**: 任何必要的辅助程序（如数据预处理、评估脚本）。
  - **Report Draft**: 包含问题描述与动机、方法设计、初步结果。
- **Packaging** (Recommended):
  - 提交目录结构建议：`milestone_submission/`
  - 包含文件：`report_draft.pdf`, `preliminary_results.md`, `code_link.txt`, `reproduction.txt`。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 团队可基于 spec 在一次评审中准确复述 v1 双机制目标，准确率达到 100%。
- **SC-002**: 按 spec 生成的实验计划 100% 包含 v1 定义的四项评估指标。
- **SC-003**: 按 spec 生成的对比计划 100% 包含 v1 定义的四组基线/消融配置。
- **SC-004**: 更新后 spec 中与 v1 冲突的 v0 主线描述项为 0。

## Assumptions

- 项目问题域保持为在线装箱任务。
- 课程交付节奏保持 proposal_v1 时间线定义不变。
- 评估对比使用统一数据与口径，保证结果可比。

## Dependencies

- `iclr2024/proposal_v1.tex`（唯一需求来源）

## Constraints

- 本次仅更新 spec 与 requirements，不扩展到额外研究目标。
- 文档要求可测试、可审阅、且不泄露实现细节。

## Out of Scope

- 不新增 proposal_v1 未定义的新算法模块。
- 不在本文档中展开实现代码和工程结构细节。
