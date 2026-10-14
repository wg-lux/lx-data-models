# Contributing to lx-data-models

Thanks for helping improve `lx-dtypes`! This guide describes how to work on the
project, from setting up your environment to preparing releases.

## Code of Conduct

Please be respectful and constructive in all interactions. The project does not
currently publish a separate code of conduct; maintainers may moderate
participation to keep the community safe and productive.

## Getting Started

1. **Fork and clone**

   ```bash
   git clone https://github.com/<your-username>/lx-data-models.git
   cd lx-data-models
   git remote add upstream https://github.com/wg-lux/lx-data-models.git
   ```

2. **Install the development environment** (Python 3.12 only)

   ```bash
   uv sync --extra dev
   ```

3. **Keep your branch updated**

   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

## Development Workflow

- **Coding style**: Use `ruff format` (or `black`) and `ruff check`. Configure
  IDEs to enforce 88-character lines.
- **Static typing**: Run `uv run pyright` before submitting. CI also checks the
  package with mypy.
- **Testing**: All changes must pass `pytest` with coverage ≥70% (configured via
  `pyproject.toml`).
- **Docs**: If you change APIs or behavior, update the Sphinx docs in `docs/`
   and relevant docstrings. Always rebuild locally before opening a PR.
- **Commits**: Keep commits focused. Use descriptive titles (optionally
  Conventional Commits). Reference issues/PRs when applicable.

### Package Boundary Rules

- Treat `lx-data-models` as a package consumed by sibling services.
- Prefer imports from public package modules instead of deep leaf modules when
  those exports exist.
- Never import package tests, test fixtures, or example scripts from consumer
  applications.
- Example/demo outputs belong under `temp/generated_exports/`.
- Tests must use `tmp_path` or dedicated fixture directories rather than
  repository-root generated files.

## Pre-commit Hooks (optional but recommended)

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

The provided configuration runs the same commands as CI, but with local
auto-fix for lint/format issues: `ruff --fix lx_dtypes tests`, `ruff format
lx_dtypes tests`, `mypy lx_dtypes`, and the full `pytest` suite. Because the
hooks run against the whole repository (`pass_filenames: false`), a passing
local run guarantees that CI will agree.

## Documentation Workflow

1. Install the documentation extras (already included in `.[dev]`):
   ```bash
   pip install -e ".[docs]"
   ```
2. Build the HTML site and verify links:
   ```bash
   make -C docs html
   make -C docs linkcheck
   ```
3. Keep generated files under `docs/_build/` out of version control.

## Submitting Changes

1. Ensure lint, type-checks, and tests pass:
   ```bash
   ruff check lx_dtypes tests
   pyright
   pytest
   ```
2. Update `CHANGELOG.md` under `Unreleased`.
3. Push your branch and open a pull request against `wg-lux:main`.
4. Fill out the PR template describing motivation, changes, and testing.
5. Address review feedback promptly; stay responsive until merge.

## Release Checklist

1. Confirm `CHANGELOG.md` lists the new version and highlights key changes.
2. Bump the version in `pyproject.toml`.
3. Tag the release (`git tag vX.Y.Z && git push origin vX.Y.Z`).
4. Build artifacts and upload:
   ```bash
   rm -rf dist
   python -m build
   twine check dist/*
   twine upload --repository testpypi dist/*
   twine upload dist/*
   ```
5. Alternatively, trigger the `Publish` GitHub Action (release event or manual
   dispatch) once Trusted Publishers are configured for TestPyPI/PyPI and the
   `testpypi`/`pypi` environments are approved. The workflow builds packages,
   uploads to TestPyPI, then PyPI for tagged releases—no API tokens required.
6. Announce in the relevant channels and update documentation badges.

Shortcut commands:

```bash
lx-dtypes-release prepare 0.1.2
lx-dtypes-release build
git tag v0.1.2 && git push origin v0.1.2
```

To provision a historical KB version for runtime lookup:

```bash
lx-dtypes-kb-registry add-current /path/to/kb_registry.json --module report_template_examples
```

## Need Help?

Open a discussion or issue on GitHub, or reach out to the maintainers listed in
`pyproject.toml`. Happy modeling!
