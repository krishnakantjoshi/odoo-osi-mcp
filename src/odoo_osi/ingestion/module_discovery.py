from dataclasses import dataclass
from pathlib import PurePosixPath

from odoo_osi.ingestion.contracts import GitHubTreeEntry


@dataclass(frozen=True)
class ModuleCandidate:
    technical_name: str
    path: str
    manifest_path: str


MANIFEST_FILENAMES = {"__manifest__.py", "__openerp__.py"}


def discover_module_candidates(tree: list[GitHubTreeEntry]) -> list[ModuleCandidate]:
    """Find Odoo module folders from repository tree entries."""
    candidates: list[ModuleCandidate] = []

    for entry in tree:
        if entry.type != "blob":
            continue

        path = PurePosixPath(entry.path)
        if path.name not in MANIFEST_FILENAMES:
            continue

        module_path = str(path.parent)
        if module_path == ".":
            continue

        candidates.append(
            ModuleCandidate(
                technical_name=path.parent.name,
                path=module_path,
                manifest_path=entry.path,
            )
        )

    return sorted(candidates, key=lambda candidate: candidate.path)
