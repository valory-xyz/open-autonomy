<a id="plugins.aea-test-autonomy.aea_test_autonomy.helpers.base"></a>

# plugins.aea-test-autonomy.aea`_`test`_`autonomy.helpers.base

Utilities for the Open Autonomy test tools.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.helpers.base.tendermint_health_check"></a>

#### tendermint`_`health`_`check

```python
def tendermint_health_check(url: str,
                            max_retries: int = MAX_RETRIES,
                            sleep_interval: float = 1.0,
                            timeout: float = DEFAULT_REQUESTS_TIMEOUT) -> bool
```

Wait until a Tendermint RPC server is up.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.helpers.base.cd"></a>

#### cd

```python
@contextlib.contextmanager
def cd(path: PathLike) -> Generator
```

Change working directory temporarily.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.helpers.base.try_send"></a>

#### try`_`send

```python
def try_send(gen: Generator, obj: Any = None) -> None
```

Try to send an object to a generator.

**Arguments**:

- `gen`: the generator.
- `obj`: the object.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.helpers.base.identity"></a>

#### identity

```python
def identity(arg: Any) -> Any
```

Define an identity function.

