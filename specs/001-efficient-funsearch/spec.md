# Feature Specification: Efficient FunSearch

**Feature Branch**: `001-efficient-funsearch`  
**Created**: 2026-02-23  
**Status**: Draft  
**Input**: User description: "根据前面的讨论和Course_Project_Instruction.pdf，生成该项目的规范文档"

---

## Course Project Overview

### Project Logistics

| Item | Requirement |
|------|-------------|
| **Team Size** | Recommended 3 students, groups of 1-2 also allowed |
| **Project Weight** | 30% of course grade |
| **Grading** | All team members share the same grade |

### Submission Milestones

| Milestone | Weight | Due Date | Deliverables |
|-----------|--------|----------|--------------|
| **Project Proposal** | 20% (6% total) | Feb 24, 2026, 11:59 PM HKT | 1-page ICLR '24 style document |
| **Project Milestone** | 10% (3% total) | Mar 31, 2026, 11:59 PM HKT | Code + Report draft + Preliminary results |
| **Final Project** | 70% (21% total) | Apr 26, 2026, 11:59 PM HKT | Report (4-6 pages) + Google Colab |

### Final Project Grading Breakdown

| Component | Points | Criteria |
|-----------|--------|----------|
| **Final Report** | 50 points | |
| - Motivation & Problem Explanation | 10 points | Clear problem description and motivation |
| - Method Appropriateness & Explanation | 15 points | Appropriate approach with clear design |
| - Insights & Results | 15 points | Meaningful experimental results and analysis |
| - Presentation | 10 points | Writing quality, figures, organization |
| **Google Colab Code** | 20 points | |
| - Code Correctness & Design | 15 points | Working, well-designed implementation |
| - Documentation | 5 points | Class/function descriptions, comments |

### Code Submission Requirements (Google Colab)

**Platform**: Google Colab (mandatory)

**Requirements**:
1. **High-level Summary**: Description of code purpose and task
2. **Complete Code**: All code to reproduce results including:
   - Data preprocessing
   - Model/algorithm definition
   - Training/evaluation pipeline
