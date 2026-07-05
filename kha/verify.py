"""Lean verification, the trust anchor.

`verify(src, thm)` compiles a Lean source and reports, structurally:
  compiled, typechecked with no hard error (exit code + an error-line regex).
  axioms, the exact axiom set `thm` depends on, parsed from `#print axioms`.
  certified, compiled, an axiom set was printed, and it contains no cheat axiom.

A proof with zero axioms (`by decide` on concrete data) is the strongest result. `sorry` and
`native_decide` stamp cheat axioms and are never reported as certified.
"""
from __future__ import annotations

import os
import re
import subprocess
import tempfile
from pathlib import Path

STD_AXIOMS = frozenset({"propext", "Quot.sound", "Classical.choice"})
CHEAT_AXIOMS = ("sorryAx", "ofReduceBool", "ofReduceNat", "native")
_ERROR_LINE = re.compile(r":\d+:\d+:\s*error", re.IGNORECASE)


def _run_lean(src: str) -> tuple[int, str]:
    env = dict(os.environ, PATH=str(Path.home() / ".elan/bin") + ":" + os.environ.get("PATH", ""))
    with tempfile.NamedTemporaryFile("w", suffix=".lean", delete=False) as f:
        f.write(src)
        path = f.name
    try:
        p = subprocess.run(["lean", path], capture_output=True, text=True, env=env)
    finally:
        Path(path).unlink(missing_ok=True)
    out = "\n".join(l for l in (p.stdout + p.stderr).splitlines() if "canonicalize" not in l)
    return p.returncode, out


def axioms_of(out: str, thm: str) -> set[str] | None:
    if f"'{thm}' does not depend on any axioms" in out:
        return set()
    needle = f"'{thm}' depends on axioms:"
    line = next((l for l in out.splitlines() if needle in l), None)
    if line is None:
        return None
    return set(re.findall(r"[A-Za-z_][\w.]*", line.split("axioms:", 1)[1]))


def verify(src: str, thm: str) -> dict:
    rc, out = _run_lean(src)
    compiled = rc == 0 and not _ERROR_LINE.search(out)
    axioms = axioms_of(out, thm)
    no_cheat = axioms is not None and not any(c in a for a in axioms for c in CHEAT_AXIOMS)
    certified = compiled and axioms is not None and no_cheat
    return {"compiled": compiled, "axioms": axioms, "certified": certified, "output": out}
