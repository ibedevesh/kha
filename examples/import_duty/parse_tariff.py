"""Parse the Customs Tariff First Schedule (layout text) into an HSN -> BCD lookup.

    pdftotext -layout customs_tariff_first_schedule.pdf tariff.txt
    python parse_tariff.py tariff.txt

Grounding, not invention: each rate comes straight from the government's published schedule. Only
ad-valorem ("NN%") standard rates are kept; specific duties ("Rs 42 per kg") are counted and
skipped so coverage is transparent.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

OUT = Path(__file__).parent / "data" / "hsn_bcd.json"
_HSN = re.compile(r"^\s*(\d{4}(?: \d{2}){2})\s+(.*\S)\s*$")
_RATE = re.compile(r"\d{1,3}(?:\.\d+)?%|\bFree\b|Rs\.?\s*\d+")


def parse(text: str) -> tuple[dict, dict]:
    rows, adval, specific, free = {}, 0, 0, 0
    for line in text.splitlines():
        m = _HSN.match(line)
        if not m:
            continue
        hsn, rest = m.group(1).replace(" ", ""), m.group(2)
        tokens = _RATE.findall(rest)
        if not tokens:
            continue
        std = tokens[-2] if len(tokens) >= 2 else tokens[-1]
        desc = rest[:rest.find(tokens[0])].strip(" .-")
        if std.endswith("%"):
            adval += 1
            rows[hsn] = {"bcd": float(std[:-1]), "desc": desc[:80]}
        elif std.lower() == "free":
            free += 1
            rows.setdefault(hsn, {"bcd": 0.0, "desc": desc[:80]})
        else:
            specific += 1
    return rows, {"advalorem": adval, "free": free, "specific_skipped": specific, "usable": len(rows)}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: python parse_tariff.py <tariff.txt>")
    rows, stats = parse(Path(sys.argv[1]).read_text(errors="ignore"))
    OUT.write_text(json.dumps(rows, separators=(",", ":")))
    print(f"{stats}  -> wrote {OUT}")
