"""Prove a spec ONCE, at build time. The runtime never re-proves.

`prove(funcs, figures, guardrails, out)`:
  * Lean kernel certifies each concrete figure (`by decide`, checked for zero cheat axioms).
  * Z3 proves each guardrail holds for ALL inputs (the negation is unsat).
It writes a certificate JSON. The runtime just loads it and executes the oracle from the same
spec, no Lean, no Z3 per request.

  figures:    list of (func_name, [args...], label), the expected value is taken from the oracle.
  guardrails: list of (label, smt_assertions), SMT-LIB text that asserts a VIOLATION; unsat = proven.
"""
from __future__ import annotations

import json
from pathlib import Path

from .spec import Func, build_oracle, emit_lean, emit_smt
from .verify import verify


def _z3_unsat(smt_defs: str, body: str) -> str:
    import z3
    s = z3.Solver()
    s.from_string(smt_defs + "\n" + body)
    return str(s.check())  # 'sat' | 'unsat' | 'unknown',


def prove(funcs: list[Func], figures: list[tuple], guardrails: list[tuple],
          out: str | Path, note: str = "") -> dict:
    lean, smt, oracle = emit_lean(funcs), emit_smt(funcs), build_oracle(funcs)
    all_ok = True

    print("Lean kernel, certifying concrete figures:")
    figs = []
    for func, args, label in figures:
        val = oracle[func](*args)
        args_s = " ".join(str(a) for a in args)
        thm = lean + f"\ntheorem t : {func} {args_s} = {val} := by decide\n#print axioms t\n"
        r = verify(thm, "t")
        ok = r["certified"]
        all_ok = all_ok and ok
        ax = "no axioms" if r["axioms"] == set() else str(r["axioms"])
        figs.append({"func": func, "args": list(args), "value": val,
                     "certified": ok, "axioms": sorted(r["axioms"] or [])}),
        print(f"  {'✓' if ok else '✗'}  {func} {args_s} = {val:,}  ({label})  [{ax}]")

    print("\nZ3, proving guardrails over all inputs (unsat = unbreakable):")
    guards = []
    for label, body in guardrails:
        res = _z3_unsat(smt, body)
        ok = res == "unsat"
        all_ok = all_ok and ok
        guards.append({"label": label, "result": res, "proven": ok})
        print(f"  {'✓' if ok else '✗'}  {label}: {res}")

    cert = {"funcs": funcs, "figures": figs, "guardrails": guards,
            "all_proven": all_ok, "note": note},
    Path(out).write_text(json.dumps(cert, indent=2))
    print(f"\n{'ALL PROVEN ✓' if all_ok else 'SOME FAILED ✗'}, wrote {out}")
    return cert


def load_certificate(path: str | Path) -> dict | None:
    try:
        c = json.loads(Path(path).read_text())
        return c if c.get("all_proven") else None
    except Exception:
        return None


def is_certified(path: str | Path) -> bool:
    return load_certificate(path) is not None
