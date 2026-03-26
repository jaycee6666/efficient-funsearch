# Milestone Submission Checklist (CS5491)

截止：**Mar 31, 2026, 11:59 pm HKT**

## 1) 必交内容（对照课程指导书）

- [ ] **Code**
  - [ ] 核心实现代码（当前仓库）
  - [ ] 可运行命令/脚本（至少能复现当前初步结果）
- [ ] **Evaluation on chosen dataset/benchmark**
  - [ ] 至少一版 preliminary 表格或结果摘要
  - [ ] 指标口径写清楚（η、duplicate rate 等）
- [ ] **Any other required programs**
  - [ ] 预处理/评估辅助脚本（若有）
- [ ] **Report draft**
  - [ ] Problem description & motivation
  - [ ] Design of method/approach
  - [ ] Preliminary results

## 2) 直接可用的本仓库材料

- 报告草稿模板：`docs/milestone/milestone_report_draft.md`
- 初步结果模板：`docs/milestone/preliminary_results.md`
- 规格与任务追踪：
  - `specs/001-efficient-funsearch/spec.md`
  - `specs/001-efficient-funsearch/plan.md`
  - `specs/001-efficient-funsearch/tasks.md`

## 3) 提交前最小验证（建议截图附到附录）

```bash
ruff check .
pytest -q -rs
```

期望结果：

- [ ] lint 通过
- [ ] 测试通过（当前目标：65 passed, 0 skipped）

## 4) 打包建议（避免漏项）

建议提交目录（或同等结构）：

```text
milestone_submission/
├─ report_draft.pdf
├─ preliminary_results.pdf (or .md)
├─ code_link.txt (GitHub/Colab link)
└─ reproduction.txt
```

`reproduction.txt` 建议写：

1. 环境版本（Python、关键依赖）
2. 运行命令
3. 预期输出摘要

## 5) 你只需补的内容

- [ ] 团队成员姓名/学号
- [ ] benchmark 数据集名称与规模
- [ ] preliminary 数值结果（表格中的 `<fill>`）
- [ ] （可选）1–2 张初步图表
