<a id="autonomy.test_tools.helpers.async_utils"></a>

# autonomy.test`_`tools.helpers.async`_`utils

Helpers for Pytest tests with asynchronous programming.

<a id="autonomy.test_tools.helpers.async_utils.wait_for_condition"></a>

#### wait`_`for`_`condition

```python
def wait_for_condition(condition_checker: Callable, timeout: int = 2, error_msg: str = "Timeout", period: float = 0.001) -> None
```

Wait for condition occures in selected timeout.

<a id="autonomy.test_tools.helpers.async_utils.AnotherThreadTask"></a>

## AnotherThreadTask Objects

```python
class AnotherThreadTask()
```

Schedule a task to run on the loop in another thread.

Provides better cancel behaviour: on cancel it will wait till cancelled completely.

<a id="autonomy.test_tools.helpers.async_utils.AnotherThreadTask.__init__"></a>

#### `__`init`__`

```python
def __init__(coro: Awaitable, loop: AbstractEventLoop) -> None
```

Init the task.

**Arguments**:

- `coro`: coroutine to schedule
- `loop`: an event loop to schedule on.

<a id="autonomy.test_tools.helpers.async_utils.AnotherThreadTask.result"></a>

#### result

```python
def result(timeout: Optional[float] = None) -> Any
```

Wait for coroutine execution result.

**Arguments**:

- `timeout`: optional timeout to wait in seconds.

**Returns**:

result

<a id="autonomy.test_tools.helpers.async_utils.AnotherThreadTask.cancel"></a>

#### cancel

```python
def cancel() -> None
```

Cancel coroutine task execution in a target loop.

<a id="autonomy.test_tools.helpers.async_utils.AnotherThreadTask.done"></a>

#### done

```python
def done() -> bool
```

Check task is done.

<a id="autonomy.test_tools.helpers.async_utils.ThreadedAsyncRunner"></a>

## ThreadedAsyncRunner Objects

```python
class ThreadedAsyncRunner(Thread)
```

Util to run thread with event loop and execute coroutines inside.

<a id="autonomy.test_tools.helpers.async_utils.ThreadedAsyncRunner.__init__"></a>

#### `__`init`__`

```python
def __init__(loop: Optional[AbstractEventLoop] = None) -> None
```

Init threaded runner.

**Arguments**:

- `loop`: optional event loop. is it's running loop, threaded runner will use it.

<a id="autonomy.test_tools.helpers.async_utils.ThreadedAsyncRunner.start"></a>

#### start

```python
def start() -> None
```

Start event loop in dedicated thread.

<a id="autonomy.test_tools.helpers.async_utils.ThreadedAsyncRunner.run"></a>

#### run

```python
def run() -> None
```

Run code inside thread.

<a id="autonomy.test_tools.helpers.async_utils.ThreadedAsyncRunner.call"></a>

#### call

```python
def call(coro: Awaitable) -> Any
```

Run a coroutine inside the event loop.

**Arguments**:

- `coro`: a coroutine to run.

**Returns**:

task

<a id="autonomy.test_tools.helpers.async_utils.ThreadedAsyncRunner.stop"></a>

#### stop

```python
def stop() -> None
```

Stop event loop in thread.

<a id="autonomy.test_tools.helpers.async_utils.BaseThreadedAsyncLoop"></a>

## BaseThreadedAsyncLoop Objects

```python
class BaseThreadedAsyncLoop()
```

Test class with a threaded event loop running.

<a id="autonomy.test_tools.helpers.async_utils.BaseThreadedAsyncLoop.setup"></a>

#### setup

```python
def setup() -> None
```

Set up the class.

<a id="autonomy.test_tools.helpers.async_utils.BaseThreadedAsyncLoop.execute"></a>

#### execute

```python
def execute(coro: Awaitable, timeout: float = DEFAULT_ASYNC_TIMEOUT) -> Any
```

Execute a coroutine and wait its completion.

<a id="autonomy.test_tools.helpers.async_utils.BaseThreadedAsyncLoop.teardown"></a>

#### teardown

```python
def teardown() -> None
```

Teardown the class.

