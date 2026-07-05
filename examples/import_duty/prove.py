"""Prove the import-duty engine once. Writes proof_certificate.json next to this file.

    export PATH="$HOME/.elan/bin:$PATH"   # Lean, for the kernel step
    python prove.py

Lean certifies concrete duty figures; Z3 proves, for every rate used, that duty is non-negative
and non-decreasing in the assessable value, over all values up to Rs 20 crore.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root, to import kha
from kha import prove  # noqa: E402
from spec import FUNCS  # noqa: E402

HI = 200_000_000
CERT = Path(__file__).parent / "proof_certificate.json"

# concrete figures to kernel-certify: (func, [av, bcd×10, igst×10, cess×10], label)
FIGURES = [
    ("totalduty", [1000000, 300, 50, 0], "cashew in shell 30% / IGST 5%"),
    ("totalduty", [2000000, 1250, 280, 0], "motor car 125% / IGST 28%"),
    ("totalduty", [80000, 0, 180, 0], "personal computer 0% / IGST 18%"),
    ("totalduty", [950000, 125, 180, 0], "12.5% BCD / IGST 18% (fractional rate)"),
    ("totalduty", [12500000, 300, 280, 120], "30% + IGST 28% + 12% comp cess"),
]

# guardrails: assert a VIOLATION over all values for each rate; unsat = the property holds.
_RATES = [(300, 50, 0), (1250, 280, 0), (0, 180, 0), (125, 180, 0), (300, 280, 120)]
GUARDRAILS = []
for b, g, c in _RATES:
    tag = f"bcd={b/10:g}% igst={g/10:g}% cess={c/10:g}%"
    GUARDRAILS.append((f"duty >= 0 ({tag})",
        f"(declare-const av Int)(assert (and (>= av 0)(<= av {HI})))(assert (< (totalduty av {b} {g} {c}) 0))"))
    GUARDRAILS.append((f"monotonic in value ({tag})",
        f"(declare-const av Int)(assert (and (>= av 0)(< av {HI})))(assert (> (totalduty av {b} {g} {c}) (totalduty (+ av 1) {b} {g} {c})))"))


if __name__ == "__main__":
    prove(FUNCS, FIGURES, GUARDRAILS, CERT, note="import duty, one-time Lean+Z3 proof")
