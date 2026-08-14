import re

ODOO_BRANCH_PATTERN = re.compile(r"^(?P<major>\d{1,2})\.0$")


def parse_odoo_version_branch(branch_name: str) -> str | None:
    """Return an Odoo version like 18.0 when a branch follows OCA conventions."""
    match = ODOO_BRANCH_PATTERN.match(branch_name)
    if not match:
        return None
    return branch_name


def is_odoo_version_branch(branch_name: str) -> bool:
    return parse_odoo_version_branch(branch_name) is not None


def odoo_version_sort_key(version: str) -> tuple[int, int]:
    major, minor = version.split(".", maxsplit=1)
    return int(major), int(minor)
