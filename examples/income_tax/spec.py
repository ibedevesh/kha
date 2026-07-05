"""The Finance Bill, 2026 tax engine — the SINGLE SOURCE.

Each entry is (name, params, expression). engine/fn_translate.py compiles ALL of these into
Lean (kernel), SMT-LIB (Z3), and Python (oracle) — so the three can never drift. Every constant
is cited to the bill (data/Finance_Bill.layout.txt) in the comment beside it.

Currently modelled: INDIVIDUAL under 60, old regime — First Schedule, Part I, Paragraph A(I),
surcharge Table 1 Sl. No. 1, marginal relief (sub-section 5), cess (sub-section 6).
"""

# ─────────────────────────────────────────────────────────────────────────────────────────
# SLAB BANDS — the SINGLE SOURCE for slab rates. `slab_expr` generates the slab expression that
# fn_translate compiles into the kernel-verified Lean + Z3 + oracle; `slab_line_data` produces the
# per-band derivation shown to the user. Both read THIS data — no hand-copied bands anywhere.
# Each band = (lower bound, upper bound or None for the top band, rate %). Cited to the bill /
# Finance Act: new regime s.115BAC(1A); old regime First Schedule Part I-A Paragraph A(I/II/III).
SLABS = {
    "new":     [(0, 400000, 0), (400000, 800000, 5), (800000, 1200000, 10), (1200000, 1600000, 15),
                (1600000, 2000000, 20), (2000000, 2400000, 25), (2400000, None, 30)],
    "old_u60": [(0, 250000, 0), (250000, 500000, 5), (500000, 1000000, 20), (1000000, None, 30)],
    "old_60":  [(0, 300000, 0), (300000, 500000, 5), (500000, 1000000, 20), (1000000, None, 30)],
    "old_80":  [(0, 500000, 0), (500000, 1000000, 20), (1000000, None, 30)],
}


def slab_expr(key: str) -> str:
    """Build the marginal-sum slab expression from the band table (feeds Lean/SMT/oracle)."""
    terms = []
    for lo, hi, rate in SLABS[key]:
        if rate == 0:
            continue
        span = f"(ti - {lo})" if hi is None else f"(min(ti, {hi}) - {lo})"
        terms.append(f"({rate} * {span} // 100 if ti > {lo} else 0)")
    return " + ".join(terms) or "0"


