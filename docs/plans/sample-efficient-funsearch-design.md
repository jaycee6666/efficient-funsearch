# Design Document: Sample-efficient FunSearch for Online Bin Packing

**Date**: 2026-02-23  
**Team Size**: 2 members  
**Course**: CS5491 AI Project

---

## 1. Problem Statement

**FunSearch** (Romera-Paredes et al., 2023) is a method that uses Large Language Models (LLMs) to automatically discover heuristic functions through evolutionary program search. During its iterative process, FunSearch generates many candidate programs, evaluates their performance, and evolves the best-performing ones.

However, FunSearch lacks mechanisms to detect functionally duplicate or near-duplicate code. This leads to:
- **Wasted LLM API calls** on generating redundant programs
- **Wasted evaluation time** on programs already tested
- **Slower convergence** to optimal solutions

**Goal**: Implement a fast duplicate code-checking mechanism to make FunSearch more sample-efficient.

---

## 2. Background

### 2.1 FunSearch Overview

FunSearch operates in an iterative loop:
1. LLM generates candidate programs (heuristic functions)
2. Each program is evaluated on test instances
3. Best-performing programs are selected as "parents"
4. Parents are used to prompt LLM for new programs
5. Process repeats until convergence or iteration limit

### 2.2 The Redundancy Problem

As FunSearch progresses, the probability of generating functionally similar programs increases. Consider these two Python snippets:

```python
# Program A
def heuristic(bins, item):
    remaining = bins - item
    return argmin(remaining)

# Program B  
def heuristic(bins, item):
    space_left = bins - item
    idx = np.argmin(space_left)
    return idx
```

These programs are functionally identical but syntactically different. FunSearch would evaluate both, wasting resources.

---

## 3. Proposed Method

### 3.1 Core Enhancement

Add a **pre-evaluation filtering step** that checks for code similarity before running the expensive evaluation.

### 3.2 System Architecture

```
┌─────────────┐    ┌──────────────────┐    ┌─────────────┐
│   LLM       │───▶│  Similarity      │───▶│ Evaluation  │
│  Generator  │    │  Filter (NEW)    │    │ Sandbox     │
└─────────────┘    └──────────────────┘    └─────────────┘
                          │
                          ▼
                   ┌──────────────┐
                   │ Program      │
                   │ Archive      │
                   └──────────────┘
```

### 3.3 Key Components

#### Component 1: Code Normalization Pipeline
- Standardize variable names to canonical form (e.g., `var_0`, `var_1`)
- Remove comments and docstrings
- Normalize whitespace and indentation
- Handle semantic-preserving transformations

#### Component 2: Similarity Detection Module

**Option A: AST-based Structural Comparison**
- Parse code into Abstract Syntax Tree
- Compare tree structures ignoring variable names
- Accurate but computationally expensive
- Best for: Precise duplicate detection

**Option B: Code Embedding + Cosine Similarity**
- Use code embedding model (e.g., CodeBERT, StarCoder embeddings)
- Compute vector representations
- Fast approximate similarity via cosine distance
- Best for: Quick filtering of near-duplicates

**Hybrid Approach (Recommended)**:
- Stage 1: Use embeddings for fast pre-filtering (threshold: 0.95 similarity)
- Stage 2: Use AST comparison for precise verification
- Best balance of speed and accuracy

#### Component 3: Program Archive with Hashing
- Store evaluated programs with their normalized signatures
- Use efficient hash-based lookup (O(1) average case)
- Maintain LRU cache for memory efficiency

#### Component 4: Integration with FunSearch Loop
```python
def enhanced_funsearch_loop():
    archive = ProgramArchive()
    while not converged:
        new_programs = llm.generate(parents)
        for program in new_programs:
            normalized = normalize(program)
            if not archive.is_duplicate(normalized):
                score = evaluate(program)
                archive.add(normalized, score)
                population.update(program, score)
```

---

## 4. Evaluation Plan

### 4.1 Dataset

**Primary**: Online Bin Packing
- OR-Library benchmarks (http://people.brunel.ac.uk/~mastjjb/jeb/info.html)
- Weibull dataset (Taillard instances)

### 4.2 Metrics

**Efficiency Metrics**:
1. **LLM Query Efficiency**: Total queries to reach target performance
2. **Time Efficiency**: Wall-clock time saved from duplicate filtering
3. **Convergence Speed**: Iterations to reach 90% of best-known solution

**Quality Metrics**:
1. **Final Performance**: Number of bins used (lower is better)
2. **Solution Quality**: Comparison with optimal/best-known solutions

### 4.3 Baselines

1. **Original FunSearch**: No duplicate checking (upper bound on queries)
2. **Exact String Match**: Simple string comparison (lower bound on detection)
3. **Our Enhanced Method**: Hybrid AST + embedding approach

### 4.4 Experimental Setup

- Run each method 5 times with different random seeds
- Fixed LLM (GPT-3.5 or GPT-4o-mini)
- Fixed iteration budget (e.g., 100 iterations)
- Report mean and standard deviation

---

## 5. Timeline

| Phase | Dates | Tasks |
|-------|-------|-------|
| Phase 1 | Feb 24 - Mar 10 | Literature review, understand FunSearch codebase |
| Phase 2 | Mar 11 - Mar 24 | Implement code normalization and similarity detection |
| Phase 3 | Mar 25 - Mar 31 | **Milestone**: Integration with FunSearch, preliminary results |
| Phase 4 | Apr 1 - Apr 14 | Full experiments, ablation studies, comparison with baselines |
| Phase 5 | Apr 15 - Apr 26 | Final report writing, documentation, code cleanup |

---

## 6. Resources

### Code Repositories
- Google DeepMind FunSearch: https://github.com/google-deepmind/funsearch
- Functional implementation (provided): https://github.com/RayZhhh/funsearch

### Papers
- Romera-Paredes et al. (2023). "Mathematical discoveries from program search with large language models." Nature.
- Lehman & Stanley (2011). "Novelty Search and the Problem with Objectives." GPTP.

### APIs & Compute
- ChatGPT API credits (provided by course)
- Google Colab with GPU access

---

## 7. Expected Contributions

1. **Novel enhancement** to FunSearch for improved sample efficiency
2. **Empirical evaluation** demonstrating resource savings
3. **Open-source implementation** of the enhanced method
4. **Potential publication** at NeurIPS '26 or EMNLP '26 workshops
