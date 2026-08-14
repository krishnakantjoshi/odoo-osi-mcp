import ast
from dataclasses import dataclass, field
from typing import Any


class ManifestParseError(ValueError):
    pass


@dataclass(frozen=True)
class ParsedManifest:
    raw: dict[str, Any]
    name: str | None
    summary: str | None
    description: str | None
    version: str | None
    license: str | None
    category: str | None
    depends: list[str] = field(default_factory=list)
    external_dependencies: dict[str, list[str]] = field(default_factory=dict)
    data: list[str] = field(default_factory=list)
    demo: list[str] = field(default_factory=list)
    assets: dict[str, Any] = field(default_factory=dict)
    installable: bool = True
    application: bool = False
    auto_install: bool = False
    author: str | None = None
    website: str | None = None
    maintainers: list[str] = field(default_factory=list)


def parse_manifest(content: str) -> ParsedManifest:
    """Parse an Odoo manifest using Python literal evaluation only."""
    try:
        payload = ast.literal_eval(content)
    except (SyntaxError, ValueError) as exc:
        raise ManifestParseError("Manifest is not a valid Python literal dictionary") from exc

    if not isinstance(payload, dict):
        raise ManifestParseError("Manifest root must be a dictionary")

    return ParsedManifest(
        raw=payload,
        name=_optional_str(payload.get("name")),
        summary=_optional_str(payload.get("summary")),
        description=_optional_str(payload.get("description")),
        version=_optional_str(payload.get("version")),
        license=_optional_str(payload.get("license")),
        category=_optional_str(payload.get("category")),
        depends=_string_list(payload.get("depends")),
        external_dependencies=_external_dependencies(payload.get("external_dependencies")),
        data=_string_list(payload.get("data")),
        demo=_string_list(payload.get("demo")),
        assets=_dict(payload.get("assets")),
        installable=bool(payload.get("installable", True)),
        application=bool(payload.get("application", False)),
        auto_install=bool(payload.get("auto_install", False)),
        author=_optional_str(payload.get("author")),
        website=_optional_str(payload.get("website")),
        maintainers=_string_list(payload.get("maintainers")),
    )


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list | tuple | set):
        return [str(item) for item in value]
    return []


def _dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _external_dependencies(value: Any) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        return {}

    return {str(key): _string_list(dep_values) for key, dep_values in value.items()}

