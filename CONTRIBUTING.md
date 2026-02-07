# Contributing Guide

Thanks for helping improve AI-Platform-Square-HB! This guide describes the expected workflow and documentation standards.

## Workflow

1. Create a branch for your change.
2. Update documentation alongside code changes.
3. Run relevant tests before opening a PR.

## Documentation expectations

- Every new service should include a README in its directory.
- Keep architectural changes in sync with `docs/ARCHITECTURE.md`.
- Update `docs/README.md` with new documents.

## Code organization

- Place domain services under `services/`.
- Put reusable code in `libs/`.
- Infrastructure and deployment artifacts belong in `infra/`.

## PR checklist

- [ ] Documentation updated.
- [ ] Tests executed (if applicable).
- [ ] Architecture changes noted in `docs/ARCHITECTURE.md`.
