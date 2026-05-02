# Contributing

## Local self-check

Run doctor first:

```bash
make doctor
```

Then run the core checks:

```bash
make backend-test
make frontend-build
```

## Migration changes

If your PR includes migration changes, follow [docs/db-migration-sop.md](docs/db-migration-sop.md) strictly.

- Do not skip steps.
- In the PR description, write what you ran and how you verified results.

## PR checklist

Before requesting review, complete the checklist in `.github/pull_request_template.md`.
