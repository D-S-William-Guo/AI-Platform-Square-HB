# Contributing

## Local self-check

Run doctor first:

- Linux: `bash backend/scripts/dev/doctor.sh`
- Windows: `powershell -ExecutionPolicy Bypass -File backend\\scripts\\dev\\doctor.ps1`

Then run the core checks:

- Backend tests: `python -m pytest -q tests`
- Frontend build: `npm run build`

## Migration changes

If your PR includes migration changes, follow `docs/db-migration-sop.md` strictly.

- Do not skip steps.
- In the PR description, write what you ran and how you verified results.

## PR checklist

Before requesting review, complete the checklist in `.github/pull_request_template.md`.
