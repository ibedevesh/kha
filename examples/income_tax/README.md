# Income tax (India)

An assistant that computes total income tax under the Finance Bill, 2026, slabs, surcharge
marginal relief and cess, for individuals (new/old regime, any age) and companies. The rules are
proven once; the model only extracts the taxpayer's facts.

- `spec.py`, the one source (all bands and thresholds cited to the bill).
- `prove.py`, one-time Lean + Z3 proof → `proof_certificate.json`.
- `engine.py`, runtime; routes facts to the proven function and derives the figure band by band.
- `assistant.py`, `serve.py`, `ui.html`, `compare.html`, chat + side-by-side comparison.

## Run

```bash
export PATH="$HOME/.elan/bin:$PATH"
python prove.py

export KHA_BASE_URL=... KHA_API_KEY=... KHA_MODEL=...
python serve.py            # http://127.0.0.1:8800/  and  /compare
```

## What the numbers show

Given the same, correct rules, a general model is exact on easy incomes but fails on the
high-value ones, silently and differently each run. On repeated crore-scale computations a
smaller model was exact on only ~10/24 runs and a stronger one ~23/24; the environment was exact
on every input, every run, kernel-certified. The figure the user sees is always the environment's.

The `new` regime is shown end to end; old-regime, company, and the dividend/capital-gains carve-out
are the same spec and are proven and routed by `engine.py`.

Source: Finance Bill, 2026.
