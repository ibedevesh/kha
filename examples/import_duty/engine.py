"""Import-duty runtime, executes the oracle generated from the proven spec.

The duty functions are not hand-written here; they come from the same spec the kernel certified
and Z3 proved (via prove.py). `CERTIFIED` is True only if that certificate is present and passed.
Rates are scaled x10 integers inside the engine (30% -> 300) so fractional rates stay exact.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parents[1]))          # repo root, to import kha
sys.path.insert(0, str(HERE))                     # to import spec

from kha import build_oracle, is_certified        # noqa: E402
from spec import FUNCS                             # noqa: E402

_O = build_oracle(FUNCS)
_CERT = HERE / "proof_certificate.json"
CERTIFIED = is_certified(_CERT)

_HSN_BCD = json.loads((HERE / "data" / "hsn_bcd.json").read_text())


def bcd_rate(hsn: str) -> dict | None:
    """Real Basic Customs Duty rate for an 8-digit HSN, from the First Schedule."""
    return _HSN_BCD.get("".join(ch for ch in str(hsn) if ch.isdigit()))


def _r10(x: float) -> int:
    return int(round(x * 10))


def duty(av: float, bcd: float, igst: float, cess: float = 0.0) -> dict:
    av, b, g, c = int(round(av)), _r10(bcd), _r10(igst), _r10(cess),
    return {"av": av, "bcd": _O["bcd"](av, b), "sws": _O["sws"](av, b),
            "igst_base": _O["igstbase"](av, b), "igst": _O["igst"](av, b, g),
            "cess": _O["cess"](av, b, c), "total_duty": _O["totalduty"](av, b, g, c)}


def total_duty(av: float, bcd: float, igst: float, cess: float = 0.0) -> int:
    return int(_O["totalduty"](int(round(av)), _r10(bcd), _r10(igst), _r10(cess)))


def breakdown(av: float, bcd: float, igst: float, cess: float = 0.0) -> list[dict]:
    d = duty(av, bcd, igst, cess)
    r = lambda n: f"₹{n:,.0f}"
    steps = [
        {"head": "Assessable Value (CIF)", "detail": "The customs value the duty is charged on.", "amount": d["av"]},
        {"head": f"Basic Customs Duty @ {bcd:g}%", "detail": f"{bcd:g}% of the value = {r(d['bcd'])}.", "amount": d["bcd"]},
        {"head": "Social Welfare Surcharge @ 10%", "detail": f"10% of the BCD only = {r(d['sws'])}.", "amount": d["sws"]},
        {"head": f"IGST @ {igst:g}%", "detail": f"on value + BCD + SWS = {r(d['igst_base'])} → {r(d['igst'])}.", "amount": d["igst"]}
    ]
    if cess:
        steps.append({"head": f"Compensation Cess @ {cess:g}%", "detail": f"on {r(d['igst_base'])} = {r(d['cess'])}.", "amount": d["cess"]})
    steps.append({"head": "Total import duty payable", "detail": "", "amount": d["total_duty"], "total": True})
    return steps
