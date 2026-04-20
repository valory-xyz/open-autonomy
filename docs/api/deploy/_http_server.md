<a id="autonomy.deploy._http_server"></a>

# autonomy.deploy.`_`http`_`server

Minimal Flask-compatible HTTP server.

Covers the subset of Flask/Werkzeug used by
``autonomy.deploy.generators.localhost.tendermint.app`` and
``autonomy.replay.tendermint``: ``App``, ``Request``, ``Response``,
``jsonify``, route decorators, error handlers, an in-process
``test_client()`` for unit tests, and a threaded HTTP/1.1 server
for production use. Deliberately API-compatible so callers don't
need to change and the switch can be reverted.

<a id="autonomy.deploy._http_server.HTTPException"></a>

## HTTPException Objects

```python
class HTTPException(Exception)
```

Base class for HTTP errors.

<a id="autonomy.deploy._http_server.NotFound"></a>

## NotFound Objects

```python
class NotFound(HTTPException)
```

404 Not Found.

<a id="autonomy.deploy._http_server.InternalServerError"></a>

## InternalServerError Objects

```python
class InternalServerError(HTTPException)
```

500 Internal Server Error.

<a id="autonomy.deploy._http_server._Args"></a>

## `_`Args Objects

```python
class _Args(dict)
```

Query-string args with Flask's ``get(key, default=None, type=None)``.

<a id="autonomy.deploy._http_server._Args.get"></a>

#### get

```python
def get(key: str,
        default: Any = None,
        type: Optional[Callable[[str], Any]] = None) -> Any
```

Return *key* from the query string, optionally coerced via *type*.

**Arguments**:

- `key`: query-string key to look up.
- `default`: value to return when *key* is absent.
- `type`: optional callable to coerce the string value.

**Returns**:

the (optionally coerced) value or *default*.

<a id="autonomy.deploy._http_server.Request"></a>

## Request Objects

```python
class Request()
```

Flask-compatible request object.

<a id="autonomy.deploy._http_server.Request.__init__"></a>

#### `__`init`__`

```python
def __init__(method: str, path: str, args: Mapping[str, str], data: bytes,
             headers: Mapping[str, str]) -> None
```

Initialize a request.

<a id="autonomy.deploy._http_server.Request.get_data"></a>

#### get`_`data

```python
def get_data() -> bytes
```

Return the raw request body bytes.

<a id="autonomy.deploy._http_server.Request.get_json"></a>

#### get`_`json

```python
def get_json(silent: bool = False) -> Any
```

Parse the body as JSON.

<a id="autonomy.deploy._http_server.Response"></a>

## Response Objects

```python
class Response()
```

Minimal Flask-compatible Response.

<a id="autonomy.deploy._http_server.Response.__init__"></a>

#### `__`init`__`

```python
def __init__(response: Union[str, bytes, None] = None,
             status: int = 200,
             mimetype: Optional[str] = None,
             headers: Optional[Mapping[str, str]] = None) -> None
```

Initialize a response.

<a id="autonomy.deploy._http_server.Response.get_json"></a>

#### get`_`json

```python
def get_json(silent: bool = False) -> Any
```

Parse the body as JSON.

<a id="autonomy.deploy._http_server.jsonify"></a>

#### jsonify

```python
def jsonify(*args: Any, **kwargs: Any) -> Response
```

Serialize a value to a JSON Response, mirroring ``flask.jsonify``.

* ``jsonify({"a": 1})`` — one positional arg is used as the body.
* ``jsonify(a=1, b=2)`` — keyword args form an object.
* ``jsonify(1, 2, 3)`` — multiple positional args form a list.

**Arguments**:

- `args`: positional value(s) to serialize.
- `kwargs`: keyword pairs to serialize as an object.

**Raises**:

- `TypeError`: when both positional and keyword args are given.

**Returns**:

a :class:`Response` with ``application/json`` mimetype.

<a id="autonomy.deploy._http_server._Route"></a>

## `_`Route Objects

```python
class _Route()
```

A single route: method(s), URL pattern, handler.

<a id="autonomy.deploy._http_server._Route.__init__"></a>

#### `__`init`__`

```python
def __init__(methods: List[str], pattern: str, handler: _Handler) -> None
```

Initialize a route and compile its URL pattern.

<a id="autonomy.deploy._http_server._Route.match"></a>

#### match

```python
def match(path: str) -> Optional[Dict[str, Any]]
```

Return captured path params if *path* matches, else ``None``.

<a id="autonomy.deploy._http_server._AppContext"></a>

## `_`AppContext Objects

