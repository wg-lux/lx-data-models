"""Shared query defaults and invariants for report-template validator models."""

from collections.abc import Mapping

from lx_dtypes.models.model import DtypesModel


def normalize_query_defaults(
    value: object, query_type: type[DtypesModel], fields: tuple[str, ...]
) -> object:
    """Mirror missing fields without changing input or hiding malformed queries."""
    if not isinstance(value, Mapping):
        return value
    data = dict(value)
    raw_query = data.get("query", {})
    if isinstance(raw_query, query_type):
        query = raw_query.model_dump(exclude_unset=True)
    elif isinstance(raw_query, Mapping):
        query = dict(raw_query)
    else:
        return data  # Let the declared query model report invalid input.
    for field in fields:
        if field not in data and field in query:
            data[field] = query[field]
        if field in data and field not in query:
            query[field] = data[field]
    data["query"] = query
    return data


def align_query[Query: DtypesModel](
    query: Query, expected: Mapping[str, str], *, suffix: str = ""
) -> Query:
    """Check every conflict before returning a copy with missing targets filled."""
    updates: dict[str, str] = {}
    for field, value in expected.items():
        actual = getattr(query, field)
        if actual is None and field != "operator":
            updates[field] = value
        elif actual != value:
            raise ValueError(
                f"query.{field} must match the top-level `{field}` value{suffix}."
            )
    return query.model_copy(update=updates) if updates else query


def validate_operator_condition(operator: str, condition: object | None) -> None:
    if operator == "condition":
        if condition is None:
            raise ValueError(
                "operator 'condition' requires a populated `condition` block."
            )
    elif condition is not None:
        raise ValueError(f"operator '{operator}' does not allow a `condition` block.")
