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

"""Unit tests for the inlined Flask-compatible HTTP server shim."""

import json
import socket
import threading
import time
import urllib.request
from http.server import ThreadingHTTPServer
from typing import Any

import pytest

from autonomy.deploy._http_server import (
    App,
    HTTPException,
    InternalServerError,
    NotFound,
    Request,
    Response,
    _AppContext,
    _Args,
    _Route,
    _build_handler_class,
    _to_response,
    jsonify,
    request,
)

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


def test_http_exception_has_code_and_description() -> None:
    """Test that HTTPException subclasses expose `code` and default message."""
    assert NotFound().code == 404
    assert InternalServerError().code == 500
    assert isinstance(NotFound(), HTTPException)


# ---------------------------------------------------------------------------
# _Args
# ---------------------------------------------------------------------------


def test_args_get_returns_default_when_missing() -> None:
    """`_Args.get` falls back to the default when the key is absent."""
    assert _Args({}).get("missing", "fallback") == "fallback"


def test_args_get_coerces_value_with_type() -> None:
    """`_Args.get` coerces the raw string with the provided callable."""
    assert _Args({"n": "42"}).get("n", type=int) == 42


def test_args_get_returns_default_on_value_error() -> None:
    """A `ValueError` during coercion falls back to the default."""
    assert _Args({"n": "abc"}).get("n", default=0, type=int) == 0


def test_args_get_returns_default_on_type_error() -> None:
    """A `TypeError` during coercion falls back to the default."""

    def _coerce(_: str) -> int:
        raise TypeError("nope")

    assert _Args({"n": "1"}).get("n", default=-1, type=_coerce) == -1


def test_args_get_no_coerce_when_value_is_default_sentinel() -> None:
    """No coercion is applied when the resolved value is the default sentinel."""
    sentinel = object()
    # missing key -> value IS default -> type() must not be called
    assert _Args({}).get("missing", default=sentinel, type=int) is sentinel


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------


def test_request_stores_normalised_fields() -> None:
    """`Request.__init__` normalises args and headers into plain dicts."""
    req = Request(
        method="GET",
        path="/x",
        args={"a": "1"},
        data=b"body",
        headers={"H": "v"},
    )
    assert req.method == "GET"
    assert req.path == "/x"
    assert req.args.get("a") == "1"
    assert req.get_data() == b"body"
    assert req.headers == {"H": "v"}


def test_request_get_json_parses_body() -> None:
    """`Request.get_json` parses a JSON body."""
    req = Request("POST", "/", {}, b'{"k": 1}', {})
    assert req.get_json() == {"k": 1}


def test_request_get_json_silent_returns_none_on_bad_body() -> None:
    """`silent=True` swallows JSON decode errors and returns None."""
    req = Request("POST", "/", {}, b"not json", {})
    assert req.get_json(silent=True) is None


def test_request_get_json_raises_on_bad_body() -> None:
    """`silent=False` (default) re-raises the JSON decode error."""
    req = Request("POST", "/", {}, b"not json", {})
    with pytest.raises(json.JSONDecodeError):
        req.get_json()


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------


def test_response_defaults_to_empty_bytes() -> None:
    """`Response()` with no body becomes an empty byte string."""
    assert Response().data == b""


def test_response_encodes_str_body_as_utf8() -> None:
    """Passing a `str` body encodes to UTF-8."""
    assert Response("hi").data == b"hi"


def test_response_accepts_bytes_body_as_is() -> None:
    """A `bytes` body is stored verbatim."""
    assert Response(b"raw").data == b"raw"


def test_response_uses_custom_mimetype_and_headers() -> None:
    """Custom mimetype/headers override defaults."""
    resp = Response("x", mimetype="text/plain", headers={"X-Foo": "1"})
    assert resp.mimetype == "text/plain"
    assert resp.headers == {"X-Foo": "1"}


def test_response_get_json_parses() -> None:
    """`Response.get_json` parses a JSON body."""
    assert Response(b'{"a":1}').get_json() == {"a": 1}


def test_response_get_json_silent_returns_none_on_non_json() -> None:
    """`silent=True` swallows JSON decode errors."""
    assert Response(b"nope").get_json(silent=True) is None


def test_response_get_json_raises_on_non_json() -> None:
    """`silent=False` (default) re-raises the JSON decode error."""
    with pytest.raises(json.JSONDecodeError):
        Response(b"nope").get_json()


# ---------------------------------------------------------------------------
# jsonify
# ---------------------------------------------------------------------------


def test_jsonify_single_positional_is_body() -> None:
    """A single positional arg is serialised as the body."""
    resp = jsonify({"a": 1})
    assert resp.get_json() == {"a": 1}
    assert resp.mimetype == "application/json"


