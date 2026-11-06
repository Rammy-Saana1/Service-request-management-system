"""Dependency-free local HTTP server for the service-request simulation."""

from __future__ import annotations

import argparse
import hmac
import json
import mimetypes
import os
import secrets
import sqlite3
import threading
import time
from http.cookies import CookieError, SimpleCookie
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from database import Database
from service import ConflictError, NotFoundError, RequestService, ValidationError


ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "web"
DEFAULT_DB = ROOT / "data" / "service_requests.db"
MAX_BODY_BYTES = 1_000_000
MANAGER_COOKIE = "local_manager_session"
MANAGER_SESSION_SECONDS = 8 * 60 * 60
MIN_MANAGER_PASSCODE_LENGTH = 12
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


def create_server(
    host: str,
    port: int,
    database_path: str | Path,
    manager_passcode: str,
) -> ThreadingHTTPServer:
    if host not in LOOPBACK_HOSTS:
        raise ValueError("The local simulation may only bind to a loopback host.")
    if not isinstance(manager_passcode, str) or len(manager_passcode) < MIN_MANAGER_PASSCODE_LENGTH:
        raise ValueError(
            f"Manager passcode must contain at least {MIN_MANAGER_PASSCODE_LENGTH} characters."
        )
    service = RequestService(Database(database_path))
    manager_sessions: dict[str, tuple[str, float]] = {}
    sessions_lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        server_version = "ServiceRequestLocal/1.0"

        def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
            parsed = urlparse(self.path)
            if parsed.path == "/api/health":
                self._json(HTTPStatus.OK, {"status": "ok", "mode": "simulated"})
                return
            if parsed.path == "/api/manager/session":
                reviewer = self._require_manager()
                if reviewer is not None:
                    self._json(HTTPStatus.OK, {"authenticated": True, "reviewer": reviewer})
                return
            if parsed.path == "/api/requests":
                if self._require_manager() is None:
                    return
                status = parse_qs(parsed.query).get("status", [None])[0]
                self._execute(lambda: {"items": service.list(status)})
                return
            request_id = _request_id(parsed.path)
            if request_id is not None:
                if self._require_manager() is None:
                    return
                self._execute(lambda: service.get(request_id))
                return
            self._static(parsed.path)

        def do_POST(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
            parsed = urlparse(self.path)
            if parsed.path == "/api/manager/login":
                self._manager_login()
                return
            if parsed.path == "/api/manager/logout":
                self._manager_logout()
                return
            if parsed.path == "/api/requests":
                self._execute(lambda: service.create(self._read_json()), HTTPStatus.CREATED)
                return
            request_id = _decision_id(parsed.path)
            if request_id is not None:
                reviewer = self._require_manager()
                if reviewer is None:
                    return

                def decide() -> dict:
                    payload = self._read_json()
                    payload["reviewed_by"] = reviewer
                    return service.decide(request_id, payload)

                self._execute(decide)
                return
            self._json(HTTPStatus.NOT_FOUND, {"error": "Route not found."})

        def _manager_login(self) -> None:
            try:
                payload = self._read_json()
                reviewer = payload.get("reviewer")
                passcode = payload.get("passcode")
                if not isinstance(reviewer, str) or not reviewer.strip():
                    raise ValidationError("Manager name is required.")
                reviewer = reviewer.strip()
                if len(reviewer) > 120:
                    raise ValidationError("Manager name must be 120 characters or fewer.")
                if not isinstance(passcode, str):
                    raise ValidationError("Manager passcode is required.")
                if not hmac.compare_digest(passcode, manager_passcode):
                    self._json(HTTPStatus.UNAUTHORIZED, {"error": "Invalid manager credentials."})
                    return

                token = secrets.token_urlsafe(32)
                expires_at = time.monotonic() + MANAGER_SESSION_SECONDS
                with sessions_lock:
                    self._remove_expired_sessions()
                    manager_sessions[token] = (reviewer, expires_at)
                self._json(
                    HTTPStatus.OK,
                    {"authenticated": True, "reviewer": reviewer},
                    headers={
                        "Set-Cookie": (
                            f"{MANAGER_COOKIE}={token}; HttpOnly; SameSite=Strict; "
                            f"Path=/; Max-Age={MANAGER_SESSION_SECONDS}"
                        )
                    },
                )
            except (ValidationError, json.JSONDecodeError, UnicodeDecodeError) as error:
                self._respond_error(error)

        def _manager_logout(self) -> None:
            token = self._manager_token()
            if token:
                with sessions_lock:
                    manager_sessions.pop(token, None)
            self._json(
                HTTPStatus.OK,
                {"authenticated": False},
                headers={
                    "Set-Cookie": (
                        f"{MANAGER_COOKIE}=; HttpOnly; SameSite=Strict; "
                        "Path=/; Max-Age=0"
                    )
                },
            )

        def _require_manager(self) -> str | None:
            token = self._manager_token()
            if token:
                with sessions_lock:
                    self._remove_expired_sessions()
                    session = manager_sessions.get(token)
                if session is not None:
                    return session[0]
            self._json(HTTPStatus.UNAUTHORIZED, {"error": "Manager sign-in is required."})
            return None

        def _manager_token(self) -> str | None:
            raw_cookie = self.headers.get("Cookie")
            if not raw_cookie:
                return None
            try:
                cookie = SimpleCookie()
                cookie.load(raw_cookie)
            except CookieError:
                return None
            morsel = cookie.get(MANAGER_COOKIE)
            return morsel.value if morsel else None

        def _remove_expired_sessions(self) -> None:
            now = time.monotonic()
            expired = [
                token for token, (_, expires_at) in manager_sessions.items() if expires_at <= now
            ]
            for token in expired:
                manager_sessions.pop(token, None)

        def _execute(self, action, success: HTTPStatus = HTTPStatus.OK) -> None:
            try:
                self._json(success, action())
            except (ValidationError, NotFoundError, ConflictError, json.JSONDecodeError,
                    UnicodeDecodeError, sqlite3.Error) as error:
                self._respond_error(error)

        def _respond_error(self, error: Exception) -> None:
            if isinstance(error, ValidationError):
                self._json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
            elif isinstance(error, NotFoundError):
                self._json(HTTPStatus.NOT_FOUND, {"error": str(error)})
            elif isinstance(error, ConflictError):
                self._json(HTTPStatus.CONFLICT, {"error": str(error)})
            elif isinstance(error, (json.JSONDecodeError, UnicodeDecodeError)):
                self._json(HTTPStatus.BAD_REQUEST, {"error": "Request body must be valid UTF-8 JSON."})
            else:
                self.log_error("Database error: %s", error)
                self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "Local database operation failed."})

        def _read_json(self) -> dict:
            content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if content_type != "application/json":
                raise ValidationError("Content-Type must be application/json.")
            try:
                size = int(self.headers.get("Content-Length", "0"))
            except ValueError as error:
                raise ValidationError("Invalid Content-Length header.") from error
            if size <= 0:
                raise ValidationError("A JSON request body is required.")
            if size > MAX_BODY_BYTES:
                raise ValidationError("Request body is too large.")
            payload = json.loads(self.rfile.read(size).decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValidationError("JSON request body must be an object.")
            return payload

        def _static(self, request_path: str) -> None:
            relative = "index.html" if request_path in {"/", "/manager"} else request_path.lstrip("/")
            candidate = (WEB_ROOT / relative).resolve()
            try:
                candidate.relative_to(WEB_ROOT.resolve())
            except ValueError:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            if not candidate.is_file():
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            content_type, _ = mimetypes.guess_type(candidate.name)
            try:
                data = candidate.read_bytes()
            except OSError:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)
                return
            content_type = content_type or "application/octet-stream"
            if content_type.startswith("text/") or content_type in {
                "application/javascript",
                "application/json",
            }:
                content_type += "; charset=utf-8"
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def _json(
            self,
            status: HTTPStatus,
            payload: object,
            *,
            headers: dict[str, str] | None = None,
        ) -> None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            for name, value in (headers or {}).items():
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(data)

        def end_headers(self) -> None:
            self.send_header("Content-Security-Policy", (
                "default-src 'self'; base-uri 'none'; form-action 'self'; "
                "frame-ancestors 'none'; object-src 'none'"
            ))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
            super().end_headers()

        def log_message(self, message: str, *args) -> None:
            print(f"{self.address_string()} - {message % args}")

    return ThreadingHTTPServer((host, port), Handler)


