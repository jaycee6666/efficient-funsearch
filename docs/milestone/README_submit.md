# CS5491 Milestone Submission Package

This folder contains the files prepared for milestone submission.

## Included Files

1. `milestone_report_draft_en.md`
   - English submission draft containing: problem description, method design, and preliminary results
2. `milestone_report_draft_zh.md`
   - Chinese reading version (for internal review)
3. `code_link.txt`
   - GitHub repository links and notebook links
4. `reproduction.txt`
   - Environment, setup, verification commands, and expected outputs
5. `README_submit.md`
   - This submission note file

## Quick Submission Checklist

- [ ] Team member information is filled in `milestone_report_draft_en.md`
- [ ] Benchmark information is filled in `milestone_report_draft_en.md`
- [ ] Preliminary result table is filled in `milestone_report_draft_en.md`
- [ ] (Optional) Report draft exported to PDF (`report_draft.pdf`) if submission system prefers PDF
- [ ] Reproduction commands validated locally

## Reproduction Commands

```bash
ruff check .
pytest -q -rs
```

Expected summary:
- Lint passes
- Tests pass (current verified snapshot: 65 passed, 0 skipped)

## Suggested Submission Bundle Structure

```text
docs/milestone/
├─ README_submit.md
├─ code_link.txt
├─ reproduction.txt
├─ milestone_report_draft_en.md
├─ milestone_report_draft_zh.md
└─ report_draft.pdf (optional)
```
