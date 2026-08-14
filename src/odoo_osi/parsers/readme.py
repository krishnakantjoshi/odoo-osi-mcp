import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ReadmeSection:
    title: str
    section_type: str
    body: str


def parse_readme_sections(content: str) -> list[ReadmeSection]:
    """Split Markdown/reStructuredText README content into useful sections."""
    lines = content.replace("\r\n", "\n").split("\n")
    sections: list[tuple[str, list[str]]] = []
    current_title = "Overview"
    current_body: list[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]
        markdown_heading = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", line)
        rst_heading = _rst_heading(lines, index)

        if markdown_heading:
            _append_section(sections, current_title, current_body)
            current_title = markdown_heading.group(1).strip()
            current_body = []
        elif rst_heading:
            _append_section(sections, current_title, current_body)
            current_title = line.strip()
            current_body = []
            index += 1
        else:
            current_body.append(line)
        index += 1

    _append_section(sections, current_title, current_body)
    return [
        ReadmeSection(
            title=title,
            section_type=_section_type(title),
            body=body,
        )
        for title, body in sections
        if body.strip()
    ]


def _append_section(sections: list[tuple[str, list[str]]], title: str, body: list[str]) -> None:
    normalized_body = "\n".join(body).strip()
    if normalized_body:
        sections.append((title, normalized_body))


def _rst_heading(lines: list[str], index: int) -> bool:
    if index + 1 >= len(lines):
        return False
    title = lines[index].strip()
    underline = lines[index + 1].strip()
    return bool(title and len(underline) >= len(title) and set(underline) <= set("=-~^#*"))


def _section_type(title: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    if normalized in {"usage", "configuration", "installation", "known_issues", "roadmap"}:
        return normalized
    if "configure" in normalized or "configuration" in normalized:
        return "configuration"
    if "usage" in normalized or "use" == normalized:
        return "usage"
    if "issue" in normalized or "bug" in normalized:
        return "known_issues"
    return normalized or "overview"
