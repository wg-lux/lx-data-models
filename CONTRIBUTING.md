# Contributing to lx-data-models

Thanks for helping improve `lx-dtypes`! This guide describes how to work on the
project, from setting up your environment to preparing releases.

## Code of Conduct

Participation is governed by the [MIT License](LICENSE) and the Lux Group
community standards. Please be respectful and constructive in all interactions.

## Getting Started

1. **Fork & Clone**
   ```bash
   git clone https://github.com/<your-username>/lx-data-models.git
   cd lx-data-models
   git remote add upstream https://github.com/wg-lux/lx-data-models.git
   ```
2. **Create a Virtual Environment** (Python 3.12 only)
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. **Install Dependencies**
   ```bash
   pip install -e ".[dev]"
   ```
4. **Keep Your Branch Updated**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

## Development Workflow

- **Coding style**: Use `ruff format` (or `black`) and `ruff check`. Configure
  IDEs to enforce 88-character lines.
- **Static typing**: Run `mypy lx_dtypes` before submitting.
- **Testing**: All changes must pass `pytest` with coverage ≥70% (configured via
  `pyproject.toml`).
- **Docs**: If you change APIs or behavior, update the Sphinx docs in `docs/`
   and relevant docstrings. Always rebuild locally before opening a PR.
- **Commits**: Keep commits focused. Use descriptive titles (optionally
  Conventional Commits). Reference issues/PRs when applicable.

## Pre-commit Hooks (optional but recommended)

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

The provided configuration runs `ruff` (lint + format), `mypy`, and the full
`pytest` suite before every commit, ensuring local parity with the CI jobs.

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
3. Commit any updated Markdown/HTML assets under `docs/_build` **only** when
   publishing to GitHub Pages; otherwise keep build artifacts out of the repo.

## Submitting Changes

1. Ensure lint, type-checks, and tests pass:
   ```bash
   ruff check lx_dtypes tests
   mypy lx_dtypes
   pytest
   ```
2. Update `CHANGELOG.md` under `Unreleased`.
3. Push your branch and open a pull request against `wg-lux:main`.
4. Fill out the PR template describing motivation, changes, and testing.
5. Address review feedback promptly; stay responsive until merge.

## Release Checklist

1. Confirm `CHANGELOG.md` lists the new version and highlights key changes.
2. Bump the version in `pyproject.toml` (and ensure `lx_dtypes.__version__`
   reflects it).
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

## Need Help?

Open a discussion or issue on GitHub, or reach out to the maintainers listed in
`pyproject.toml`. Happy modeling!