```python
class _AppContext()
```

Stand-in for ``flask.ctx.AppContext`` — a no-op context manager.

<a id="autonomy.deploy._http_server._AppContext.push"></a>

#### push

```python
def push() -> None
```

No-op.

<a id="autonomy.deploy._http_server._AppContext.pop"></a>

#### pop

```python
def pop() -> None
```

No-op.

<a id="autonomy.deploy._http_server._AppContext.__enter__"></a>

#### `__`enter`__`

```python
def __enter__() -> "_AppContext"
```

Return self.

<a id="autonomy.deploy._http_server._AppContext.__exit__"></a>

#### `__`exit`__`

```python
def __exit__(exc_type: Any, exc_val: Any, exc_tb: Any) -> None
```

No-op.

<a id="autonomy.deploy._http_server.App"></a>

## App Objects

```python
class App()
```

Minimal Flask-compatible application.

<a id="autonomy.deploy._http_server.App.__init__"></a>

#### `__`init`__`

```python
def __init__(name: str) -> None
```

Initialize the app with an identifying *name*.

<a id="autonomy.deploy._http_server.App.route"></a>

#### route

```python
def route(
        rule: str,
        methods: Optional[List[str]] = None) -> Callable[[_Handler], _Handler]
```

Register a handler for *rule* (GET by default).

<a id="autonomy.deploy._http_server.App.get"></a>

#### get

```python
def get(rule: str) -> Callable[[_Handler], _Handler]
```

Register a GET handler.

<a id="autonomy.deploy._http_server.App.post"></a>

#### post

```python
def post(rule: str) -> Callable[[_Handler], _Handler]
```

Register a POST handler.

<a id="autonomy.deploy._http_server.App.errorhandler"></a>

#### errorhandler

```python
def errorhandler(code: int) -> Callable[[_Handler], _Handler]
```

Register a handler for HTTP *code* (e.g. 404, 500).

<a id="autonomy.deploy._http_server.App.app_context"></a>

#### app`_`context

```python
def app_context() -> _AppContext
```

Return a no-op application context.

<a id="autonomy.deploy._http_server.App.test_client"></a>

#### test`_`client

```python
def test_client() -> "_TestClient"
```

Return an in-process test client.

<a id="autonomy.deploy._http_server.App.run"></a>

#### run

```python
def run(host: str = "127.0.0.1", port: int = 5000) -> None
```

Serve this app on *host:port* — matches ``flask.Flask.run``.

<a id="autonomy.deploy._http_server.App.dispatch"></a>

#### dispatch

```python
def dispatch(req: Request) -> Response
```

Dispatch *req* to the matching handler (or an error handler).

<a id="autonomy.deploy._http_server._TestClient"></a>

## `_`TestClient Objects

```python
class _TestClient()
```

In-process test client mirroring ``flask.testing.FlaskClient``.

<a id="autonomy.deploy._http_server._TestClient.__init__"></a>

#### `__`init`__`

```python
def __init__(app: App) -> None
```

Initialize the test client.

<a id="autonomy.deploy._http_server._TestClient.__enter__"></a>

#### `__`enter`__`

```python
def __enter__() -> "_TestClient"
```

Return self (context-manager compatibility).

<a id="autonomy.deploy._http_server._TestClient.__exit__"></a>

#### `__`exit`__`

```python
def __exit__(exc_type: Any, exc_val: Any, exc_tb: Any) -> None
```

No-op cleanup.

<a id="autonomy.deploy._http_server._TestClient.get"></a>

#### get

```python
def get(path: str, **kwargs: Any) -> "_TestResponse"
```

Send a GET request.

<a id="autonomy.deploy._http_server._TestClient.post"></a>

#### post

```python
def post(path: str, **kwargs: Any) -> "_TestResponse"
```

Send a POST request.

<a id="autonomy.deploy._http_server._TestResponse"></a>

## `_`TestResponse Objects

```python
class _TestResponse()
```

Test response mirroring ``flask.wrappers.Response``.

<a id="autonomy.deploy._http_server._TestResponse.__init__"></a>

#### `__`init`__`

```python
def __init__(response: Response) -> None
```

Wrap *response* for test-client consumers.

<a id="autonomy.deploy._http_server._TestResponse.get_json"></a>

#### get`_`json

```python
def get_json(silent: bool = False) -> Any
```

Parse the body as JSON.

<a id="autonomy.deploy._http_server.run_app"></a>

#### run`_`app

```python
def run_app(app: App, host: str, port: int) -> None
```

Serve *app* on *host:port* using a threaded HTTP/1.1 server (blocks).

