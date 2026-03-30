# CS5491 Milestone Submission Package

This folder contains the files prepared for milestone submission.

## Included Files

1. `milestone_report_draft.pdf`
   
   - containing: problem description, method design, and preliminary results
2. `code_link.txt`
   
   - GitHub repository links and notebook links
3. `reproduction.txt`
   
   - Environment, setup, verification commands, and expected outputs
4. `notebooks/efficient_funsearch_colab.ipynb`
   

   

## Quick Submission Checklist

- [ ] Team member information is filled in `milestone_report_draft_en.md`
- [ ] Benchmark information is filled in `milestone_report_draft_en.md`
- [ ] Preliminary result table is filled in `milestone_report_draft_en.md`
- [ ] (Optional) Report draft exported to PDF (`milestone_report_draft.pdf`) if submission system prefers PDF
- [ ] Reproduction commands validated locally
- [ ] Colab path and 1.2 requirements are explicitly stated (`notebooks/efficient_funsearch_colab.ipynb`)

Status (2026-03-30):

- [x] Team member information is filled in `milestone_report_draft_en.md`
- [x] Benchmark information is filled in `milestone_report_draft_en.md`
- [x] Preliminary result table is filled in `milestone_report_draft_en.md`
- [x] Report draft exported to PDF (`milestone_report_draft.pdf`) if submission system prefers PDF
- [x] Reproduction commands validated locally
- [x] Colab path and 1.2 requirements are explicitly stated (`notebooks/efficient_funsearch_colab.ipynb`)
- [x] Behavioral dedup results added to milestone_report_draft_en.md
- [x] Behavioral dedup reproduction steps added to reproduction.txt

## Reproduction Commands

```bash
ruff check .
pytest -q -rs
```

Expected summary:
- Tests pass (current verified snapshot: 65 passed, 0 skipped)
- Lint passes (`ruff check .` -> All checks passed!)

## Suggested Submission Bundle Structure

```text
docs/milestone/
├─ README_submit.md
├─ code_link.txt
├─ reproduction.txt
└─ milestone_report_draft.pdf
```
