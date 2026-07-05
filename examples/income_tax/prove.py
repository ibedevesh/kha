"""Prove the income-tax engine once. Writes proof_certificate.json next to this file.

    export PATH="$HOME/.elan/bin:$PATH"
    python prove.py

Lean certifies concrete tax figures across regimes; Z3 proves, over all incomes up to Rs 20 crore
that tax is non-negative, never exceeds income, and has no single-rupee cliff.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root
sys.path.insert(0, str(Path(__file__).parent))                # for spec
from kha import prove  # noqa: E402
from spec import FUNCS  # noqa: E402

HI = 200_000_000
CERT = Path(__file__).parent / "proof_certificate.json"

FIGURES = [
    ("taxNew", [1200000], "new regime 12L (87A rebate to nil)"),
    ("taxNew", [3000000], "new regime 30L"),
    ("taxNew", [25000000], "new regime 2.5cr (surcharge)"),
    ("taxInd", [2100000, 45], "old regime 21L, age 45"),
    ("taxCo", [120000000, 1, 1], "domestic company 12cr, small turnover"),
]

GUARDRAILS = [
    ("tax >= 0 (new regime)",
     f"(declare-const t Int)(assert (and (>= t 0)(<= t {HI})))(assert (< (taxNew t) 0))"),
    ("tax <= income (new regime)",
     f"(declare-const t Int)(assert (and (>= t 0)(<= t {HI})))(assert (> (taxNew t) t))"),
    ("no single-rupee cliff (new regime)",
     f"(declare-const t Int)(assert (and (>= t 0)(< t {HI})))(assert (> (- (taxNew (+ t 1)) (taxNew t)) 5))"),
]

if __name__ == "__main__":
    prove(FUNCS, FIGURES, GUARDRAILS, CERT, note="income tax, one-time Lean+Z3 proof")
