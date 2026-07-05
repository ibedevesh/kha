"""Web app for the income-tax assistant: a chat and a side-by-side comparison.

    export KHA_BASE_URL=...  KHA_API_KEY=...  KHA_MODEL=...   # your model
    python serve.py           # http://127.0.0.1:8800/  (chat) and /compare

The model supplies inputs; the environment computes and its figure is what the user sees.
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from assistant import engine_chat, plain_chat
from kha import default_llm

HERE = Path(__file__).parent
PORT = 8800
_llm = default_llm()


def _handle(path: str, body: dict) -> dict:
    msgs = body.get("messages", [])
    if path == "/api/chat":
        return engine_chat(msgs, _llm)
    if path == "/api/plain":
        return plain_chat(msgs, _llm)
    return {"error": "not found"}


class H(BaseHTTPRequestHandler):
    def _send(self, code, obj=None, html=None):
        body = html.encode() if html is not None else json.dumps(obj, default=str).encode()
        self.send_response(code)
        self.send_header("content-type", "text/html; charset=utf-8" if html is not None else "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        page = "compare.html" if self.path.startswith("/compare") else "ui.html"
        self._send(200, html=(HERE / page).read_text())

    def do_POST(self):
        n = int(self.headers.get("content-length", 0))
        try:
            self._send(200, self._handle_post(json.loads(self.rfile.read(n) or b"{}")))
        except Exception as e:  # noqa: BLE001
            self._send(400, {"error": str(e)})

    def _handle_post(self, body):
        return _handle(self.path, body)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print(f"income-tax assistant on http://127.0.0.1:{PORT}/  (compare at /compare)")
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
