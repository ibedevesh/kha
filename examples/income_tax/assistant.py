"""Two assistants over the same model, for the comparison.

  engine_chat, the model only extracts the taxpayer's facts; the environment computes the tax.
  plain_chat, the model computes the tax itself from the rules. No environment.
"""
from __future__ import annotations

import json
import re

import engine as E
from kha import default_llm

_ENGINE_SYSTEM = (
    "You are an India income-tax assistant (FY 2025-26). You never do arithmetic, not even converting "
    "lakh/crore to rupees; the environment does all of it. Chat and gather: entity (individual/company), "
    "the income as a bare number PLUS its unit, and regime/age for individuals. Do NOT multiply the "
    "income out, '2.5 crore' is amount 2.5, unit crore. Ask one follow-up if needed. Reply each turn "
    'with ONLY JSON: {"reply": str, "ready": bool, "entity": "individual"|"company", "regime": "new"|"old", '
    '"age": int, "income_amount": number, "income_unit": "rupees"|"lakh"|"crore", "domestic": bool, '
    '"small_turnover": bool}. Set ready true when you have entity + income_amount. Relay the figure unchanged.')

_UNIT = {"rupees": 1, "rupee": 1, "rs": 1, "lakh": 100000, "lakhs": 100000, "crore": 10000000, "crores": 10000000}


def _rupees(amount, unit) -> int:
    """The environment does the lakh/crore scaling, never the model."""
    return int(round(float(amount) * _UNIT.get(str(unit).lower().strip(), 1)))

_PLAIN_SYSTEM = (
    "You are an India income-tax assistant (FY 2025-26). Compute the total tax payable yourself, "
    "including surcharge and 4% cess, under the stated regime. New-regime slabs: 0-4L nil, 4-8L 5%, "
    "8-12L 10%, 12-16L 15%, 16-20L 20%, 20-24L 25%, >24L 30%; 87A rebate makes tax nil up to 12L. "
    "Surcharge 10/15/25% above 50L/1cr/2cr with marginal relief. Ask a follow-up if you need the "
    'income or regime. Reply with ONLY JSON: {"reply": str, "ready": bool, "total_tax": int}.')


def _json(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.DOTALL)
    try:
        return json.loads(m.group(0)) if m else {"reply": text}
    except Exception:
        return {"reply": text}


def engine_chat(messages: list[dict], llm=None) -> dict:
    llm = llm or default_llm()
    f = _json(llm(_ENGINE_SYSTEM, messages))
    reply = (f.get("reply") or "").strip()
    if not (f.get("ready") and f.get("income_amount") is not None):
        return {"reply": reply}
    f["total_income"] = _rupees(f["income_amount"], f.get("income_unit", "rupees"))  # env scales, not the model
    r = E.route(f)
    return {"reply": reply, "value": r["value"], "steps": E.breakdown(f), "certified": E.CERTIFIED}


def plain_chat(messages: list[dict], llm=None) -> dict:
    llm = llm or default_llm()
    f = _json(llm(_PLAIN_SYSTEM, messages))
    out = {"reply": (f.get("reply") or "").strip()}
    if f.get("ready") and f.get("total_tax") is not None:
        out["value"] = int(f["total_tax"])
    return out
