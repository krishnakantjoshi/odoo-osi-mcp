from dataclasses import dataclass
from pathlib import PurePosixPath

from odoo_osi.ingestion.contracts import GitHubTreeEntry

INDEXED_SUFFIXES = {
    ".py": ("python", "python"),
    ".xml": ("xml", "xml"),
    ".csv": ("csv", "csv"),
    ".js": ("javascript", "javascript"),
    ".md": ("markdown", "markdown"),
    ".rst": ("markdown", "restructuredtext"),
}


@dataclass(frozen=True)
class SourceFileCandidate:
    path: str
    file_type: str
    language: str
    sha: str
    size: int


def discover_source_file_candidates(
    tree: list[GitHubTreeEntry],
    module_path: str,
    limit: int | None = None,
) -> list[SourceFileCandidate]:
    prefix = f"{module_path.rstrip('/')}/"
    candidates: list[SourceFileCandidate] = []

    for entry in tree:
        if entry.type != "blob" or not entry.path.startswith(prefix):
            continue

        suffix = PurePosixPath(entry.path).suffix.lower()
        source_type = INDEXED_SUFFIXES.get(suffix)
        if source_type is None:
            continue

        file_type, language = source_type
        candidates.append(
            SourceFileCandidate(
                path=entry.path,
                file_type=file_type,
                language=language,
                sha=entry.sha,
                size=entry.size or 0,
            )
        )

    candidates = sorted(candidates, key=lambda candidate: candidate.path)
    if limit is not None:
        return candidates[:limit]
    return candidates

