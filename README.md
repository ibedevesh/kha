<h1 align="center">ख · Kha</h1>
<p align="center"><b>A proven space for AI to act in.</b></p>
<p align="center">The model moves freely, but every result is computed by an environment whose rules were<br>proven once with a kernel and an SMT solver. Not by the model.</p>

---

## What is Kha

Kha puts an AI inside an environment. The AI is free to think and act, but its actions are bounded
by the environment's rules, the same way a person is free yet still cannot break the laws of
physics. Because the AI only ever supplies inputs and the environment computes every result, you
can rely on the outcome completely: the AI cannot cheat, cannot escape, and cannot produce a wrong
result, whatever it believes.

On its own an AI is confidently unreliable. Asked to compute a real income tax or import duty, a
leading general-purpose model often returns a wrong figure and then justifies that wrong figure
fluently (our experiments below show exactly this). That is fine for a conversation, but it is why
you cannot yet hand an AI a job that has to be correct.

Kha changes the arrangement. You write the rules once, prove them, load them as an environment, and
drop the AI inside. The AI does not know the rules and never computes the answer, so it cannot game
them or slip past them. Every result comes from the proven environment, and every step the AI takes
inside it is recorded and checkable. For that task the AI becomes reliable, with a proof.

An environment is like a room with fixed laws. The AI moves freely inside, but the walls, the
floor, and gravity are not up for negotiation. Build one room per job (income tax, customs duty,
and so on), load it, and the AI inside can only ever act within its laws.

## How Kha works

The AI's only job is to supply inputs. The environment owns the computation and the output, and
because the AI never sees the rules, it cannot bend them or escape them.

**The recipe:**

1. **Find the rules**, from an authoritative public source. Never invent them.
2. **Write them once as a spec**, one source of truth (`spec.py`).
3. **Prove the spec once**, Lean kernel certifies figures (zero axioms), Z3 proves guardrails over all inputs.
4. **Load the proven environment**, runtime executes the oracle generated from the same spec.
5. **Drop a model in**, it extracts inputs; the environment computes results.

**Under the hood**, the three backends are generated from that single source, so they can never drift:

```
                         ┌──────────► Lean   →  kernel certifies concrete results (zero axioms)
   spec.py  (one source) ├──────────► SMT    →  Z3 proves guardrails over ALL inputs (unsat)
                         └──────────► oracle →  the function the runtime executes
                                                 (all three co-generated, they cannot drift)

   run:   model supplies inputs  →  environment computes the result  →  result + derivation
          (never the answer)         (the proven oracle)                (with a saved certificate)
```

The proof is a one-time build step. It writes a `proof_certificate.json`; the runtime just loads it.

Because every consequential step happens inside the environment, the whole run is inspectable: you
get the result, its derivation, and a saved certificate. The AI can say anything; only the
environment's proven figure reaches the user. See [Results](#results) for the measured gap between a
general model on its own and the same task run inside a Kha environment.
See [`theory.md`](theory.md) for the intuitions behind the design.

## Quickstart

```bash
git clone https://github.com/ibedevesh/kha && cd kha
pip install -e .                        # installs kha (dep: z3-solver)
# Lean (elan) is needed only for the proving step:  https://leanprover.github.io  →  export PATH="$HOME/.elan/bin:$PATH"

cd examples/import_duty
python prove.py                         # one-time: certify figures + guardrails → proof_certificate.json

export KHA_BASE_URL=... KHA_API_KEY=... KHA_MODEL=...   # any OpenAI-compatible endpoint
python serve.py                         # http://127.0.0.1:8800/  (chat) and /compare
```

Bring your own model: Kha depends on no provider. `kha.llm` speaks any OpenAI-compatible endpoint
via `KHA_BASE_URL` / `KHA_API_KEY` / `KHA_MODEL`, or pass your own callable.

## Results

Same rules and inputs given to both a general-purpose model and the Kha environment. The oracle
that the environment runs is the one the kernel certified.

### Import duty, official method + real First-Schedule rates

The model is told the method and given the inputs; the environment additionally looks up the real
Basic Customs Duty for the HSN code.

| Import | Real BCD | Kha (proven) | A general model |
|---|---|---|---|
| Motor car · HSN 87032391 · ₹20L · IGST 28% | 125% | **₹40,80,000** | ~₹24,31,200 |

A general model was wrong on **5 / 5** test imports, understating duty by ~**20-50%**, it both
misremembers the published rate and mishandles the cascade (charging IGST on the wrong base). Kha
is exact on every input, kernel-certified once.

### Income tax, same rules given to both

| Model | Exact across repeated crore-scale computations |
|---|---|
| A smaller general model | ~10 / 24 runs |
| A frontier general model | ~23 / 24 runs |
| **Kha environment** | **exact, every run, kernel-certified** |

The general model is fine on easy incomes and fails on the high-value ones, silently, and with a
different wrong number each run. Kha's figure is the same every time and carries its certificate.

Sources: Finance Bill, 2026; Customs Tariff Act First Schedule (CBIC).

## Layout

```
kha/            core: spec (one→Lean/SMT/oracle) · verify · prove · env (loop, ledger) · assistant · llm
examples/
  import_duty/  official cascade + 11,972 real HSN→BCD rates
  income_tax/   Finance Bill slabs, surcharge, marginal relief, cess
theory.md       the intuitions behind the design
```

## The honest boundary

Kha proves the engine **obeys the spec**, exactly. Two things remain human, by nature: that the
**spec faithfully captures the real rules** (reviewed once, when authored), and that the model
**extracts the inputs correctly** (the one soft step, it supplies causes, the environment computes
effects). Everything between is proven and out of the model's hands.

## License

MIT.
