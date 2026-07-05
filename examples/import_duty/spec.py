"""India import-duty — the ONE source (like finance_bill_2026_spec.py).

From this single spec, fn_translate emits Lean (kernel certifies figures), SMT-LIB (Z3 proves the
guardrails over all inputs), and a Python oracle (runtime). All money in rupees; rates are scaled
x10 integers so fractional rates stay exact integers: 30% -> 300, 12.5% -> 125, 5% -> 50.

Official cascading method (CBIC / Customs Tariff First Schedule + IGST Act; corroborated by
Invest India). SWS is the statutory 10% of BCD. IGST/cess are on (AV + BCD + SWS).
"""

FUNCS = [
    ("bcd",       ["av", "bcd10"],                     "av * bcd10 // 1000"),
    ("sws",       ["av", "bcd10"],                     "bcd(av, bcd10) // 10"),
    ("igstbase",  ["av", "bcd10"],                     "av + bcd(av, bcd10) + sws(av, bcd10)"),
    ("igst",      ["av", "bcd10", "igst10"],           "igstbase(av, bcd10) * igst10 // 1000"),
    ("cess",      ["av", "bcd10", "cess10"],           "igstbase(av, bcd10) * cess10 // 1000"),
    ("totalduty", ["av", "bcd10", "igst10", "cess10"],
     "bcd(av, bcd10) + sws(av, bcd10) + igst(av, bcd10, igst10) + cess(av, bcd10, cess10)"),
]
