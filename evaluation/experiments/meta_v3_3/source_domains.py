"""Evaluate explicit numeric source-domain comparisons without executing source text."""

# ruff: noqa: INP001 - Repository experiment helper.

from __future__ import annotations

import ast
import math
import operator
from functools import cache
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Callable


ARITHMETIC: dict[type[ast.operator], Callable[[float, float], float]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}
COMPARISONS: dict[type[ast.cmpop], Callable[[float, float], bool]] = {
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
}


@cache
def clauses(text: str) -> tuple[ast.Compare, ...]:
    result = []
    for clause in text.split(';'):
        try:
            node = ast.parse(clause.strip(), mode='eval').body
        except SyntaxError:
            continue  # Prose domains are not silently translated into inequalities.
        if isinstance(node, ast.Compare):
            result.append(node)
    return tuple(result)


def number(node: ast.expr, values: dict) -> float:
    if (
        isinstance(node, ast.Constant)
        and isinstance(node.value, (int, float))
        and not isinstance(node.value, bool)
    ):
        return float(node.value)
    if isinstance(node, ast.Name):
        return float(values[node.id])
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        return (-1 if isinstance(node.op, ast.USub) else 1) * number(node.operand, values)
    if isinstance(node, ast.BinOp) and type(node.op) in ARITHMETIC:
        return ARITHMETIC[type(node.op)](number(node.left, values), number(node.right, values))
    raise NotImplementedError


def within_named_domain(text: str, values: dict) -> bool:
    """Enforce parseable numeric clauses, including chained and joint constraints.

    Missing covariates retain their existing missing-input decisions. Unsupported
    prose or operations retain the prior unresolved status; they are never run.
    """
    for clause in clauses(text):
        if any(type(op) not in COMPARISONS for op in clause.ops):
            continue
        try:
            numbers = [number(node, values) for node in [clause.left, *clause.comparators]]
        except (KeyError, TypeError, NotImplementedError):
            continue
        except (ArithmeticError, ValueError):
            return False
        if not all(math.isfinite(value) for value in numbers):
            return False
        if not all(
            COMPARISONS[type(op)](left, right)
            for op, left, right in zip(clause.ops, numbers[:-1], numbers[1:], strict=True)
        ):
            return False
    return True
