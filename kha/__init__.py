"""Kha (ख), a proven space for AI to act in.

The model moves freely, but every result is computed by an environment whose rules were proven
once with a kernel and an SMT solver, not by the model. Write rules once as a spec, prove the
spec, load it, and drop a model in where it only supplies inputs.
"""
from .spec import Spec, build_oracle, emit_lean, emit_smt
from .verify import verify
from .prove import prove, load_certificate, is_certified
from .env import Move, Ledger, World, land, replay
from .assistant import ChatWorld, Assistant, serve, console
from .llm import LLM, OpenAICompatLLM, default_llm

__all__ = [
    "Spec", "build_oracle", "emit_lean", "emit_smt",
    "verify", "prove", "load_certificate", "is_certified",
    "Move", "Ledger", "World", "land", "replay",
    "ChatWorld", "Assistant", "serve", "console",
    "LLM", "OpenAICompatLLM", "default_llm",
]