def slab_line_data(ti: int, key: str) -> list[dict]:
    """Per-band contribution for the on-screen derivation — same band data as the engine."""
    out = []
    for lo, hi, rate in SLABS[key]:
        if ti <= lo:
            break
        taxable = (ti if hi is None else min(ti, hi)) - lo
        out.append({"lo": lo, "hi": hi, "rate": rate, "taxable": taxable, "amount": rate * taxable // 100})
    return out


FUNCS: list[tuple[str, list[str], str]] = [
    # Slab tax — old regime, under 60 (First Schedule Part I-A Para A(I)); generated from SLABS.
    ("slab26", ["ti"], slab_expr("old_u60")),

    # Surcharge RATE by band — Paragraph F, Table 1, Sl. No. 1 (strict '>').
    ("surRate26", ["ti"],
     "0 if ti <= 5000000 else "
     "10 if ti <= 10000000 else "
     "15 if ti <= 20000000 else "
     "25 if ti <= 50000000 else 37"),

    ("surRaw26", ["ti"], "(surRate26(ti) * slab26(ti)) // 100"),

    # Threshold C for marginal relief (sub-section 5 Table, row for Sl. Nos. 1 & 2).
    ("marginC26", ["ti"],
     "0 if ti <= 5000000 else "
     "5000000 if ti <= 10000000 else "
     "10000000 if ti <= 20000000 else "
     "20000000 if ti <= 50000000 else 50000000"),

    ("taxPlusSur26", ["ti"], "slab26(ti) + surRaw26(ti)"),

    # Cap: To = Ro + So, Ro = (tax+surcharge) at threshold C, So = income − C.
    ("marginCap26", ["ti"],
     "taxPlusSur26(ti) if marginC26(ti) == 0 else "
     "taxPlusSur26(marginC26(ti)) + (ti - marginC26(ti))"),

    ("taxSurRelieved26", ["ti"], "min(taxPlusSur26(ti), marginCap26(ti))"),

    # 4% Health & Education Cess (sub-section 6).
    ("cess26", ["ti"], "(4 * taxSurRelieved26(ti)) // 100"),

    ("tax26", ["ti"], "taxSurRelieved26(ti) + cess26(ti)"),

    # ─────────────────────────────────────────────────────────────────────────────────
    # ITEM 2a — AGE BRACKETS. First Schedule Part I Paragraph A(II) 60–79, A(III) 80+.
    # Only the slab thresholds change; surcharge/relief/cess (Table 1 Sl.1) are identical,
    # so those helpers just take `age` and reuse surRate26/marginC26.
    # Age-bracketed old-regime slab — all three brackets generated from SLABS (single source).
    ("slabInd", ["ti", "age"],
     f"({slab_expr('old_80')}) if age >= 80 else "
     f"({slab_expr('old_60')}) if age >= 60 else slab26(ti)"),

    ("surRawInd", ["ti", "age"], "(surRate26(ti) * slabInd(ti, age)) // 100"),
    ("taxPlusSurInd", ["ti", "age"], "slabInd(ti, age) + surRawInd(ti, age)"),
    ("marginCapInd", ["ti", "age"],
     "taxPlusSurInd(ti, age) if marginC26(ti) == 0 else "
     "taxPlusSurInd(marginC26(ti), age) + (ti - marginC26(ti))"),
    ("taxSurRelInd", ["ti", "age"], "min(taxPlusSurInd(ti, age), marginCapInd(ti, age))"),
    ("taxInd", ["ti", "age"], "taxSurRelInd(ti, age) + (4 * taxSurRelInd(ti, age)) // 100"),

    # ─────────────────────────────────────────────────────────────────────────────────
    # ITEM 2b — COMPANIES. Paragraph E: domestic 25% (turnover ≤400cr in FY23-24) else 30%;
    # foreign 35%. Surcharge Table 1 Sl.5 (domestic 7%/12%) & Sl.6 (foreign 2%/5%);
    # marginal relief Table 2 Sl.5 (thresholds 1cr, 10cr). Flags are Int 0/1.
    ("slabCo", ["ti", "domestic", "small"],
     "((25 * ti) // 100 if small == 1 else (30 * ti) // 100) if domestic == 1 else (35 * ti) // 100"),
    ("surRateCo", ["ti", "domestic"],
     "(0 if ti <= 10000000 else 7 if ti <= 100000000 else 12) if domestic == 1 else "
     "(0 if ti <= 10000000 else 2 if ti <= 100000000 else 5)"),
    ("surRawCo", ["ti", "domestic", "small"], "(surRateCo(ti, domestic) * slabCo(ti, domestic, small)) // 100"),
    ("marginCCo", ["ti"], "0 if ti <= 10000000 else 10000000 if ti <= 100000000 else 100000000"),
    ("taxPlusSurCo", ["ti", "domestic", "small"], "slabCo(ti, domestic, small) + surRawCo(ti, domestic, small)"),
    ("marginCapCo", ["ti", "domestic", "small"],
     "taxPlusSurCo(ti, domestic, small) if marginCCo(ti) == 0 else "
     "taxPlusSurCo(marginCCo(ti), domestic, small) + (ti - marginCCo(ti))"),
    ("taxSurRelCo", ["ti", "domestic", "small"], "min(taxPlusSurCo(ti, domestic, small), marginCapCo(ti, domestic, small))"),
    ("taxCo", ["ti", "domestic", "small"], "taxSurRelCo(ti, domestic, small) + (4 * taxSurRelCo(ti, domestic, small)) // 100"),

    # ─────────────────────────────────────────────────────────────────────────────────
    # ITEM 1 — DIVIDEND / CAPITAL-GAINS SURCHARGE CARVE-OUT (Paragraph F, Table 1, Sl.1).
    # Two facts from the bill: (a) the 25%/37% surcharge bands test income EXCLUDING
    # dividend & 111A/112/112A capital gains; (b) the surcharge rate on the tax attributable
    # to that dividend/CG part "shall not exceed 15 per cent." `normal` = income excluding
    # divCg (= the "excl" figure); `divcg` = dividend + capital-gains income.
    # SCOPE (honest boundary): this models the surcharge-rate carve-out; it does NOT layer
    # marginal relief on top (the relief×carve-out interaction is legally ambiguous), so it is
    # exact only OUTSIDE the narrow relief bands just above 50L/1cr/2cr/5cr. divCg is taxed at
    # slab rates stacked above normal income (marginal stacking).
    ("surRateExcl", ["ti", "excl"],
     "0 if ti <= 5000000 else "
     "10 if ti <= 10000000 else "
     "37 if excl > 50000000 else "     # excl > 5cr
     "25 if excl > 20000000 else "     # excl > 2cr
     "15"),                            # TI > 1cr but excl <= 2cr (clause v)
    ("taxNormalPart", ["normal", "age"], "slabInd(normal, age)"),
    ("taxDivPart",    ["normal", "divcg", "age"], "slabInd(normal + divcg, age) - slabInd(normal, age)"),
    ("surchargeDiv", ["normal", "divcg", "age"],
     "(surRateExcl(normal + divcg, normal) * taxNormalPart(normal, age)) // 100 + "
     "(min(surRateExcl(normal + divcg, normal), 15) * taxDivPart(normal, divcg, age)) // 100"),
    ("taxIndDiv", ["normal", "divcg", "age"],
     "(slabInd(normal + divcg, age) + surchargeDiv(normal, divcg, age)) + "
     "(4 * (slabInd(normal + divcg, age) + surchargeDiv(normal, divcg, age))) // 100"),

    # AI-style NAIVE comparator: includes divCg in the threshold test AND applies the full
    # rate to the whole tax (the mistake the carve-out exists to prevent). Used only to prove
    # the carve-out never raises tax.
    ("taxIndNaive", ["normal", "divcg", "age"],
     "(slabInd(normal + divcg, age) + (surRate26(normal + divcg) * slabInd(normal + divcg, age)) // 100) + "
     "(4 * (slabInd(normal + divcg, age) + (surRate26(normal + divcg) * slabInd(normal + divcg, age)) // 100)) // 100"),

    # ─────────────────────────────────────────────────────────────────────────────────
    # NEW REGIME (Section 115BAC(1A)) — the statutory DEFAULT for individuals now.
    # Slabs (FY25-26): ≤4L nil; 4–8L 5%; 8–12L 10%; 12–16L 15%; 16–20L 20%; 20–24L 25%; >24L 30%.
    # 87A rebate + marginal relief: tax nil up to 12L; just above, capped at (income − 12L).
    # Surcharge caps at 25% in the new regime (NO 37% band). 4% cess. Surcharge marginal relief too.
    ("slabNew", ["ti"], slab_expr("new")),

    # 87A: full rebate ≤12L; just above, marginal relief caps tax at (income − 12L).
    ("baseNew", ["ti"], "0 if ti <= 1200000 else min(slabNew(ti), ti - 1200000)"),

    # New-regime surcharge rate: 0 / 10 / 15 / 25 (capped at 25 — no 37% band).
    ("surRateNew", ["ti"],
     "0 if ti <= 5000000 else 10 if ti <= 10000000 else 15 if ti <= 20000000 else 25"),
    ("marginCNew", ["ti"],
     "0 if ti <= 5000000 else 5000000 if ti <= 10000000 else 10000000 if ti <= 20000000 else 20000000"),
    ("taxPlusSurNew", ["ti"], "baseNew(ti) + (surRateNew(ti) * baseNew(ti)) // 100"),
    ("marginCapNew", ["ti"],
     "taxPlusSurNew(ti) if marginCNew(ti) == 0 else "
     "taxPlusSurNew(marginCNew(ti)) + (ti - marginCNew(ti))"),
    ("taxSurRelNew", ["ti"], "min(taxPlusSurNew(ti), marginCapNew(ti))"),
    ("taxNew", ["ti"], "taxSurRelNew(ti) + (4 * taxSurRelNew(ti)) // 100"),
]
