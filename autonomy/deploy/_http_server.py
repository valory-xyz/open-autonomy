# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2026 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""Minimal Flask-compatible HTTP server.

Covers the subset of Flask/Werkzeug used by
``autonomy.deploy.generators.localhost.tendermint.app`` and
``autonomy.replay.tendermint``: ``App``, ``Request``, ``Response``,
``jsonify``, route decorators, error handlers, an in-process
``test_client()`` for unit tests, and a threaded HTTP/1.1 server
for production use. Deliberately API-compatible so callers don't
need to change and the switch can be reverted.
"""

import json as _json
import logging
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    Pattern,
    Type,
    Union,
)
from urllib.parse import parse_qsl, urlsplit


# ---------------------------------------------------------------------------
# Errors (stand-ins for werkzeug.exceptions)
# ---------------------------------------------------------------------------


class HTTPException(Exception):
    """Base class for HTTP errors."""

    code = 500
    description = "Internal Server Error"


class NotFound(HTTPException):
    """404 Not Found."""

    code = 404
    description = "Not Found"


class InternalServerError(HTTPException):
    """500 Internal Server Error."""

    code = 500
    description = "Internal Server Error"


# ---------------------------------------------------------------------------
# Request / Response
# ---------------------------------------------------------------------------


class _Args(dict):
    """Query-string args with Flask's ``get(key, default=None, type=None)``."""

    def get(  # type: ignore[override]
        self,
        key: str,
        default: Any = None,
        type: Optional[Callable[[str], Any]] = None,  # noqa: A002
    ) -> Any:
        value = super().get(key, default)
        if type is not None and value is not None and value is not default:
            try:
                return type(value)
            except (ValueError, TypeError):
                return default
        return value


class Request:
    """Flask-compatible request object."""

    def __init__(
        self,
        method: str,
        path: str,
        args: Mapping[str, str],
        data: bytes,
        headers: Mapping[str, str],
    ) -> None:
        """Initialize a request."""
        self.method = method
        self.path = path
        self.args = _Args(args)
        self._data = data
        self.headers: Dict[str, str] = dict(headers)

    def get_data(self) -> bytes:
        """Return the raw request body bytes."""
        return self._data

    def get_json(self, silent: bool = False) -> Any:
        """Parse the body as JSON."""
        try:
            return _json.loads(self._data.decode("utf-8"))
        except Exception:
            if silent:
                return None
            raise


