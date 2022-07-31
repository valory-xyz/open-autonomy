<a id="autonomy.test_tools.helpers.base"></a>

# autonomy.test`_`tools.helpers.base

Utilities for the autonomy test tools.

<a id="autonomy.test_tools.helpers.base.tendermint_health_check"></a>

#### tendermint`_`health`_`check

```python
def tendermint_health_check(url: str, max_retries: int = MAX_RETRIES, sleep_interval: float = 1.0, timeout: float = DEFAULT_REQUESTS_TIMEOUT) -> bool
```

Wait until a Tendermint RPC server is up.

<a id="autonomy.test_tools.helpers.base.cd"></a>

#### cd

```python
@contextlib.contextmanager
def cd(path: PathLike) -> Generator
```

Change working directory temporarily.

<a id="autonomy.test_tools.helpers.base.try_send"></a>

#### try`_`send

```python
def try_send(gen: Generator, obj: Any = None) -> None
```

Try to send an object to a generator.

**Arguments**:

- `gen`: the generator.
- `obj`: the object.

<a id="autonomy.test_tools.helpers.base.make_round_class"></a>

#### make`_`round`_`class

```python
def make_round_class(name: str, bases: Tuple = (AbstractRound,)) -> Type[AbstractRound]
```

Make a round class.

