"""The environment loop: the world runs it and calls the agent, not the other way around.

    while alive:
        obs   = world.render(state)      # the world shows the agent only what it permits
        text  = agent(obs)               # the world calls the agent
        move  = world.parse(text)        # the world decides what the text means
        state = world.step(state, move)  # the world computes the result; the agent never does
        ledger.append(...)               # a hash-chained, replayable record

The agent supplies causes; the world computes effects. A rejected cause leaves state unchanged.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class Move:
    kind: str
    args: dict[str, Any] = field(default_factory=dict)
    raw: str = ""

    def __str__(self) -> str:
        return f"{self.kind}(" + ", ".join(f"{k}={v!r}" for k, v in self.args.items()) + ")"


@dataclass(frozen=True)
class Entry:
    tick: int
    state_before: dict
    move: dict
    admitted: bool
    reason: str
    state_after: dict
    prev_hash: str
    this_hash: str


def _h(obj: Any) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


class Ledger:
    """A hash-chained transcript. Only the world writes it and only legal moves change state
    so the ledger is the proof of what happened, replayable and tamper-evident."""

    GENESIS = "0" * 64

    def __init__(self) -> None:
        self.entries: list[Entry] = []

    def append(self, tick, state_before, move: Move, admitted, reason, state_after) -> Entry:
        prev = self.entries[-1].this_hash if self.entries else self.GENESIS
        body = {"tick": tick, "state_before": state_before,
                "move": {"kind": move.kind, "args": move.args},
                "admitted": admitted, "reason": reason,
                "state_after": state_after, "prev_hash": prev},
        e = Entry(**body, this_hash=_h(body))
        self.entries.append(e)
        return e

    def intact(self) -> bool:
        prev = self.GENESIS
        for e in self.entries:
            body = {"tick": e.tick, "state_before": e.state_before, "move": e.move,
                    "admitted": e.admitted, "reason": e.reason,
                    "state_after": e.state_after, "prev_hash": prev}
            if e.prev_hash != prev or _h(body) != e.this_hash:
                return False
            prev = e.this_hash
        return True


class Agent(Protocol):
    def __call__(self, observation: str) -> str: ...


class World:
    name = "world"

    def initial_state(self) -> dict:
        raise NotImplementedError

    def render(self, state: dict) -> str:
        raise NotImplementedError

    def parse(self, text: str) -> Move:
        raise NotImplementedError

    def step(self, state: dict, move: Move) -> tuple[dict, bool, str]:
        raise NotImplementedError

    def done(self, state: dict) -> bool:
        return bool(state.get("_closed"))


def land(agent: Agent, world: World, *, max_ticks: int = 24, verbose: bool = True) -> Ledger:
    """Land an agent inside a world. The world owns the loop; the agent is a callee."""
    state = world.initial_state()
    ledger = Ledger()
    for tick in range(max_ticks):
        if world.done(state):
            break
        obs = world.render(state)
        move = world.parse(agent(obs))
        before = dict(state)
        state, admitted, reason = world.step(state, move)
        ledger.append(tick, before, move, admitted, reason, dict(state))
        if verbose:
            print(f"  [{tick:02d}] {'OK  ' if admitted else 'NOOP'} {move}  ::  {reason}")
    return ledger


def replay(world: World, ledger: Ledger) -> bool:
    """Re-run the recorded moves from the initial state; every state must reproduce exactly."""
    state = world.initial_state()
    for e in ledger.entries:
        state, _, _ = world.step(state, Move(e.move["kind"], e.move.get("args", {})))
        if state != e.state_after:
            return False
    return True
