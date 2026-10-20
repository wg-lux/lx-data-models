# Contributing to lx-data-models

You can help through questions, domain feedback, documentation, examples, tests,
or code. This guide covers setup, review, and releases.

## Choose a starting point

1. Follow the [reader roadmap](docs/index.md#reader-roadmap) to explore the package.
2. Try an example with synthetic data. Report unclear steps or unexpected results
   in the [issue tracker](https://github.com/wg-lux/lx-data-models/issues).
3. Choose a small fix. For larger changes, open an issue to discuss scope and
   compatibility with maintainers.
4. Submit a focused pull request with your changes and verification results.

You can suggest a documentation correction without setting up Python. Use the
environment below to run examples, build documentation, or change code.

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

2. **Install the development environment** with Python 3.12 and `uv`

   ```bash
   uv sync --extra dev
   ```

3. **Keep your branch updated**

   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

## Development Workflow

- **Style**: Run `uv run ruff format` and `uv run ruff check`. Use 88-character lines.
- **Types**: Run `uv run pyright` for code changes.
- **Tests**: Run focused tests while developing. CI runs the full suite with a
  70% coverage threshold.
- **Docs**: Update the guides and docstrings when APIs or behavior change.
  Build changed documentation before opening a pull request.
- **Commits**: Keep each change focused and use a descriptive title.

### Package Boundary Rules

Use public package imports in consuming applications. Keep fixtures and example
scripts in development workflows. Write generated examples to
`temp/generated_exports/` and test output to `tmp_path`. Keep fixtures synthetic
and free of patient data, credentials, and machine-local paths.

See the [package boundary guide](docs/guides/package_boundary.md) for the full
contract. Before authoring terminology YAML, read the
[package structure guide](docs/guides/dtypes-package-structure.md).

## Pre-commit Hooks (optional but recommended)

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

The hooks run Ruff, context-manifest validation, and knowledge-base YAML linting
across the repository. Ruff may update files. CI also runs Pyright and pytest;
passing the hooks covers part of those checks.

## Documentation Workflow

The development environment includes the documentation dependencies.

1. Edit the existing guide for the topic. Keep sentences short and link to
   detailed contracts instead of repeating them. Give new guides a clear owner
   and topic.
2. Build the site and check links:
   ```bash
   uv run make -C docs html
   uv run make -C docs linkcheck
   ```
3. Keep generated files under `docs/_build/` out of version control.

## Submitting Changes

1. Run the checks relevant to your change. For code changes:
   ```bash
   uv run ruff check lx_dtypes tests
   uv run pyright
   uv run pytest tests -q --cov=lx_dtypes
   ```
   For every change, validate the repository context:
   ```bash
   uv run python scripts/lint_structure.py
   ```
2. Update `CHANGELOG.md` under `Unreleased` for user-visible changes.
3. Push your branch and open a pull request against `wg-lux:main`.
4. Describe the problem, resulting behavior, and checks run in the PR template.
   Include any failures or checks you could not run.
5. Work with reviewers to resolve feedback.

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

Open an issue on GitHub or contact the maintainers listed in `pyproject.toml`.
Include the step you tried, your expected result, and a synthetic example when
reporting a problem.