def test_jsonify_multiple_positional_becomes_list() -> None:
    """Multiple positional args form a JSON array."""
    assert jsonify(1, 2, 3).get_json() == [1, 2, 3]


def test_jsonify_kwargs_become_object() -> None:
    """Keyword args form a JSON object."""
    assert jsonify(a=1, b=2).get_json() == {"a": 1, "b": 2}


def test_jsonify_rejects_mixed_positional_and_kwargs() -> None:
    """Mixing positional and kwargs raises TypeError (mirrors Flask)."""
    with pytest.raises(TypeError):
        jsonify({"a": 1}, b=2)


def test_jsonify_empty_returns_empty_object() -> None:
    """`jsonify()` with no args returns an empty object."""
    assert jsonify().get_json() == {}


# ---------------------------------------------------------------------------
# _Route
# ---------------------------------------------------------------------------


def test_route_matches_plain_path() -> None:
    """A constant path matches without captures."""
    route = _Route(["GET"], "/hello", lambda: None)
    assert route.match("/hello") == {}


def test_route_captures_string_param() -> None:
    """`<name>` placeholders are captured as strings."""
    route = _Route(["GET"], "/u/<name>", lambda name: None)
    assert route.match("/u/alice") == {"name": "alice"}


def test_route_captures_and_coerces_int_param() -> None:
    """`<int:name>` placeholders are captured and coerced to int."""
    route = _Route(["GET"], "/item/<int:id>", lambda id: None)
    assert route.match("/item/42") == {"id": 42}


def test_route_returns_none_on_mismatch() -> None:
    """A non-matching path returns `None`."""
    route = _Route(["GET"], "/a", lambda: None)
    assert route.match("/b") is None


def test_route_methods_are_uppercased() -> None:
    """Method names are normalised to uppercase."""
    route = _Route(["get", "Post"], "/", lambda: None)
    assert route.methods == ["GET", "POST"]


# ---------------------------------------------------------------------------
# _RequestProxy (module-level `request`)
# ---------------------------------------------------------------------------


def test_request_proxy_raises_outside_context() -> None:
    """Accessing `request.*` outside a dispatched handler raises."""
    with pytest.raises(RuntimeError, match="No active request context"):
        _ = request.method


def test_request_proxy_short_circuits_dunder_access() -> None:
    """Dunder attribute access falls through to AttributeError.

    Needed so introspection tools (repr, pydoc) do not hit the
    runtime-error branch when inspecting the proxy outside a request.
    """
    with pytest.raises(AttributeError):
        request.__some_nonexistent_dunder__  # noqa: B018


def test_request_proxy_forwards_inside_context() -> None:
    """Inside a dispatched handler, `request.*` forwards to the current Request."""
    app = App(__name__)
    captured = {}

    @app.route("/", methods=["GET"])
    def _handler() -> Any:
        captured["method"] = request.method
        captured["path"] = request.path
        return "ok"

    # The test client sets the thread-local request context; calling
    # app.dispatch() directly does not, so use the client to exercise
    # the proxy-forwarding path.
    with app.test_client() as client:
        client.get("/")
    assert captured == {"method": "GET", "path": "/"}


# ---------------------------------------------------------------------------
# _AppContext
# ---------------------------------------------------------------------------


def test_app_context_is_a_no_op_context_manager() -> None:
    """`_AppContext` supports the context-manager protocol."""
    ctx = _AppContext()
    with ctx as entered:
        assert entered is ctx
    # push/pop are no-ops but should be callable
    ctx.push()
    ctx.pop()


# ---------------------------------------------------------------------------
# App — route registration + dispatch
# ---------------------------------------------------------------------------


def test_app_route_decorator_registers_handler() -> None:
    """`app.route` registers a handler reachable via `dispatch`."""
    app = App(__name__)

    @app.route("/hi", methods=["GET"])
    def _handler() -> str:
        return "hi"

    resp = app.dispatch(Request("GET", "/hi", {}, b"", {}))
    assert resp.data == b"hi"


def test_app_get_and_post_decorators_scope_method() -> None:
    """`app.get` / `app.post` register method-specific routes."""
    app = App(__name__)

    @app.get("/r")
    def _g() -> str:
        return "G"

    @app.post("/r")
    def _p() -> str:
        return "P"

    assert app.dispatch(Request("GET", "/r", {}, b"", {})).data == b"G"
    assert app.dispatch(Request("POST", "/r", {}, b"", {})).data == b"P"


