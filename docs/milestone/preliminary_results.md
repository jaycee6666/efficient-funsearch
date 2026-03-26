# Preliminary Results (Milestone)

> 用于里程碑提交的“初步结果”页。可复制到报告草稿中。

## A. Current Verification Snapshot

- Lint: `ruff check .` ✅ pass
- Tests: `pytest -q -rs` ✅ 65 passed, 0 skipped

## B. Preliminary Experiment Table (Fillable)

| Setting | N_total | N_unique | Sample Efficiency η | Duplicate Rate | Convergence Proxy | Final Quality Proxy | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| original | 待跑 | 待跑 | 待跑 | 待跑 | 待跑 | 待跑 | 配置已就绪（ablation registry） |
| exact_string_match | 待跑 | 待跑 | 待跑 | 待跑 | 待跑 | 待跑 | 配置已就绪（ablation registry） |
| normalized_hash_only | 待跑 | 待跑 | 待跑 | 待跑 | 待跑 | 待跑 | 配置已就绪（ablation registry） |
| behavioral_plus_diversity | 待跑 | 待跑 | 待跑 | 待跑 | 待跑 | 待跑 | 主线路径已实现并通过测试 |

> 指标定义建议（与 spec 一致）：
> - Sample Efficiency: \(\eta = N_{unique}/N_{total}\)
> - Duplicate Rate: \(N_{duplicate}/N_{total}\)

## C. Preliminary Interpretation Template

1. **Efficiency trend**: `<behavioral_plus_diversity 相比 baseline 在 η 与 duplicate rate 上的初步变化>`
2. **Search behavior**: `<是否观察到更稳健的策略多样性>`
3. **Quality impact**: `<最终质量是否保持或提升>`
4. **Limitations**: `<当前样本量、运行预算、统计显著性限制>`

## C1. Current Non-Empty Evidence You Can Report Now

如果老师允许“工程阶段初步结果”，可以先写这张已完成表：

| Evidence Item | Result |
|---|---|
| Full lint | `ruff check .` 通过 |
| Full tests | `pytest -q -rs` 通过（65 passed, 0 skipped） |
| US1 behavioral dedup path | 单元+集成测试通过 |
| US2 diversity ranking path | 单元+集成测试通过 |
| US3 metrics + ablation interfaces | 单元+集成测试通过 |

> 这张表可以作为“preliminary implementation result”；后续再补 benchmark 数值表。

## D. Commands / Evidence

可复现实验与验证命令（按需附在提交中）：

```bash
ruff check .
pytest -q -rs
pytest tests/unit -v
pytest tests/integration -v
```
