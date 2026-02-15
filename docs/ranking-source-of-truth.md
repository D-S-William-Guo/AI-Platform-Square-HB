# Ranking Source of Truth Decision (Restart from PR11)

## Scope
- Batch 2 only.
- No API path/field semantic changes.
- No business result rule changes.

## Current Entry Points Inventory
1. Legacy score function: `calculate_app_score()` in `backend/app/main.py`.
2. Three-layer ranking sync path: `sync_rankings_service()` in `backend/app/main.py`.
3. Seed-time helper: `seed.py` also has ranking calculations, but runtime authority should remain in service sync path.

## Decision
- **Single source of truth** for runtime ranking calculation is `sync_rankings_service()` (three-layer config + `AppRankingSetting`).
- `calculate_app_score()` is kept for compatibility/audit only and marked deprecated via docstring + warning log.

## Deprecated Strategy
- Keep function to avoid breakage in hidden or tooling callers.
- Emit warning when called to make accidental usage visible.
- Do not route production sync through legacy function.

## Stability Regression Anchor
- Add one pure-function test for three-layer scoring to assert deterministic output for same input.
- This acts as a regression anchor without changing ranking semantics.

## Validation
```bash
cd backend
PYTHONPATH=. pytest -q tests/test_ranking_consistency.py tests/test_api.py::test_health
```

## Rollback
```bash
git revert <batch2-commit-sha>
```
