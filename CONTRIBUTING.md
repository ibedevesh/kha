# Contributing to Kha

Kha is an open-source framework for building 100% reliable AI agents. It grows one environment at a
time, and that is where you can help most.

## Build an environment for a critical, rule-based domain

The best contribution is a new proven environment. Pick a domain that runs on rules, ideally a
high-stakes one where a single wrong answer is costly or dangerous: tax, customs, benefits
eligibility, drug dosing, safety limits, financial compliance, legal thresholds. Encode its
published rules once, prove them, and any AI agent can then act in that domain safely.

## How

Fork, then copy an example in `examples/` and swap four things: `spec.py` (the rules), `prove.py`
(the figures and guardrails to prove), `engine.py` (the runtime), and the chat surface. Open a pull
request; a maintainer reviews and merges. Direct pushes to `main` are not open, so nothing lands
without review.

Two rules for any environment:

- Rules must come from an authoritative public source, never invented (cite it in the spec).
- The proof must pass (`python prove.py` prints `ALL PROVEN`).