def _request_id(path: str) -> int | None:
    parts = path.strip("/").split("/")
    if len(parts) == 3 and parts[:2] == ["api", "requests"] and parts[2].isdigit():
        return int(parts[2])
    return None


def _decision_id(path: str) -> int | None:
    parts = path.strip("/").split("/")
    if (
        len(parts) == 4
        and parts[:2] == ["api", "requests"]
        and parts[2].isdigit()
        and parts[3] == "decision"
    ):
        return int(parts[2])
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local service-request simulation.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--db", default=str(DEFAULT_DB))
    arguments = parser.parse_args()
    manager_passcode = os.environ.get("LOCAL_SIM_MANAGER_PASSCODE", "")
    if len(manager_passcode) < MIN_MANAGER_PASSCODE_LENGTH:
        parser.error(
            "Set LOCAL_SIM_MANAGER_PASSCODE to at least 12 characters, "
            "or start the app with run-local.ps1."
        )
    try:
        server = create_server(
            arguments.host,
            arguments.port,
            arguments.db,
            manager_passcode,
        )
    except ValueError as error:
        parser.error(str(error))
    print(f"Local simulation running at http://{arguments.host}:{server.server_port}")
    print(f"SQLite database: {Path(arguments.db).resolve()}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping local simulation.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
