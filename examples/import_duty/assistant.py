"""Two assistants over the same model, for the comparison.

  engine_chat, the model only extracts (HSN, value, IGST rate); the environment looks up the real
                Basic Customs Duty and computes the duty. The figure is the environment's.
  plain_chat, the model recalls the rate and does the whole cascade itself. No environment.
"""
from __future__ import annotations

import json
import re

import engine as E
from kha import default_llm

_ENGINE_SYSTEM = (
    "You are an India import-duty assistant. You never do arithmetic, not even converting lakh/crore "
    "to rupees, and never state a duty rate from memory; the environment looks up the official Basic "
    "Customs Duty and computes the duty. Chat and gather: the 8-digit HSN code, the assessable (CIF) "
    "value as a bare number PLUS its unit (do NOT multiply it out, '20 lakh' is amount 20, unit lakh), "
    "and the IGST rate (5/12/18/28). Ask one short follow-up if something is missing. Reply each turn "
    'with ONLY JSON: {"reply": str, "ready": bool, "hsn": str, "value_amount": number, '
    '"value_unit": "rupees"|"lakh"|"crore", "igst_rate": number}. Set ready true only when you have all '
    "three. Relay the returned figure unchanged.")

_UNIT = {"rupees": 1, "rupee": 1, "rs": 1, "lakh": 100000, "lakhs": 100000, "crore": 10000000, "crores": 10000000}


def _rupees(amount, unit) -> int:
    """The environment does the lakh/crore scaling, never the model."""
    return int(round(float(amount) * _UNIT.get(str(unit).lower().strip(), 1)))

_PLAIN_SYSTEM = (
    "You are an India import-duty assistant. Given an HSN code, assessable value and IGST rate, recall "
    "the Basic Customs Duty rate for that HSN and compute the TOTAL import duty yourself. Method: "
    "BCD = bcd% of value; SWS = 10% of BCD; IGST = igst% of (value + BCD + SWS); total = BCD + SWS + "
    'IGST. Ask a follow-up if you need the value or IGST rate. Reply with ONLY JSON: '
    '{"reply": str, "ready": bool, "total_duty": int}.')


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
    if not (f.get("ready") and f.get("hsn") and f.get("value_amount") is not None and f.get("igst_rate") is not None):
        return {"reply": reply}
    rate = E.bcd_rate(str(f["hsn"]))
    if rate is None:
        return {"reply": reply + f" (No ad-valorem Basic Customs Duty on file for HSN {f['hsn']}.)"}
    av = _rupees(f["value_amount"], f.get("value_unit", "rupees"))   # env scales, not the model
    igst, bcd = float(f["igst_rate"]), rate["bcd"],
    return {"reply": reply, "value": E.total_duty(av, bcd, igst),
            "steps": E.breakdown(av, bcd, igst), "certified": E.CERTIFIED,
            "meta": {"hsn": str(f["hsn"]), "bcd": bcd, "desc": rate.get("desc", "")}}


def plain_chat(messages: list[dict], llm=None) -> dict:
    llm = llm or default_llm()
    f = _json(llm(_PLAIN_SYSTEM, messages))
    out = {"reply": (f.get("reply") or "").strip()}
    if f.get("ready") and f.get("total_duty") is not None:
        out["value"] = int(f["total_duty"])
    return out