def test_app_dispatch_default_404_response() -> None:
    """No matching route and no error handler → generic 404."""
    app = App(__name__)
    resp = app.dispatch(Request("GET", "/nope", {}, b"", {}))
    assert resp.status_code == 404
    assert resp.data == b"Not Found"


def test_app_dispatch_custom_404_error_handler() -> None:
    """A registered 404 handler receives a `NotFound` instance."""
    app = App(__name__)

    @app.errorhandler(404)
    def _not_found(exc: NotFound) -> Any:
        assert isinstance(exc, NotFound)
        return "custom-404", 404

    resp = app.dispatch(Request("GET", "/absent", {}, b"", {}))
    assert resp.status_code == 404
    assert resp.data == b"custom-404"


def test_app_dispatch_500_generic_when_no_handler() -> None:
    """Handler exception with no 500 handler → generic 500 with str(exc)."""
    app = App(__name__)

    @app.route("/boom", methods=["GET"])
    def _h() -> str:
        raise RuntimeError("kaboom")

    resp = app.dispatch(Request("GET", "/boom", {}, b"", {}))
    assert resp.status_code == 500
    assert b"kaboom" in resp.data


def test_app_dispatch_500_custom_handler_response() -> None:
    """A registered 500 handler receives an `InternalServerError` and its response is used."""
    app = App(__name__)

    @app.errorhandler(500)
    def _five_hundred(exc: InternalServerError) -> Any:
        return {"err": str(exc)}, 500

    @app.route("/boom", methods=["GET"])
    def _h() -> str:
        raise RuntimeError("kaboom")

    resp = app.dispatch(Request("GET", "/boom", {}, b"", {}))
    assert resp.status_code == 500
    assert resp.get_json() == {"err": "kaboom"}


def test_app_app_context_returns_appcontext() -> None:
    """`App.app_context()` returns a usable context manager."""
    app = App(__name__)
    with app.app_context() as ctx:
        assert isinstance(ctx, _AppContext)


def test_app_test_client_roundtrip() -> None:
    """`App.test_client()` can drive GET/POST through dispatch."""
    app = App(__name__)

    @app.get("/hello")
    def _g() -> str:
        return "hi"

    @app.post("/echo")
    def _p() -> Any:
        return {"body": request.get_json()}

    with app.test_client() as client:
        assert client.get("/hello").get_json(silent=True) is None
        r = client.post("/echo", json={"x": 1})
        assert r.get_json() == {"body": {"x": 1}}


def test_test_client_posts_raw_data_and_custom_headers() -> None:
    """POST with raw bytes and custom headers reaches the handler."""
    app = App(__name__)
    seen = {}

    @app.post("/x")
    def _h() -> str:
        seen["data"] = request.get_data()
        seen["h"] = request.headers.get("X-Test")
        return "ok"

    with app.test_client() as client:
        client.post("/x", data=b"raw", headers={"X-Test": "v"})
    assert seen == {"data": b"raw", "h": "v"}


def test_test_response_get_json_silent_returns_none() -> None:
    """`_TestResponse.get_json(silent=True)` returns None on bad body."""
    app = App(__name__)

    @app.get("/p")
    def _h() -> str:
        return "not-json"

    with app.test_client() as client:
        assert client.get("/p").get_json(silent=True) is None


def test_test_response_get_json_raises_by_default() -> None:
    """`_TestResponse.get_json()` re-raises on non-JSON body."""
    app = App(__name__)

    @app.get("/p")
    def _h() -> str:
        return "not-json"

    with app.test_client() as client:
        with pytest.raises(json.JSONDecodeError):
            client.get("/p").get_json()


# ---------------------------------------------------------------------------
# _to_response
# ---------------------------------------------------------------------------


def test_to_response_passes_through_response_instance() -> None:
    """A `Response` return value is returned as-is."""
    r = Response("body")
    assert _to_response(r) is r


def test_to_response_tuple_sets_status_on_response() -> None:
    """A `(Response, status)` tuple updates `status_code`."""
    r = Response("body")
    out = _to_response((r, 418))
    assert out.status_code == 418


def test_to_response_dict_becomes_jsonify_with_status() -> None:
    """A `(dict, status)` tuple becomes a JSON response with the given status."""
    out = _to_response(({"a": 1}, 201))
    assert out.status_code == 201
    assert out.get_json() == {"a": 1}


def test_to_response_list_becomes_jsonify() -> None:
    """A list return value is serialised as JSON."""
    out = _to_response([1, 2])
    assert out.get_json() == [1, 2]


def test_to_response_str_becomes_plain_response() -> None:
    """A str return value becomes a plain `Response`."""
    out = _to_response("hi")
    assert out.data == b"hi"


