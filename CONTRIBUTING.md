# Contributing to Kha

Thanks for your interest. Kha is an open-source framework for building 100% reliable AI agents: the
agent acts inside a proven environment that computes and certifies every result. Contributions are
very welcome, especially new environments.

## How to contribute

The repo is public, so anyone can help:

1. **Fork** the repo and create a branch (`git checkout -b my-change`).
2. Make your change and keep the proofs green (see below).
3. **Open a pull request.** A maintainer reviews and merges. Direct pushes to `main` are not open;
   all changes come through PRs, so nothing lands without review.

Please open an issue first for anything large, so we can agree on the approach.

## The most useful contribution: a new environment

Adding a domain is the highest-value contribution. Copy an example in `examples/` and swap:

- `spec.py` — the rules, written once as data (facts + expressions).
- `prove.py` — the figures to certify and the guardrails to prove.
- `engine.py` — the runtime that executes the proven oracle.
- `assistant.py` / `serve.py` / `ui.html` — the chat surface.

Two hard rules for any environment:

- **Rules must come from an authoritative public source. Never invent them.** Cite the source in
  the spec (as the tax and customs examples do).
- **The proof must pass.** `python prove.py` has to print `ALL PROVEN` and write a certificate. A PR
  whose proof does not pass will not be merged.

## Dev setup

```bash
pip install -e .          # installs kha (dep: z3-solver)
# Lean 4 via elan is needed only for the proving step: https://leanprover.github.io
```

## Ground rules

- Keep the framework **vendor-neutral** (no model-vendor names in code or docs; the benchmark is the
  only place a specific model is named, because that is evidence).
- Keep the honest boundary honest: the environment proves it obeys *its spec*; whether the spec
  matches the real-world rules is the author's responsibility, and the model's input extraction is
  the one soft step. Do not claim more than that.
- Plain prose, no em dashes.

By contributing you agree your work is licensed under the repository's MIT License.
