# Milestone Docs Package

This folder provides ready-to-submit milestone materials:

- `milestone_report_draft.md`: report draft template with prefilled project context.
- `preliminary_results.md`: fillable preliminary results table and interpretation template.
- `MILESTONE_SUBMISSION_CHECKLIST.md`: submission checklist and packaging instructions.

## Suggested workflow

1. Fill team info and benchmark details in `milestone_report_draft.md`.
2. Fill experiment numbers in `preliminary_results.md`.
3. Export report to PDF (recommended file name: `report_draft.pdf`).
4. Verify reproducibility:

```bash
ruff check .
pytest -q -rs
```

5. Follow `MILESTONE_SUBMISSION_CHECKLIST.md` to package and submit.