3. **Detailed Comments**: Each cell must have clear documentation
4. **Self-contained**: Must be runnable as-is without external dependencies
5. **Reference Example**: See [PyTorch Geometric Colabs](https://pytorch-geometric.readthedocs.io/en/latest/notes/colabs.html) for good examples

### Compute Resources

| Resource | Allocation |
|----------|------------|
| **ChatGPT API Credits** | ~20,000 queries to GPT-3.5 (per team, 500 tokens input/output assumed) |
| **Google Cloud Credits** | $300 for new customers (usable in Colab for TPUv3, A100, etc.) |
| **Extra Resources** | Available for top-ranked teams pursuing publication |

### Report Format Requirements

- **Style**: ICLR '24 style file ([download](https://github.com/ICLR/MasterTemplate/raw/master/iclr2024.zip))
- **Page Limit**: 4-6 pages (excluding references)
- **No abstract required for proposal**

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run FunSearch with Duplicate Detection (Priority: P1)

As a researcher using FunSearch for combinatorial optimization problems, I want the system to automatically detect and filter out functionally duplicate programs before evaluation, so that I can reduce wasted LLM API calls and evaluation time.

**Why this priority**: This is the core functionality - without duplicate detection, the entire project has no value. The primary goal is to improve sample efficiency.

**Independent Test**: Can be fully tested by running FunSearch with and without the duplicate detection module and comparing the number of unique programs evaluated.

**Acceptance Scenarios**:

1. **Given** FunSearch generates 10 new candidate programs, **When** the duplicate detection module processes them, **Then** it should identify and filter out programs that are functionally identical to previously evaluated ones.
2. **Given** A program with different variable names but identical logic, **When** processed by normalization, **Then** it should be detected as a duplicate.
3. **Given** A program archive with 1000 unique programs, **When** checking a new candidate, **Then** the lookup should complete in under 1 second.

---

### User Story 2 - Evaluate Sample Efficiency Improvements (Priority: P2)

As a student completing the course project, I want to measure how much the duplicate detection improves FunSearch's efficiency, so that I can demonstrate the effectiveness of the enhancement in the final report.

**Why this priority**: The course requires empirical evaluation demonstrating the improvement. Without measurable results, the project cannot be completed.

**Independent Test**: Can be fully tested by running experiments with and without the enhancement and comparing LLM query counts to reach target performance.

**Acceptance Scenarios**:

1. **Given** A fixed iteration budget (e.g., 100 iterations), **When** running original FunSearch vs enhanced FunSearch, **Then** the enhanced version should use at least 20% fewer LLM queries to reach similar performance.
2. **Given** The same random seed, **When** comparing convergence speed, **Then** the enhanced version should reach 90% of best-known solution in fewer iterations.

---

### User Story 3 - Maintain Solution Quality (Priority: P3)

As a researcher, I want to ensure that the duplicate detection does not filter out potentially valuable programs, so that the final solutions remain high quality.

**Why this priority**: Over-aggressive filtering could remove novel programs that just happen to look similar but have different behavior. Must balance efficiency with quality.

**Independent Test**: Can be tested by comparing final solution quality (bin count for bin packing) between original and enhanced FunSearch.

**Acceptance Scenarios**:

1. **Given** A program that is semantically different but syntactically similar, **When** processed by the hybrid detection, **Then** it should NOT be filtered out as a duplicate.
2. **Given** Running FunSearch to completion, **When** comparing final bin count, **Then** the enhanced version should achieve within 5% of the original's solution quality.

---

### User Story 4 - Prepare Deliverables for Course Submission (Priority: P2)

As a student, I need to prepare all required deliverables in the correct format for each milestone, so that my team can receive full credit for the project.

**Why this priority**: Without proper deliverables, the project cannot be graded regardless of technical quality.

**Independent Test**: Can be tested by verifying each deliverable matches the submission requirements.

**Acceptance Scenarios**:

1. **Given** The proposal deadline, **When** submitting, **Then** the document must be in ICLR '24 style, one page, without abstract and references.
2. **Given** The milestone deadline, **When** submitting, **Then** code must run on evaluation dataset and report draft must include problem description, method design, and preliminary results.
3. **Given** The final deadline, **When** submitting, **Then** the report must be 4-6 pages (ICLR '24 style) and Google Colab must be self-contained and runnable.

---

### Edge Cases

- What happens when the code contains syntax errors and cannot be parsed?
- How does the system handle empty or trivial programs (e.g., just "return 0")?
- What happens when the program archive reaches memory limits?
- How are newly generated programs that are slightly modified versions of existing ones handled?
- What happens when LLM generates completely invalid code?
- What happens if ChatGPT API quota is exhausted before experiments complete?

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept a Python program as input and output a normalized canonical representation
- **FR-002**: System MUST compute similarity scores between normalized programs using a two-stage hybrid approach
- **FR-003**: System MUST maintain a program archive that stores all previously evaluated programs with their normalized forms
- **FR-004**: System MUST filter out programs that exceed a similarity threshold (0.95) before evaluation
- **FR-005**: System MUST integrate with FunSearch's iteration loop as a pre-evaluation filter
- **FR-006**: System MUST log all duplicate detection decisions for debugging and analysis
- **FR-007**: System MUST handle edge cases including syntax errors, empty programs, and invalid code gracefully
- **FR-008**: System MUST provide metrics on duplicate detection rate and resource savings

### Course Deliverable Requirements

- **CD-001**: Proposal MUST be submitted by Feb 24, 2026 in ICLR '24 style format (1 page, no abstract, no references)
- **CD-002**: Proposal MUST include: topic selection, motivation, tentative plan, evaluation approach, comparison baseline
- **CD-003**: Milestone MUST be submitted by Mar 31, 2026 with working code and report draft
- **CD-004**: Milestone code MUST run on chosen dataset/benchmark and produce preliminary results
- **CD-005**: Final report MUST be submitted by Apr 26, 2026 in ICLR '24 style format (4-6 pages, excluding references)
- **CD-006**: Final report MUST include: motivation & problem (10 pts), method explanation (15 pts), insights & results (15 pts), presentation quality (10 pts)
- **CD-007**: Final code MUST be submitted via Google Colab with high-level summary, complete runnable code, and detailed cell comments
- **CD-008**: Google Colab MUST be self-contained and runnable as-is without external setup

### Key Entities

- **Program**: A Python function that implements a heuristic for the bin packing problem
- **Normalized Program**: A canonical representation of a program after AST parsing and variable standardization
- **Program Archive**: Storage containing all previously evaluated programs with their normalized forms and scores
- **Similarity Score**: A numerical value (0-1) indicating how similar two programs are

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Enhanced FunSearch uses at least 20% fewer LLM queries than original FunSearch to achieve comparable performance (measured by bin count)
- **SC-002**: Duplicate detection module processes each candidate program in under 1 second (including archive lookup)
- **SC-003**: Final solution quality of enhanced FunSearch is within 5% of original FunSearch's performance
- **SC-004**: System correctly identifies at least 90% of syntactically different but functionally identical program pairs
- **SC-005**: The project produces a working implementation with documented experimental results suitable for the course report

### Course Deliverable Success Criteria

- **SC-006**: Proposal submitted on time meeting all format requirements
- **SC-007**: Milestone code produces preliminary results on benchmark dataset
- **SC-008**: Final report achieves at least 40/50 points on report rubric
- **SC-009**: Google Colab achieves at least 15/20 points on code rubric
- **SC-010**: ChatGPT API usage stays within provided quota (~20,000 queries)

---

## Assumptions

- FunSearch will be based on the RayZhhh/funsearch community implementation (as agreed in brainstorming)
- The problem domain is Online Bin Packing as specified in the course project
- LLM API access will be available via course-provided credits (~20,000 GPT-3.5 queries)
- Code similarity detection will use a hybrid approach: embedding-based pre-filtering + AST verification
- Development will occur on Google Colab for final submission
- Team size is 2 members (as indicated in existing design document)

---

## Constraints

- **Time Constraints**: Must meet three hard deadlines (Feb 24, Mar 31, Apr 26, 2026)
- **Resource Constraints**: ChatGPT API limited to ~20,000 queries (may need optimization)
- **Format Constraints**: ICLR '24 style file mandatory for all written submissions
- **Platform Constraints**: Final code must run on Google Colab without external dependencies
- **Page Constraints**: Final report limited to 4-6 pages (excluding references)

---

## Out of Scope

- Publication submission (though top teams will be invited)
- GPU-intensive model training (embedding model can use pre-computed embeddings)
- Real-time production deployment
- Support for programming languages other than Python
