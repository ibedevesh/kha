# Import duty (India)

An assistant that computes total import duty from the **official Basic Customs Duty** for an HSN
code plus the statutory surcharge and IGST cascade. The rules are proven once; the model only
extracts inputs.

- `spec.py`, the one source (BCD → SWS = 10% of BCD → IGST on AV+BCD+SWS → cess).
- `data/hsn_bcd.json`, 11,972 real BCD rates parsed from the Customs Tariff First Schedule (see `data/SOURCE.md`).
- `prove.py`, one-time Lean + Z3 proof → `proof_certificate.json`.
- `engine.py`, runtime; executes the oracle from the proven spec, looks up the real rate.
- `assistant.py`, `serve.py`, `ui.html`, `compare.html`, chat + side-by-side comparison.

## Run

```bash
export PATH="$HOME/.elan/bin:$PATH"     # Lean, for proving
python prove.py                         # once, certifies figures + guardrails

export KHA_BASE_URL=... KHA_API_KEY=... KHA_MODEL=...   # your model
python serve.py                         # http://127.0.0.1:8800/  and  /compare
```

## What the numbers show

Same method and inputs given to both a general model and the environment:

| Import | Real BCD | Environment | A general model |
|---|---|---|---|
| Motor car (HSN 87032391), ₹20L, IGST 28% | 125% | **₹40,80,000** | ~₹24,31,200 |

The general model was wrong on **5/5** test imports, understating duty by roughly **20-50%**, it
both misremembers the published rate and mishandles the cascade (charging IGST on the wrong base).
The environment is exact on every input and kernel-certified once.

Source: Customs Tariff Act First Schedule (CBIC); IGST under the GST law.