class Response:
    """Minimal Flask-compatible Response."""

    default_mimetype = "text/html; charset=utf-8"

    def __init__(
        self,
        response: Union[str, bytes, None] = None,
        status: int = 200,
        mimetype: Optional[str] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> None:
        """Initialize a response."""
        if response is None:
            response = b""
        if isinstance(response, str):
            response = response.encode("utf-8")
        self.data: bytes = response
        self.status_code: int = status
        self.mimetype: str = mimetype or self.default_mimetype
        self.headers: Dict[str, str] = dict(headers or {})

    def get_json(self, silent: bool = False) -> Any:
        """Parse the body as JSON."""
        try:
            return _json.loads(self.data.decode("utf-8"))
        except Exception:
            if silent:
                return None
            raise


def jsonify(*args: Any, **kwargs: Any) -> Response:
    """Serialize a value to a JSON Response, mirroring ``flask.jsonify``.

    * ``jsonify({"a": 1})`` — one positional arg is used as the body.
    * ``jsonify(a=1, b=2)`` — keyword args form an object.
    * ``jsonify(1, 2, 3)`` — multiple positional args form a list.
    """
    if args and kwargs:
        raise TypeError(
            "jsonify() accepts either positional args or kwargs, not both"
        )
    if len(args) == 1:
        payload = args[0]
    elif args:
        payload = list(args)
    else:
        payload = kwargs
    return Response(
        _json.dumps(payload).encode("utf-8"),
        mimetype="application/json",
    )


# ---------------------------------------------------------------------------
# Route dispatch
# ---------------------------------------------------------------------------


_Handler = Callable[..., Any]


class _Route:
    """A single route: method(s), URL pattern, handler."""

    def __init__(
        self, methods: List[str], pattern: str, handler: _Handler
    ) -> None:
        """Initialize a route and compile its URL pattern."""
        self.methods = [m.upper() for m in methods]
        # Translate Flask-style <int:x> and <x> placeholders to regex groups
        # in a single pass so we don't re-match the <name> we just produced.
        self._int_params = set(re.findall(r"<int:(\w+)>", pattern))

        def _replace(match: "re.Match[str]") -> str:
            if match.group(1) is not None:  # <int:name>
                return f"(?P<{match.group(1)}>\\d+)"
            return f"(?P<{match.group(2)}>[^/]+)"  # <name>

        regex = re.sub(r"<int:(\w+)>|<(\w+)>", _replace, pattern)
        self.regex: Pattern[str] = re.compile(f"^{regex}$")
        self.handler = handler

    def match(self, path: str) -> Optional[Dict[str, Any]]:
        """Return captured path params if *path* matches, else ``None``."""
        m = self.regex.match(path)
        if m is None:
            return None
        return {
            k: (int(v) if k in self._int_params else v)
            for k, v in m.groupdict().items()
        }


# ---------------------------------------------------------------------------
# Threading request context
# ---------------------------------------------------------------------------


_request_context = threading.local()


class _RequestProxy:
    """Thread-local proxy that forwards to the current :class:`Request`."""

    def __getattr__(self, name: str) -> Any:
        req = getattr(_request_context, "request", None)
        if req is None:
            raise RuntimeError("No active request context")
        return getattr(req, name)


# Module-level alias mirroring ``from flask import request``.
request = _RequestProxy()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------


class _AppContext:
    """Stand-in for ``flask.ctx.AppContext`` — a no-op context manager."""

    def push(self) -> None:
        """No-op."""

    def pop(self) -> None:
        """No-op."""

    def __enter__(self) -> "_AppContext":
        """Return self."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """No-op."""


class App:
    """Minimal Flask-compatible application."""

    def __init__(self, name: str) -> None:
        """Initialize the app with an identifying *name*."""
        self.name = name
        self._routes: List[_Route] = []
        self._error_handlers: Dict[int, _Handler] = {}
        self.logger: logging.Logger = logging.getLogger(name)
        self.config: Dict[str, Any] = {}

    def route(
        self, rule: str, methods: Optional[List[str]] = None
    ) -> Callable[[_Handler], _Handler]:
        """Register a handler for *rule* (GET by default)."""

        def decorator(fn: _Handler) -> _Handler:
            self._routes.append(_Route(methods or ["GET"], rule, fn))
            return fn

        return decorator

    def get(self, rule: str) -> Callable[[_Handler], _Handler]:
        """Register a GET handler."""
        return self.route(rule, methods=["GET"])

    def post(self, rule: str) -> Callable[[_Handler], _Handler]:
        """Register a POST handler."""
        return self.route(rule, methods=["POST"])

    def errorhandler(
        self, code: int
    ) -> Callable[[_Handler], _Handler]:
        """Register a handler for HTTP *code* (e.g. 404, 500)."""

        def decorator(fn: _Handler) -> _Handler:
            self._error_handlers[code] = fn
            return fn

        return decorator

    def app_context(self) -> _AppContext:
        """Return a no-op application context."""
        return _AppContext()

    def test_client(self) -> "_TestClient":
        """Return an in-process test client."""
        return _TestClient(self)

    def dispatch(self, req: Request) -> Response:
        """Dispatch *req* to the matching handler (or an error handler)."""
        for route in self._routes:
            if req.method not in route.methods:
                continue
            params = route.match(req.path)
            if params is None:
                continue
            try:
                result = route.handler(**params)
            except Exception as exc:  # pylint: disable=broad-except
                self.logger.exception("unhandled exception in handler")
                handler = self._error_handlers.get(500)
                if handler is not None:
                    try:
                        return _to_response(handler(InternalServerError(str(exc))))
                    except Exception:  # pragma: no cover  # pylint: disable=broad-except
                        pass
                return Response(str(exc), status=500)
            return _to_response(result)

        handler = self._error_handlers.get(404)
        if handler is not None:
            return _to_response(handler(NotFound()))
        return Response("Not Found", status=404)


def _to_response(result: Any) -> Response:
    """Coerce a handler's return value to a :class:`Response`."""
    status = 200
    if isinstance(result, tuple):
        if len(result) != 2:
            raise TypeError(f"Unsupported handler tuple shape: {result!r}")
        result, status = result
    if isinstance(result, Response):
        if status != 200:
            result.status_code = status
        return result
    if isinstance(result, (dict, list)):
        resp = jsonify(result)
        resp.status_code = status
        return resp
    if isinstance(result, (str, bytes)):
        return Response(result, status=status)
    raise TypeError(
        f"Unsupported handler return type: {type(result).__name__}"
    )


# ---------------------------------------------------------------------------
# Test client
# ---------------------------------------------------------------------------


class _TestClient:
    """In-process test client mirroring ``flask.testing.FlaskClient``."""

    def __init__(self, app: App) -> None:
        """Initialize the test client."""
        self._app = app

    def __enter__(self) -> "_TestClient":
        """Return self (context-manager compatibility)."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """No-op cleanup."""

    def _do(
        self,
        method: str,
        path: str,
        json: Any = None,  # noqa: A002
        data: Optional[bytes] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> "_TestResponse":
        """Build a :class:`Request` and dispatch it through the app."""
        parts = urlsplit(path)
        body = b""
        req_headers: Dict[str, str] = dict(headers or {})
        if json is not None:
            body = _json.dumps(json).encode("utf-8")
            req_headers.setdefault("Content-Type", "application/json")
        elif data is not None:
            body = data
        req = Request(
            method=method.upper(),
            path=parts.path,
            args=dict(parse_qsl(parts.query, keep_blank_values=True)),
            data=body,
            headers=req_headers,
        )
        _request_context.request = req
        try:
            resp = self._app.dispatch(req)
        finally:
            _request_context.request = None
        return _TestResponse(resp)

    def get(self, path: str, **kwargs: Any) -> "_TestResponse":
        """Send a GET request."""
        return self._do("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> "_TestResponse":
        """Send a POST request."""
        return self._do("POST", path, **kwargs)


class _TestResponse:
    """Test response mirroring ``flask.wrappers.Response``."""

    def __init__(self, response: Response) -> None:
        """Wrap *response* for test-client consumers."""
        self._response = response
        self.status_code: int = response.status_code
        self.data: bytes = response.data
        self.mimetype: str = response.mimetype

    def get_json(self, silent: bool = False) -> Any:
        """Parse the body as JSON."""
        try:
            return _json.loads(self.data.decode("utf-8"))
        except Exception:
            if silent:
                return None
            raise


# ---------------------------------------------------------------------------
# Live server
# ---------------------------------------------------------------------------


def _build_handler_class(app: App) -> Type[BaseHTTPRequestHandler]:
    """Build a BaseHTTPRequestHandler subclass bound to *app*."""

    class _AppHandler(BaseHTTPRequestHandler):
        """HTTP/1.1 handler that dispatches through the app."""

        protocol_version = "HTTP/1.1"
        server_version = "open-autonomy"

        def _serve(self, method: str) -> None:
            parts = urlsplit(self.path)
            content_length = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(content_length) if content_length else b""
            req = Request(
                method=method,
                path=parts.path,
                args=dict(parse_qsl(parts.query, keep_blank_values=True)),
                data=body,
                headers={k: v for k, v in self.headers.items()},
            )
            _request_context.request = req
            try:
                resp = app.dispatch(req)
            finally:
                _request_context.request = None
            self.send_response(resp.status_code)
            self.send_header("Content-Type", resp.mimetype)
            self.send_header("Content-Length", str(len(resp.data)))
            for k, v in resp.headers.items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(resp.data)

        def do_GET(self) -> None:  # noqa: N802
            """Handle GET."""
            self._serve("GET")

        def do_POST(self) -> None:  # noqa: N802
            """Handle POST."""
            self._serve("POST")

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            """Forward stdlib access log lines to the app logger."""
            app.logger.info(format % args)

    return _AppHandler


def run_app(app: App, host: str, port: int) -> None:
    """Serve *app* on *host:port* using a threaded HTTP/1.1 server (blocks)."""
    server = ThreadingHTTPServer((host, port), _build_handler_class(app))
    try:
        server.serve_forever()
    finally:
        server.server_close()