def test_to_response_bytes_becomes_plain_response() -> None:
    """A bytes return value becomes a plain `Response`."""
    out = _to_response(b"raw")
    assert out.data == b"raw"


def test_to_response_tuple_of_wrong_length_raises() -> None:
    """Only two-tuples are allowed; anything else raises TypeError."""
    with pytest.raises(TypeError):
        _to_response(("a", 200, "extra"))


def test_to_response_unsupported_type_raises() -> None:
    """A return type we do not know how to coerce raises TypeError."""
    with pytest.raises(TypeError):
        _to_response(object())


# ---------------------------------------------------------------------------
# App.run / run_app wrappers (delegation tested via monkeypatch)
# ---------------------------------------------------------------------------


def test_app_run_delegates_to_run_app(monkeypatch: pytest.MonkeyPatch) -> None:
    """`App.run(host, port)` forwards to the module-level `run_app`."""
    from autonomy.deploy import _http_server as mod

    called: dict = {}

    def _fake(app: App, host: str, port: int) -> None:
        called["args"] = (app, host, port)

    monkeypatch.setattr(mod, "run_app", _fake)
    app = App(__name__)
    app.run(host="1.2.3.4", port=1234)
    assert called["args"] == (app, "1.2.3.4", 1234)


def test_run_app_closes_server_even_when_serve_forever_returns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`run_app` must call `server_close()` via the `finally` branch."""
    from autonomy.deploy import _http_server as mod

    events: list = []

    class _FakeServer:
        def __init__(self, _addr: Any, _handler: Any) -> None:
            events.append("init")

        def serve_forever(self) -> None:
            events.append("serve_forever")

        def server_close(self) -> None:
            events.append("server_close")

    monkeypatch.setattr(mod, "ThreadingHTTPServer", _FakeServer)
    mod.run_app(App(__name__), "127.0.0.1", 0)
    assert events == ["init", "serve_forever", "server_close"]


# ---------------------------------------------------------------------------
# _build_handler_class — integration via a threaded real HTTP server
# ---------------------------------------------------------------------------


def _get_free_port() -> int:
    """Return an ephemeral localhost port."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_built_handler_dispatches_real_http_requests() -> None:
    """Spin up a real `ThreadingHTTPServer` and verify end-to-end dispatch."""
    app = App(__name__)

    @app.get("/hello")
    def _g() -> Any:
        return {"greeting": "hi"}

    @app.post("/echo/<int:n>")
    def _p(n: int) -> Any:
        body = request.get_json()
        return {"n": n, "body": body}

    @app.errorhandler(500)
    def _five_hundred(_: InternalServerError) -> Any:
        return "handled", 500

    @app.route("/boom", methods=["GET"])
    def _boom() -> str:
        raise RuntimeError("boom")

    @app.get("/with-headers")
    def _with_headers() -> Any:
        # Returns a Response with a custom header so the `_serve` loop
        # that forwards `resp.headers` to the wire is exercised.
        return Response(b"ok", headers={"X-Custom": "yes"})

    port = _get_free_port()
    server = ThreadingHTTPServer(("127.0.0.1", port), _build_handler_class(app))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        # give the server a moment to bind (usually instant, but be safe)
        for _ in range(50):
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                    break
            except OSError:  # pragma: no cover
                time.sleep(0.05)

        # GET → json handler
        with urllib.request.urlopen(  # nosec B310  # hard-coded 127.0.0.1 test server
            f"http://127.0.0.1:{port}/hello", timeout=5
        ) as r:
            assert json.loads(r.read()) == {"greeting": "hi"}

        # POST with int path param + json body
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/echo/7",
            data=json.dumps({"x": 1}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as r:  # nosec B310
            assert json.loads(r.read()) == {"n": 7, "body": {"x": 1}}

        # 500 path → custom handler response
        try:
            urllib.request.urlopen(  # nosec B310
                f"http://127.0.0.1:{port}/boom", timeout=5
            )
        except urllib.error.HTTPError as e:
            assert e.code == 500
            assert e.read() == b"handled"
        else:  # pragma: no cover
            pytest.fail("expected HTTP 500")

        # 404 path → default handler
        try:
            urllib.request.urlopen(  # nosec B310
                f"http://127.0.0.1:{port}/nope", timeout=5
            )
        except urllib.error.HTTPError as e:
            assert e.code == 404
        else:  # pragma: no cover
            pytest.fail("expected HTTP 404")

        # custom-header forwarding path
        with urllib.request.urlopen(  # nosec B310
            f"http://127.0.0.1:{port}/with-headers", timeout=5
        ) as r:
            assert r.headers.get("X-Custom") == "yes"
            assert r.read() == b"ok"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
