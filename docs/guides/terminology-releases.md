# Terminology Releases

This guide is for maintainers who change the terminology and report-template
packages shipped in `lx_dtypes/data/`. It explains the release rule, the tool
that applies it, and what each integrity error means.

The rule: **a published `module@version` never changes.** Hosts record the exact
identity and content digest of the terminology they used, and they must be able
to load those exact bytes again years later. Every change to published
content, including a typo fix, ships as a new version.

## Concepts

| Term | Meaning |
| --- | --- |
| Catalog | `lx_dtypes/data/catalog.json`: one entry per shipped `module@version`. |
| Default release | The catalog entry with `default: true`. One per module. It lives in the normal directory, for example `data/report_templates/coloreg/`. |
| Retained release | An older release (`default: false`) that hosts may still have pinned. It is frozen. |
| Catalog digest | `content_sha256` of a catalog entry: SHA-256 over the relative paths and bytes of every YAML file in the module directory. The loader checks it when it resolves a packaged release. |
| Retained bundle | `data/terminology/versions/<module>/<version>/`: the retained module and copies of the dependency modules it was published with. |
| Bundle pin | Digest of every YAML file in a retained bundle, stored in `tests/fixtures/lx_dtypes/retained_release_bundles.json`. It also protects the copied dependencies, which the catalog digest does not cover. |

## Workflow

Start every terminology change by checking the catalog:

```bash
uv run python scripts/kb_catalog.py status
```

It checks every release against its files, the committed catalog, the bundle
pins and the retained layout. Each problem comes with a `fix:` line.

### Change a published release

Make your edits in the default release directory, then publish them as a new
version. The order does not matter: the tool retains the bytes committed at
`HEAD`, not your working tree.

```bash
uv run python scripts/kb_catalog.py new-version coloreg 0.4.0 --dry-run
uv run python scripts/kb_catalog.py new-version coloreg 0.4.0
```

`new-version` then:

1. resolves the dependency closure of the default release as it was committed;
2. checks that the committed module bytes match the catalog digest and that the
   snapshot loads as the old version;
3. copies the module and its dependencies to
   `data/terminology/versions/coloreg/0.3.0/`;
4. sets `version` in the live `config.yaml` to the new version;
5. updates the catalog: the new version becomes the default and the old one is
   retained;
6. appends the bundle pin of the retained release.

It lists other YAML files that still mention the old version, such as rule
sidecars that carry their own `version`. Review them by hand.

If the edit was already committed, `new-version` refuses because `HEAD` no
longer holds the published bytes. Find the publishing commit and pass it:

```bash
git log --oneline -- lx_dtypes/data/report_templates/coloreg lx_dtypes/data/catalog.json
uv run python scripts/kb_catalog.py new-version coloreg 0.4.0 --from-ref <commit>
```

### Keep editing an unreleased version

A version that is not committed yet is still a draft. After each edit, update
its digest:

```bash
uv run python scripts/kb_catalog.py refresh-digest coloreg
```

`refresh-digest` refuses releases that are already in the committed catalog,
because they may have shipped. Pass `--allow-committed` only if that
`module@version` was never included in a released lx-dtypes package.

### Choose a version

Versions are opaque strings that are compared exactly; the resolver never sorts
them. Use a version that has never been published for that module. Use new
choice names when a meaning changes, and keep names whose meaning is unchanged.

### Before you open a pull request

1. Describe the terminology change under `[Unreleased]` in `CHANGELOG.md`.
2. Run the checks:

   ```bash
   uv run python scripts/kb_catalog.py status
   uv run python scripts/lint_kb_yaml.py --config <package>/config.yaml
   uv run pytest tests/unit/lx_dtypes/models/interface/test_knowledge_base_integrity.py \
     tests/test_kb_catalog_tool.py -q
   uv run pytest -q
   ```

3. Have the clinical content reviewed separately. These checks confirm that
   the software is consistent, not that the content is clinically correct.

## Never do this

| Action | Why it breaks hosts | Instead |
| --- | --- | --- |
| Edit files of a retained release | Hosts that pinned it would get different terminology or a refused load. | `git restore` it; correct the default release and run `new-version`. |
| Change `version` in `config.yaml` by hand | The catalog, the retained copy and the pins stay behind; the old release disappears. | `new-version`. |
| Update a committed `content_sha256` to match your edits | Hosts with the old digest refuse to load; hosts without it silently get new content. | `new-version`. |
| Edit or delete a bundle pin | The pin is the only protection for copied dependency modules. | Restore the bundle. |
| Remove a committed catalog entry | Recorded data can no longer be loaded. | Keep it as a retained release. |

## Error reference

Each error names the release involved and repeats the relevant fix.

| Message starts with | Meaning | Fix |
| --- | --- | --- |
| `Packaged knowledge-base digest mismatch` | The YAML files of a packaged release differ from its catalog digest. | In a checkout: `git restore` the release, or keep the edit with `new-version`. When installed: reinstall lx-dtypes. |
| `Packaged knowledge-base catalog identity conflicts with config.yaml` | `config.yaml` declares another name or version than the catalog. | Restore `config.yaml`; use `new-version` to change versions. |
| `Packaged knowledge-base catalog package_kind conflicts` | `package_kind` in `config.yaml` differs from the catalog. | Restore it, or publish the reclassification as a new version (see [package kinds](package-kinds.md)). |
| `Packaged knowledge-base directory is missing` | The catalog lists a release whose files are absent. | Restore the directory or correct `resource_root`. |
| `Registered knowledge-base digest conflicts with the installed provider` | A host registry recorded other content for this release than the installed lx-dtypes ships. | Hosts: install the lx-dtypes version that provided it, or adopt a newer module version. Maintainers: a release was changed in place; restore it. |
| `Resolved knowledge-base artifact identity ... conflicts with requested identity` | The registry entry or `input_dirs` points at a directory that holds another version. | Point it at the directory of the requested release. |
| `Knowledge-base version not provisioned locally` | The registry has no entry for that exact version. The message lists the registered versions. | Register it with `lx-dtypes-kb-registry add` or `bootstrap`. |
| `Published report template validators must resolve` | A published template names a validator that its package and dependencies do not define. | Define it, fix the name, or keep the template in draft status. |

`status` and the tests in
`tests/unit/lx_dtypes/models/interface/test_knowledge_base_integrity.py` report
the same problems with the same fixes. The tests also tamper with private
copies of a release to prove that changed bytes are refused, not served.

## Limits

- Digests cover YAML files only; the loader ignores other files.
- The resolver checks a provider's digest when it reads the registry file and
  caches the result for the life of the process. Files changed after that are
  noticed only after `clear_knowledge_base_resolver_caches()` or a restart.
- Default releases load their dependencies by name from the current tree, so
  changing a dependency changes what dependent defaults serve. Release the
  dependency under a new version as well.

## Related guides

- [Knowledge-base authoring](knowledge-base-authoring.md)
- [Structure of a valid lx-dtypes package](dtypes-package-structure.md)
- [Package kinds](package-kinds.md)
- [KB YAML linting](kb-yaml-linting.md)
