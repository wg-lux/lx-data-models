from __future__ import annotations

from pathlib import Path

import pytest

from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
from lx_dtypes.models.interface.KnowledgeBaseConfig import KnowledgeBaseConfig


def test_create_from_config_rejects_duplicate_model_names(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    records_file = tmp_path / "records.yaml"

    config_file.write_text(
        (
            "name: duplicate_module\n"
            'version: "1.0.0"\n'
            "data:\n"
            "  files:\n"
            "    - records.yaml\n"
        ),
        encoding="utf-8",
    )
    records_file.write_text(
        (
            "- model: finding\n"
            "  name: duplicate_finding\n"
            "- model: finding\n"
            "  name: duplicate_finding\n"
        ),
        encoding="utf-8",
    )

    config = KnowledgeBaseConfig.from_yaml_file(config_file)
    config.normalize_data_paths(config_file)

    with pytest.raises(ValueError) as exc_info:
        KnowledgeBase.create_from_config(config)

    err = str(exc_info.value)
    assert "Duplicate 'finding' name 'duplicate_finding'" in err
    assert ":1:3" in err
    assert ":3:3" in err


def _write_module(root: Path, name: str, records: str, edges: str = "") -> Path:
    module = root / name
    module.mkdir()
    config = module / "config.yaml"
    config.write_text(
        f'name: {name}\nversion: "1.0.0"\n{edges}data:\n  files: [records.yml]\n',
        encoding="utf-8",
    )
    (module / "records.yml").write_text(records, encoding="utf-8")
    return config


@pytest.mark.parametrize("edge", ["depends_on", "modules"])
@pytest.mark.parametrize("model", ["finding", "classification", "examination"])
@pytest.mark.parametrize("description", ["canonical", "changed"])
def test_loader_rejects_child_concept_redefinition(
    tmp_path: Path, edge: str, model: str, description: str
) -> None:
    from lx_dtypes.models.interface.DataLoader import DataLoader

    _write_module(
        tmp_path,
        "child",
        f"- model: {model}\n  name: shared\n  description: canonical\n",
    )
    _write_module(
        tmp_path,
        "reporting",
        f"- model: {model}\n  name: shared\n  description: {description}\n"
        "- model: report_finding\n  name: reference\n  finding: shared\n",
        f"{edge}: [child]\n",
    )
    with (
        pytest.warns(UserWarning, match=f"'{model}' definition 'shared'"),
        pytest.raises(ValueError, match=f"Conflicting '{model}'") as exc,
    ):
        DataLoader(input_dirs=[tmp_path]).load_knowledge_base("reporting")
    assert str(tmp_path / "child" / "records.yml") in str(exc.value)
    assert str(tmp_path / "reporting" / "records.yml") in str(exc.value)


def test_reporting_warns_for_custom_concepts_across_selected_files(
    tmp_path: Path,
) -> None:
    config_file = _write_module(
        tmp_path, "reporting", "- model: finding\n  name: custom\n"
    )
    config = KnowledgeBaseConfig.from_yaml_file(config_file)
    other_file = config_file.parent / "report.yml"
    other_file.write_text(
        "- model: report_finding\n  name: reference\n  finding: custom\n"
    )
    config.data.files.append(other_file)
    config.normalize_data_paths(config_file)
    with pytest.warns(UserWarning, match="'finding' definition 'custom'") as recorded:
        kb = KnowledgeBase.create_from_config(config)
    assert len(recorded) == 1
    assert "records.yml:1:3" in str(recorded[0].message)
    assert "definitions.yml" in str(recorded[0].message)
    assert "custom" in kb.finding


def test_reporting_references_dependency_without_warning(tmp_path: Path) -> None:
    import warnings

    from lx_dtypes.models.interface.DataLoader import DataLoader

    _write_module(tmp_path, "child", "- model: finding\n  name: canonical\n")
    _write_module(
        tmp_path,
        "reporting",
        "- model: report_finding\n  name: reference\n  finding: canonical\n",
        "depends_on: [child]\n",
    )
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        kb = DataLoader(input_dirs=[tmp_path]).load_knowledge_base("reporting")
    assert not recorded
    assert kb.finding["canonical"].kb_module_name == "child"


def test_failed_import_does_not_partially_mutate_knowledge_base(tmp_path: Path) -> None:
    def load(name: str, records: str) -> KnowledgeBase:
        path = _write_module(tmp_path, name, records)
        config = KnowledgeBaseConfig.from_yaml_file(path)
        config.normalize_data_paths(path)
        return KnowledgeBase.create_from_config(config)

    kb = load("original", "- model: finding\n  name: shared\n")
    other = load(
        "incoming",
        "- model: unit\n  name: new_unit\n- model: finding\n  name: shared\n",
    )
    before = kb.model_dump()
    with pytest.raises(ValueError, match="Conflicting 'finding'"):
        kb.import_knowledge_base(other)
    assert kb.model_dump() == before


def test_transitive_conflicts_and_shared_dependency(tmp_path: Path) -> None:
    from lx_dtypes.models.interface.DataLoader import DataLoader

    _write_module(tmp_path, "canonical", "- model: finding\n  name: shared\n")
    _write_module(tmp_path, "left", "[]\n", "depends_on: [canonical]\n")
    _write_module(tmp_path, "right", "[]\n", "depends_on: [canonical]\n")
    _write_module(
        tmp_path,
        "reporting",
        "- model: report_finding\n  name: reference\n  finding: shared\n",
        "depends_on: [left, right]\n",
    )
    loader = DataLoader(input_dirs=[tmp_path])
    assert len(loader.load_knowledge_base("reporting").finding) == 1
    (tmp_path / "right" / "records.yml").write_text(
        "- model: finding\n  name: shared\n"
    )
    with pytest.raises(ValueError, match="Conflicting 'finding'") as exc:
        loader.load_knowledge_base("reporting")
    assert "canonical/records.yml" in str(exc.value)
    assert "right/records.yml" in str(exc.value)


@pytest.mark.parametrize("edge", ["depends_on", "modules"])
def test_inherited_reporting_warns_only_for_local_concepts(
    tmp_path: Path, edge: str
) -> None:
    from lx_dtypes.models.interface.DataLoader import DataLoader
    from lx_dtypes.models.interface.KnowledgeBase import ReportTemplateConceptWarning

    _write_module(tmp_path, "terminology", "- model: finding\n  name: canonical\n")
    _write_module(
        tmp_path,
        "reporting",
        "- model: report_finding\n  name: reference\n  finding: canonical\n",
        "depends_on: [terminology]\n",
    )
    _write_module(tmp_path, "intermediate", "[]\n", f"{edge}: [reporting]\n")
    _write_module(
        tmp_path,
        "study",
        "- model: finding\n  name: custom\n",
        f"{edge}: [intermediate]\n",
    )
    with pytest.warns(ReportTemplateConceptWarning) as recorded:
        kb = DataLoader(input_dirs=[tmp_path]).load_knowledge_base("study")
    assert len(recorded) == 1
    assert "study/records.yml:1:3" in str(recorded[0].message)
    assert "'finding' definition 'custom'" in str(recorded[0].message)
    assert kb.is_reporting_package
    assert kb.finding["canonical"].kb_module_name == "terminology"


def test_reporting_directory_warns_without_reporting_records(tmp_path: Path) -> None:
    from lx_dtypes.models.interface.KnowledgeBase import ReportTemplateConceptWarning

    root = tmp_path / "report_templates"
    root.mkdir()
    path = _write_module(root, "study", "- model: finding\n  name: custom\n")
    config = KnowledgeBaseConfig.from_yaml_file(path)
    config.normalize_data_paths(path)
    with pytest.warns(
        ReportTemplateConceptWarning, match="'finding' definition 'custom'"
    ):
        KnowledgeBase.create_from_config(config)


@pytest.mark.parametrize("reporting_first", [True, False])
def test_conflict_identifies_terminology_owner_and_preserves_imported_locations(
    tmp_path: Path, reporting_first: bool
) -> None:
    from lx_dtypes.models.interface.KnowledgeBase import ReportTemplateConceptWarning

    def load(name: str, records: str) -> KnowledgeBase:
        path = _write_module(tmp_path, name, records)
        config = KnowledgeBaseConfig.from_yaml_file(path)
        config.normalize_data_paths(path)
        return KnowledgeBase.create_from_config(config)

    canonical = load("terminology", "# guideline\n- model: finding\n  name: shared\n")
    with pytest.warns(ReportTemplateConceptWarning):
        reporting = load(
            "reporting",
            "- model: report_finding\n  name: reference\n  finding: shared\n- model: finding\n  name: shared\n",
        )
    aggregate = load("aggregate", "[]\n")
    first, second = (
        (reporting, canonical) if reporting_first else (canonical, reporting)
    )
    aggregate.import_knowledge_base(first)
    before = aggregate.model_dump()
    with pytest.raises(ValueError) as exc:
        aggregate.import_knowledge_base(second)
    message = str(exc.value)
    assert "reporting/records.yml:4:3" in message
    assert "terminology/records.yml:2:3" in message
    assert (
        f"Remove the reporting copy and reference 'shared' from module 'terminology' at {tmp_path / 'terminology' / 'records.yml'}:2:3"
        in message
    )
    assert aggregate.model_dump() == before


def test_bundled_terminology_under_reporting_directory_does_not_warn(
    tmp_path: Path,
) -> None:
    import warnings

    from lx_dtypes.models.interface.DataLoader import DataLoader

    root = tmp_path / "report_templates"
    root.mkdir()
    report_path = _write_module(
        root,
        "reporting",
        "- model: report_finding\n  name: reference\n  finding: canonical\n",
        "modules: [terminology]\n",
    )
    _write_module(
        report_path.parent, "terminology", "- model: finding\n  name: canonical\n"
    )
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        kb = DataLoader(input_dirs=[root]).load_knowledge_base("reporting")
    assert not recorded
    assert kb.finding["canonical"].kb_module_name == "terminology"
