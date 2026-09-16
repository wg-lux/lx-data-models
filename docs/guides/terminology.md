## Terminology configuration and usage

Terminology is addressed by a **module name and version**. The central resolver reads the registry for that identity and loads the registered resources. Application code uses `lx_dtypes.terminology.terminology_loader` rather than constructing paths to individual knowledge-base folders.

### Initialize and load terminology

Initialize the runtime registry explicitly before loading terminology for the first time:

```python
from lx_dtypes.terminology.terminology_loader import (
    active_kb_identity,
    hydrate_shipped_terminology,
    load_module_kb,
)

# Run during standalone initialization or deployment provisioning.
registry_path = hydrate_shipped_terminology()

# Resolve a complete identity and keep it for the operation.
module_name, version = active_kb_identity()
kb = load_module_kb(module_name, version=version)

print(registry_path)
print(kb.config.source_file)
```

`hydrate_shipped_terminology()` copies and registers shipped resources in writable runtime storage. Run it as an initialization operation, not inside a request handler or at module import. Later reads use the registry without automatically hydrating it.

`get_terminology_service()` only constructs and caches the configured service. It does not create the registry, copy resources, or choose an active bundle.

### Choose the storage directory

The runtime directory is selected in this order:

| Configuration | Behaviour |
| --- | --- |
| A `path` argument to `hydrate_shipped_terminology(path)` | Use that directory for this hydration call. |
| A non-`None` Django `TERMINOLOGY_ROOT` setting | Use the application-configured directory. |
| No configured root, or a value of `None` | Use `platformdirs.user_data_path("lx-dtypes", appauthor=False, ensure_exists=False) / "terminology"`. |

The standalone default requires no terminology-specific environment variable. Django does not need a `TERMINOLOGY_ROOT` setting merely to select this default; a configured application can override it.

For a hosted application, set the directory in Django settings before initializing the API or obtaining the service:

```python
from pathlib import Path

TERMINOLOGY_ROOT = Path("/var/lib/lx-annotate/terminology")
```

The configured value must be a nonempty, absolute `str` or `Path`. Empty strings, relative paths, and unsupported types are configuration errors, not requests to use the default. `TERMINOLOGY_ROOT` names a **directory**; the service appends `registry.json`.

Inspect the effective registry location without provisioning it:

```python
from lx_dtypes.terminology.terminology_loader import get_terminology_service

print(get_terminology_service().registry_path)
```

**An explicit hydration path is not a global configuration override.** Calling `hydrate_shipped_terminology(other_root)` prepares that location but does not redirect later calls to `get_terminology_service()`, `active_kb_identity()`, or `load_module_kb()`. For application-wide use, configure `TERMINOLOGY_ROOT` before obtaining the shared service.

### Understand the source and runtime data

Hydration reads the data directory belonging to the imported `lx_dtypes` package. When the package is imported from a `./lx-data-models` checkout, the source is `./lx-data-models/lx_dtypes/data`. An installed package uses its own data directory. The source is not selected from the process's current working directory.

The runtime directory has this layout:

```text
<terminology-root>/
    registry.json
    shipped/
        <source-tree-digest>/
            origin.json
            data/
                <module>/
                    config.yaml
                    ...
                ...
    terminology-packages/
        ...
```

The shipped tree's internal layout, including versioned subdirectories, is preserved. Registry entries identify the actual input roots; callers must not infer a module's location by concatenating its name to the runtime root.

**The source and runtime directory must not overlap:** neither may equal or contain the other. Shipped package data is the initialization source, not the writable application directory.

Hydration validates the catalog identities and content for entries it needs to seed, publishes a copied tree, and registers its filesystem locations. Repeated hydration preserves existing runtime filesystem entries, edited copies, and the active selection. An initially empty registry receives the shipped default active identity. A populated registry without an active selection is not automatically assigned one.

The source-tree digest identifies the original shipped tree. It is not a guarantee that an editable runtime copy still has those original contents.

### Load active or explicitly versioned knowledge bases

Use a complete identity throughout each request or operation:

```python
from lx_dtypes.terminology.terminology_loader import (
    active_kb_identity,
    load_module_kb,
)

module_name, version = active_kb_identity()
kb = load_module_kb(module_name, version=version)
core_concepts = kb.export_core_concepts()
```

`active_kb_identity()` reads the registry's current selection. Keep the returned tuple for the operation instead of resolving the active selection separately in each serializer or nested helper.

For an existing examination or another persisted record, load its stored module and version instead. Both values must be present; a missing persisted identity must not be replaced by the current active selection.

The version argument is optional only for the active module. `load_module_kb(module_name)` uses the active version if `module_name` matches the active module; otherwise it raises `TerminologyError`. It does not choose the newest version of an arbitrary module. An explicit version requests exactly that registered identity, independently of which bundle is active.

The root fallback only selects a storage directory. It does not silently replace a missing registry, unknown version, or invalid bundle with package data.

### Resolve a module directory for the report builder

Use the central path resolver when an operation genuinely needs a filesystem directory:

```python
from lx_dtypes.terminology.terminology_loader import (
    active_kb_identity,
    resolve_module_path,
)

module_name, version = active_kb_identity()
module_path = resolve_module_path(
    module_name,
    version=version,
    for_write=True,
)
```

The result is the directory containing the resolved module's `config.yaml`, not the overall terminology root. The resolver checks the loaded identity and source file. `for_write=True` rejects directories inside the shipped package data; editing requires a hydrated or imported runtime copy.

This check does not grant filesystem permissions or application authorization. Perform edits through the report-builder workflow and preserve its validation and cache-handling requirements.

### Use an isolated registry directly

For tests or utilities that need an independent location without changing application configuration, construct a service with an explicit **registry file path**:

```python
from pathlib import Path
from tempfile import TemporaryDirectory

from lx_dtypes.terminology.terminology_service import TerminologyService

with TemporaryDirectory(prefix="lx-dtypes-terminology-") as directory:
    service = TerminologyService(
        registry_path=Path(directory) / "registry.json",
    )
    service.provision()

    identity = service.active_identity()
    if identity is None:
        raise RuntimeError("The test registry has no active terminology.")

    kb = service.load(*identity)
    # Complete operations using this registry inside the context.
```

Use this service consistently for the isolated operation. Global loader functions continue to use the application-configured or standalone default service.

API tests must configure their test root before importing modules that register routes and capture a service. Clearing `get_terminology_service.cache_clear()` allows a later factory call to read changed settings, but does not replace a service already retained by a route.

### Runtime behaviour and errors

The shared factory caches service configuration, not the active identity. All processes intended to share terminology must use the same registry and have access to its registered resources. A matching path string on separate filesystems is not shared storage.

Knowledge-base and route caches are separate from the service factory. Same-version resource edits require the applicable cache invalidation in each affected worker or a restart. Reading the active identity again does not invalidate cached knowledge-base contents.

Invalid root configuration raises `ImproperlyConfigured`. Registry and bundle operations report `TerminologyError`; for example, `active_kb_identity()` reports an error when no active identity exists. Let the application's terminology error handler preserve the service's status and message. Provision a missing registry explicitly, and correct invalid identities or resource locations rather than silently loading a different bundle.
