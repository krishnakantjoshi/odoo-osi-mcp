from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree


@dataclass(frozen=True)
class XmlSymbol:
    symbol_type: str
    name: str | None
    xml_id: str | None
    parent_xml_id: str | None
    odoo_model: str | None
    metadata: dict[str, Any]


def parse_xml_symbols(content: str) -> list[XmlSymbol]:
    """Extract common Odoo XML records and view inheritance signals."""
    root = ElementTree.fromstring(content)
    symbols: list[XmlSymbol] = []

    for record in root.iter("record"):
        model = record.attrib.get("model")
        xml_id = record.attrib.get("id")
        name = _field_text(record, "name")
        inherit_id = _field_ref(record, "inherit_id")

        symbols.append(
            XmlSymbol(
                symbol_type=_symbol_type_for_record(model),
                name=name,
                xml_id=xml_id,
                parent_xml_id=inherit_id,
                odoo_model=model,
                metadata={"model": model},
            )
        )

    for menu in root.iter("menuitem"):
        symbols.append(
            XmlSymbol(
                symbol_type="menuitem",
                name=menu.attrib.get("name"),
                xml_id=menu.attrib.get("id"),
                parent_xml_id=menu.attrib.get("parent"),
                odoo_model=None,
                metadata=dict(menu.attrib),
            )
        )

    return symbols


def _field_text(record: ElementTree.Element, field_name: str) -> str | None:
    field = _find_field(record, field_name)
    if field is None:
        return None
    return field.text or field.attrib.get("name")


def _field_ref(record: ElementTree.Element, field_name: str) -> str | None:
    field = _find_field(record, field_name)
    if field is None:
        return None
    return field.attrib.get("ref")


def _find_field(record: ElementTree.Element, field_name: str) -> ElementTree.Element | None:
    for field in record.findall("field"):
        if field.attrib.get("name") == field_name:
            return field
    return None


def _symbol_type_for_record(model: str | None) -> str:
    if model == "ir.ui.view":
        return "view"
    if model == "ir.actions.act_window":
        return "action"
    if model == "ir.rule":
        return "record_rule"
    if model == "res.groups":
        return "security_group"
    return "record"

