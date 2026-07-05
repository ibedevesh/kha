"""Income-tax runtime, executes the oracle generated from the proven spec.

Routes structured facts to the matching proven function and produces a per-band derivation. The
model never computes the figure; this does, from the same spec the kernel certified.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parents[1]))     # repo root, for kha
sys.path.insert(0, str(HERE))                # for spec

from kha import build_oracle, is_certified   # noqa: E402
import spec as SPEC                           # noqa: E402

O = build_oracle(SPEC.FUNCS)
CERTIFIED = is_certified(HERE / "proof_certificate.json")


def _inr(n: int) -> str:
    n = int(n); sign = "-" if n < 0 else ""; s = str(abs(n))
    if len(s) <= 3:
        return sign + s
    last3, rest, parts = s[-3:], s[:-3], []
    while len(rest) > 2:
        parts.insert(0, rest[-2:]); rest = rest[:-2]
    if rest:
        parts.insert(0, rest)
    return sign + ",".join(parts) + "," + last3


def _lakh(n: int) -> str:
    if n and n % 10000000 == 0:
        return f"₹{n // 10000000} crore"
    if n and n % 100000 == 0:
        return f"₹{n // 100000} lakh"
    return f"₹{_inr(n)}"


def _old_key(age: int) -> str:
    return "old_80" if age >= 80 else "old_60" if age >= 60 else "old_u60"


def _slab_lines(ti: int, key: str) -> list[dict]:
    out = []
    for b in SPEC.slab_line_data(ti, key):
        lo, hi, rate = b["lo"], b["hi"], b["rate"]
        if rate == 0:
            out.append({"label": f"{_lakh(lo)} - {_lakh(hi)}: nil", "amount": 0}); continue
        rng = f"above {_lakh(lo)} (on ₹{_inr(b['taxable'])})" if hi is None else f"{_lakh(lo)} - {_lakh(hi)}"
        out.append({"label": f"{rng} @ {rate}%", "amount": b["amount"]})
    return out


def route(f: dict) -> dict:
    """facts -> {value}. entity: individual|company; regime: new|old."""
    ti = int(f.get("total_income", 0))
    if f.get("entity") == "company":
        dom = 1 if f.get("domestic", True) else 0
        sml = 1 if f.get("small_turnover", True) else 0
        return {"value": O["taxCo"](ti, dom, sml), "kind": "company", "dom": dom, "sml": sml}
    age = int(f.get("age") or 45)
    divcg = int(f.get("dividend_cg_income", 0) or 0)
    if divcg > 0:
        return {"value": O["taxIndDiv"](ti - divcg, divcg, age), "kind": "divcg", "age": age, "divcg": divcg}
    if f.get("regime", "new") == "old":
        return {"value": O["taxInd"](ti, age), "kind": "old", "age": age}
    return {"value": O["taxNew"](ti), "kind": "new"}


def breakdown(f: dict) -> list[dict]:
    ti = int(f.get("total_income", 0))
    r = route(f)
    kind = r["kind"]
    money = lambda n: f"₹{_inr(n)}"
    steps: list[dict] = []
    if kind == "company":
        base = O["slabCo"](ti, r["dom"], r["sml"]); tsr = O["taxSurRelCo"](ti, r["dom"], r["sml"])
        br = 25 if (r["dom"] and r["sml"]) else 30 if r["dom"] else 35
        steps.append({"head": f"Corporate tax @ {br}%", "detail": f"{br}% × {money(ti)}.", "amount": base})
    elif kind == "new":
        slab = O["slabNew"](ti); base = O["baseNew"](ti); tsr = O["taxSurRelNew"](ti)
        head = "Income-tax, nil (87A rebate)" if ti <= 1200000 else \
               "Income-tax, marginal relief applies" if base < slab else "Income-tax on the slabs"
        steps.append({"head": head, "detail": f"New-regime slabs on {money(ti)}.", "amount": base, "lines": _slab_lines(ti, "new")})
    else:
        age = r["age"]; base = O["slabInd"](ti, age); tsr = O["taxSurRelInd"](ti, age)
        steps.append({"head": "Income-tax on the slabs", "detail": f"Old-regime slabs (age {age}) on {money(ti)}.",
                      "amount": base, "lines": _slab_lines(ti, _old_key(age))})
    sur = tsr - base
    if sur > 0:
        steps.append({"head": "Surcharge (with marginal relief)", "detail": "Charged on the income-tax.", "amount": sur})
    steps.append({"head": "Health & Education Cess @ 4%", "detail": f"4% of {money(tsr)}.", "amount": r["value"] - tsr})
    steps.append({"head": "Total tax payable", "detail": "", "amount": r["value"], "total": True})
    return steps
