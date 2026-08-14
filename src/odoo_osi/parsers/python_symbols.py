import ast
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PythonSymbol:
    symbol_type: str
    name: str | None
    odoo_model: str | None
    inherited_model: str | None
    line_start: int
    line_end: int
    metadata: dict[str, Any]


def parse_python_symbols(content: str) -> list[PythonSymbol]:
    """Extract Odoo model class signals from Python source."""
    tree = ast.parse(content)
    symbols: list[PythonSymbol] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue

        assignments = _class_assignments(node)
        odoo_model = _string_value(assignments.get("_name"))
        inherited_model = _inherit_value(assignments.get("_inherit"))

        if odoo_model or inherited_model:
            symbols.append(
                PythonSymbol(
                    symbol_type="odoo_model",
                    name=node.name,
                    odoo_model=odoo_model,
                    inherited_model=inherited_model,
                    line_start=node.lineno,
                    line_end=getattr(node, "end_lineno", node.lineno),
                    metadata={
                        "_description": _string_value(assignments.get("_description")),
                        "_inherits": _raw_literal(assignments.get("_inherits")),
                    },
                )
            )

    return symbols


def _class_assignments(node: ast.ClassDef) -> dict[str, ast.AST]:
    assignments: dict[str, ast.AST] = {}
    for statement in node.body:
        if isinstance(statement, ast.Assign):
            for target in statement.targets:
                if isinstance(target, ast.Name):
                    assignments[target.id] = statement.value
        elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
            assignments[statement.target.id] = statement.value
    return assignments


def _string_value(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _inherit_value(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.List | ast.Tuple):
        values = [
            item.value
            for item in node.elts
            if isinstance(item, ast.Constant) and isinstance(item.value, str)
        ]
        return ",".join(values) if values else None
    return None


def _raw_literal(node: ast.AST | None) -> Any:
    if node is None:
        return None
    try:
        return ast.literal_eval(node)
    except ValueError:
        return None
