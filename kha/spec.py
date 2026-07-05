"""One spec, three faithful backends.

A rule is written once as a Python expression over named integer parameters. The same source is
compiled to Lean 4 (the kernel certifies concrete results), SMT-LIB (Z3 proves guardrails over all
inputs), and a Python callable (the runtime oracle). Because all three come from one source, the
thing the kernel checks, the thing Z3 attacks, and the thing that runs cannot silently diverge.

Supported forms: `a if c else b`, and/or/not, single comparisons, `+ - *`, `//` (integer
division), `min`/`max`, calls to earlier functions, names, integer literals.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass

Func = tuple[str, list[str], str]  # (name, params, expression)

_CMP = {ast.Lt: "<", ast.LtE: "≤", ast.Gt: ">", ast.GtE: "≥", ast.Eq: "=", ast.NotEq: "≠"}
_CMP_SMT = {ast.Lt: "<", ast.LtE: "<=", ast.Gt: ">", ast.GtE: ">=", ast.Eq: "=", ast.NotEq: "distinct"}
_BIN = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*"}


def _lean(n: ast.AST) -> str:
    if isinstance(n, ast.IfExp):
        return f"(if {_lean(n.test)} then {_lean(n.body)} else {_lean(n.orelse)})"
    if isinstance(n, ast.BoolOp):
        op = " ∧ " if isinstance(n.op, ast.And) else " ∨ "
        return "(" + op.join(_lean(v) for v in n.values) + ")"
    if isinstance(n, ast.UnaryOp):
        if isinstance(n.op, ast.Not):
            return f"(¬ {_lean(n.operand)})"
        if isinstance(n.op, ast.USub):
            return f"(- {_lean(n.operand)})"
    if isinstance(n, ast.Compare):
        assert len(n.ops) == 1, "chained comparisons unsupported"
        return f"({_lean(n.left)} {_CMP[type(n.ops[0])]} {_lean(n.comparators[0])})"
    if isinstance(n, ast.BinOp):
        if isinstance(n.op, ast.FloorDiv):
            return f"({_lean(n.left)} / {_lean(n.right)})"   # Int.div on nonneg = floor
        return f"({_lean(n.left)} {_BIN[type(n.op)]} {_lean(n.right)})"
    if isinstance(n, ast.Call):
        return f"({n.func.id} " + " ".join(_lean(a) for a in n.args) + ")"
    if isinstance(n, ast.Name):
        return n.id
    if isinstance(n, ast.Constant):
        return str(n.value)
    raise ValueError(f"lean: unsupported {ast.dump(n)}")


def _smt(n: ast.AST) -> str:
    if isinstance(n, ast.IfExp):
        return f"(ite {_smt(n.test)} {_smt(n.body)} {_smt(n.orelse)})"
    if isinstance(n, ast.BoolOp):
        op = "and" if isinstance(n.op, ast.And) else "or"
        return "(" + op + " " + " ".join(_smt(v) for v in n.values) + ")"
    if isinstance(n, ast.UnaryOp):
        if isinstance(n.op, ast.Not):
            return f"(not {_smt(n.operand)})"
        if isinstance(n.op, ast.USub):
            return f"(- {_smt(n.operand)})"
    if isinstance(n, ast.Compare):
        return f"({_CMP_SMT[type(n.ops[0])]} {_smt(n.left)} {_smt(n.comparators[0])})"
    if isinstance(n, ast.BinOp):
        if isinstance(n.op, ast.FloorDiv):
            return f"(div {_smt(n.left)} {_smt(n.right)})"
        return f"({_BIN[type(n.op)]} {_smt(n.left)} {_smt(n.right)})"
    if isinstance(n, ast.Call):
        f = n.func.id
        if f in ("min", "max"):
            a, b = _smt(n.args[0]), _smt(n.args[1])
            cmp = "<=" if f == "min" else ">="
            return f"(ite ({cmp} {a} {b}) {a} {b})"
        return f"({f} " + " ".join(_smt(a) for a in n.args) + ")"
    if isinstance(n, ast.Name):
        return n.id
    if isinstance(n, ast.Constant):
        return str(n.value)
    raise ValueError(f"smt: unsupported {ast.dump(n)}")


def _parse(expr: str) -> ast.AST:
    return ast.parse(expr, mode="eval").body


def emit_lean(funcs: list[Func]) -> str:
    out = []
    for name, params, expr in funcs:
        sig = " ".join(f"({p} : Int)" for p in params)
        out.append(f"def {name} {sig} : Int := {_lean(_parse(expr))}")
    return "\n".join(out) + "\n"


def emit_smt(funcs: list[Func]) -> str:
    out = []
    for name, params, expr in funcs:
        sig = " ".join(f"({p} Int)" for p in params)
        out.append(f"(define-fun {name} ({sig}) Int {_smt(_parse(expr))})")
    return "\n".join(out) + "\n"


def build_oracle(funcs: list[Func]) -> dict:
    """Execute the spec into real Python callables, the runtime oracle."""
    ns: dict = {"min": min, "max": max}
    for name, params, expr in funcs:
        exec(f"def {name}({', '.join(params)}):\n    return {expr}\n", ns)
    return ns


@dataclass(frozen=True)
class Spec:
    """A named set of functions with its three backends."""
    funcs: list[Func]

    def lean(self) -> str:
        return emit_lean(self.funcs)

    def smt(self) -> str:
        return emit_smt(self.funcs)

    def oracle(self) -> dict:
        return build_oracle(self.funcs)
