import csv
from dataclasses import dataclass
from io import StringIO
from typing import Any


@dataclass(frozen=True)
class AccessRuleSymbol:
    name: str | None
    xml_id: str | None
    odoo_model: str | None
    group_xml_id: str | None
    permissions: dict[str, bool]
    metadata: dict[str, Any]


def parse_access_rules(content: str) -> list[AccessRuleSymbol]:
    """Parse standard Odoo ir.model.access.csv files."""
    reader = csv.DictReader(StringIO(content))
    if not reader.fieldnames:
        return []

    rules: list[AccessRuleSymbol] = []
    for row in reader:
        xml_id = _value(row, "id")
        name = _value(row, "name") or xml_id
        model_external_id = _value(row, "model_id:id") or _value(row, "model_id/id")
        group_xml_id = _value(row, "group_id:id") or _value(row, "group_id/id")
        permissions = {
            "read": _truthy(_value(row, "perm_read")),
            "write": _truthy(_value(row, "perm_write")),
            "create": _truthy(_value(row, "perm_create")),
            "unlink": _truthy(_value(row, "perm_unlink")),
        }

        rules.append(
            AccessRuleSymbol(
                name=name,
                xml_id=xml_id,
                odoo_model=_model_name(model_external_id),
                group_xml_id=group_xml_id,
                permissions=permissions,
                metadata={
                    "model_external_id": model_external_id,
                    "group_xml_id": group_xml_id,
                    "permissions": permissions,
                },
            )
        )

    return rules


def _value(row: dict[str, str | None], key: str) -> str | None:
    value = row.get(key)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "y"}


def _model_name(model_external_id: str | None) -> str | None:
    if model_external_id is None:
        return None
    technical = model_external_id.rsplit(".", 1)[-1]
    if technical.startswith("model_"):
        return technical.removeprefix("model_").replace("_", ".")
    return technical
