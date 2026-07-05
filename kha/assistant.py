"""Drop a model inside an environment and expose it as a chat assistant.

Implement a `ChatWorld`: declare how the assistant talks and what causes it collects, and how the
environment computes the answer (the trusted part). The framework runs the loop, keeps per-session
state, parses the model's JSON, and lets ONLY the environment's computed result reach the user.
"""
from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .llm import LLM, default_llm


class ChatWorld(ABC):
    name = "assistant"
    greeting = "Hi! How can I help?"

    @abstractmethod
    def initial_state(self) -> dict: ...

    @abstractmethod
    def system(self) -> str:
        """Persona + JSON turn protocol. Must tell the model it never computes the answer."""

    @abstractmethod
    def env_view(self, state: dict) -> str:
        """One-line summary of the record, shown to the model each turn (re-grounding)."""

    @abstractmethod
    def apply(self, state: dict, move: dict) -> tuple[dict, list[str], dict | None]:
        """Take the model's causes, compute effects. Return (new_state, log, result_or_None).
        This is the only place answers are produced, never by the model."""


@dataclass
class Session:
    state: dict
    history: list[dict] = field(default_factory=list)


class Assistant:
    def __init__(self, world: ChatWorld, llm: LLM | None = None):
        self.world = world
        self.llm = llm or default_llm()
        self.sessions: dict[str, Session] = {}

    def _session(self, sid: str) -> Session:
        return self.sessions.setdefault(sid, Session(state=self.world.initial_state()))

    def _move(self, s: Session, user_msg: str) -> dict:
        grounded = f"{user_msg}\n\n[env record] {self.world.env_view(s.state)}"
        s.history.append({"role": "user", "content": grounded})
        text = self.llm(self.world.system(), s.history)
        s.history.append({"role": "assistant", "content": text})
        m = re.search(r"\{.*\}", text, re.DOTALL)
        try:
            return json.loads(m.group(0)) if m else {"reply": text}
        except Exception:
            return {"reply": text}

    def chat(self, sid: str, user_msg: str) -> dict:
        s = self._session(sid)
        move = self._move(s, user_msg)
        s.state, log, result = self.world.apply(s.state, move)
        return {"reply": move.get("reply", "").strip(), "env_log": log, "result": result}


def console(world: ChatWorld, llm: LLM | None = None, script: list[str] | None = None) -> None:
    a = Assistant(world, llm)
    print(f"\n{world.name}, the model chats; the environment computes the answer.")
    print(f"assistant: {world.greeting}\n")
    msgs = script if script is not None else iter(lambda: input("you: ").strip(), "")
    for u in msgs:
        if script is not None:
            print(f"you: {u}")
        if u.lower() in {"quit", "exit", "q"}:
            break
        out = a.chat("console", u)
        print(f"assistant: {out['reply']}")
        for line in out["env_log"]:
            print(f"           [env] {line}")
        print()


def serve(world: ChatWorld, llm: LLM | None = None, port: int = 8800, ui: str | None = None) -> None:
    """Minimal HTTP API (POST /chat) plus an optional static UI at /."""
    assistant = Assistant(world, llm)
    ui_path = Path(ui) if ui else None

    class H(BaseHTTPRequestHandler):
        def _send(self, code, obj=None, html=None):
            body = html.encode() if html is not None else json.dumps(obj, default=str).encode()
            ctype = "text/html; charset=utf-8" if html is not None else "application/json"
            self.send_response(code)
            self.send_header("content-type", ctype)
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path in ("/", "/index.html") and ui_path and ui_path.exists():
                return self._send(200, html=ui_path.read_text())
            self._send(200, {"ok": True, "assistant": world.name})

        def do_POST(self):
            if self.path != "/chat":
                return self._send(404, {"error": "POST /chat"})
            n = int(self.headers.get("content-length", 0))
            try:
                body = json.loads(self.rfile.read(n) or b"{}")
                self._send(200, assistant.chat(body.get("session", "default"), body.get("message", "")))
            except Exception as e:  # noqa: BLE001
                self._send(400, {"error": str(e)})

        def log_message(self, *a):
            pass

    print(f"{world.name} on http://127.0.0.1:{port}" + (f"  (UI at /)" if ui_path else ""))
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
