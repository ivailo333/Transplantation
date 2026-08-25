from __future__ import annotations

import json
import mimetypes
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlsplit
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 4173
DEFAULT_BACKEND_URL = "http://127.0.0.1:8000/v1"
PROXY_TIMEOUT_SECONDS = 20


class FrontendHandler(SimpleHTTPRequestHandler):
    server_version = "HLAFrontendPrototype/0.1"

    def translate_path(self, path: str) -> str:
        parsed = urlsplit(path)
        if parsed.path in {"", "/"}:
            return str(ROOT / "index.html")

        parts = [
            unquote(part)
            for part in parsed.path.split("/")
            if part and part not in {".", ".."}
        ]
        target = (ROOT.joinpath(*parts)).resolve()
        try:
            target.relative_to(ROOT)
        except ValueError:
            return str(ROOT / "index.html")
        if target.is_dir():
            target = target / "index.html"
        return str(target)

    def end_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        if self._is_api_path():
            self.send_response(204)
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, X-API-Key, X-Request-ID")
            self.end_headers()
            return
        super().do_OPTIONS()

    def do_GET(self) -> None:
        if self._is_api_path():
            self._proxy()
            return

        path = Path(self.translate_path(self.path))
        if path.exists() and path.is_file():
            super().do_GET()
            return

        self.path = "/"
        super().do_GET()

    def do_POST(self) -> None:
        if self._is_api_path():
            self._proxy()
            return
        self.send_error(405, "Method not allowed")

    def _is_api_path(self) -> bool:
        return urlsplit(self.path).path.startswith("/api/")

    def _proxy(self) -> None:
        body = self._request_body()
        target_url = self._target_url()
        request = Request(
            target_url,
            data=body if self.command != "GET" else None,
            headers=self._forward_headers(),
            method=self.command,
        )

        try:
            with urlopen(request, timeout=PROXY_TIMEOUT_SECONDS) as response:
                payload = response.read()
                self.send_response(response.status)
                self._copy_response_headers(response)
                self.end_headers()
                self.wfile.write(payload)
        except HTTPError as exc:
            payload = exc.read()
            self.send_response(exc.code)
            self._copy_response_headers(exc)
            self.end_headers()
            self.wfile.write(payload)
        except (TimeoutError, URLError, OSError) as exc:
            self._json_error(502, "BackendProxyError", str(exc))

    def _target_url(self) -> str:
        backend_url = self.server.backend_url.rstrip("/")  # type: ignore[attr-defined]
        parsed = urlsplit(self.path)
        upstream_path = parsed.path.removeprefix("/api") or "/"
        suffix = upstream_path
        if parsed.query:
            suffix = f"{suffix}?{parsed.query}"
        return f"{backend_url}{suffix}"

    def _request_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return b""
        return self.rfile.read(length)

    def _forward_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Accept": "application/json"}
        for name in ("Content-Type", "X-API-Key", "X-Request-ID", "Authorization"):
            value = self.headers.get(name)
            if value:
                headers[name] = value
        return headers

    def _copy_response_headers(self, response) -> None:
        for name in ("Content-Type", "X-Request-ID"):
            value = response.headers.get(name)
            if value:
                self.send_header(name, value)

    def _json_error(self, status: int, error: str, message: str) -> None:
        payload = json.dumps(
            {
                "schema": "hla-frontend-proxy-error-v1",
                "clinical": False,
                "error": error,
                "message": message,
            },
            ensure_ascii=False,
        ).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def main() -> None:
    host = os.getenv("HLA_FRONTEND_HOST", DEFAULT_HOST)
    port = int(os.getenv("HLA_FRONTEND_PORT", str(DEFAULT_PORT)))
    backend_url = os.getenv("HLA_FRONTEND_BACKEND_URL", DEFAULT_BACKEND_URL)

    mimetypes.add_type("application/javascript; charset=utf-8", ".js")
    mimetypes.add_type("text/css; charset=utf-8", ".css")
    mimetypes.add_type("text/html; charset=utf-8", ".html")

    server = ThreadingHTTPServer((host, port), FrontendHandler)
    server.backend_url = backend_url
    print(f"HLA frontend prototype: http://{host}:{port}")
    print(f"Proxy backend: {backend_url}")
    server.serve_forever()


if __name__ == "__main__":
    main()
