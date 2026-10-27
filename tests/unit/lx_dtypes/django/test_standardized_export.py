import csv
from pathlib import Path

import pytest
from django.contrib.auth.models import Group, Permission
from django.db.models import Model, QuerySet

from lx_dtypes.django.standardized_export import export_querysets, queryset_tables


@pytest.mark.django_db
def test_queryset_export_retains_filters_and_m2m(tmp_path: Path) -> None:
    chosen = Group.objects.create(name="selected")
    excluded = Group.objects.create(name="excluded")
    permissions = list(Permission.objects.order_by("pk")[:2])
    assert len(permissions) == 2
    chosen.permissions.add(permissions[0])
    excluded.permissions.add(permissions[1])
    selected: QuerySet[Model] = Group.objects.filter(pk=chosen.pk).using("default")
    export_querysets({"groups": selected}, tmp_path)
    with (tmp_path / "groups.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    assert rows == [{"id": str(chosen.pk), "name": "selected"}]
    with (tmp_path / "groups__permissions.csv").open() as stream:
        links = list(csv.DictReader(stream))
    assert len(links) == 1
    assert links[0]["group_id"] == str(chosen.pk)
    assert links[0]["permission_id"] == str(permissions[0].pk)
    assert Group.objects.count() == 2


@pytest.mark.django_db
def test_empty_queryset_preserves_model_and_relation_headers() -> None:
    tables = queryset_tables({"groups": Group.objects.none()})
    assert tables["groups"].columns == ["id", "name"]
    assert tables["groups"].rows == []
    assert tables["groups__permissions"].columns == ["id", "group_id", "permission_id"]


def test_sliced_queryset_and_table_collision_are_rejected() -> None:
    with pytest.raises(ValueError, match="sliced"):
        queryset_tables({"groups": Group.objects.all()[:1]})


@pytest.mark.django_db
def test_join_duplicates_are_rejected_and_distinct_exports() -> None:
    group = Group.objects.create(name="two permissions")
    permissions = list(Permission.objects.order_by("pk")[:2])
    group.permissions.add(*permissions)
    joined = Group.objects.filter(permissions__in=permissions)
    with pytest.raises(ValueError, match="distinct"):
        queryset_tables({"groups": joined})
    tables = queryset_tables({"groups": joined.distinct()})
    assert [row["id"] for row in tables["groups"].rows] == [group.pk]


@pytest.mark.django_db
def test_unordered_queryset_rows_follow_primary_key() -> None:
    created = [Group.objects.create(name=name) for name in ("b", "a", "c")]
    tables = queryset_tables({"groups": Group.objects.filter(name__in="abc")})
    assert [row["id"] for row in tables["groups"].rows] == sorted(
        group.pk for group in created
    )


def test_binary_columns_rejected_unless_base64_opt_in(
    django_db_blocker, tmp_path: Path
) -> None:
    from django.db import connections, models
    from django.test.utils import isolate_apps

    alias = "csv_binary_test"
    connections.databases[alias] = {
        **connections.databases["default"],
        "NAME": ":memory:",
    }
    try:
        with isolate_apps("django.contrib.contenttypes"), django_db_blocker.unblock():

            class Prediction(models.Model):
                payload = models.BinaryField(null=True)

                class Meta:
                    app_label = "contenttypes"

            with connections[alias].schema_editor() as editor:
                editor.create_model(Prediction)
            Prediction.objects.using(alias).create(payload=b"\x00\xffkey")
            Prediction.objects.using(alias).create(payload=None)
            selected = Prediction.objects.using(alias).all()
            with pytest.raises(ValueError, match="binary columns.*payload"):
                queryset_tables({"predictions": selected})
            export_querysets({"predictions": selected}, tmp_path, binary="base64")
            with (tmp_path / "predictions.csv").open() as stream:
                rows = list(csv.DictReader(stream))
            assert [row["payload"] for row in rows] == ["AP9rZXk=", ""]
    finally:
        connections[alias].close()
        del connections[alias]
        del connections.databases[alias]


@pytest.mark.django_db
def test_bundled_frame_files_are_exported_with_hashes(tmp_path: Path) -> None:
    import hashlib

    import yaml

    image = tmp_path / "source.jpg"
    image.write_bytes(b"synthetic-frame")
    out = tmp_path / "export"
    path = "frames/video-1/frame_000001.jpg"
    manifest = export_querysets(
        {"groups": Group.objects.none()}, out, files={path: image}
    )
    assert (out / path).read_bytes() == b"synthetic-frame"
    entry = yaml.safe_load(manifest.read_text())["files"][path]
    assert entry == {
        "bytes": 15,
        "sha256": hashlib.sha256(b"synthetic-frame").hexdigest(),
    }


def test_non_default_database_and_relations(django_db_blocker) -> None:
    from django.contrib.contenttypes.models import ContentType
    from django.db import connections

    alias = "csv_export_test"
    config = {**connections.databases["default"], "NAME": ":memory:"}
    connections.databases[alias] = config
    try:
        with django_db_blocker.unblock():
            connection = connections[alias]
            with connection.schema_editor() as editor:
                for model in (ContentType, Permission, Group):
                    editor.create_model(model)
            content_type = ContentType.objects.using(alias).create(
                app_label="test", model="export"
            )
            permission = Permission.objects.using(alias).create(
                name="export", codename="export", content_type=content_type
            )
            group = Group.objects.using(alias).create(name="other database only")
            group.permissions.add(permission)
            tables = queryset_tables(
                {"groups": Group.objects.using(alias).filter(pk=group.pk)}
            )
            assert tables["groups"].rows == [
                {"id": group.pk, "name": "other database only"}
            ]
            assert (
                tables["groups__permissions"].rows[0]["permission_id"] == permission.pk
            )
    finally:
        connections[alias].close()
        del connections[alias]
        del connections.databases[alias]
