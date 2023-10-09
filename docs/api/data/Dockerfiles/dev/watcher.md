<a id="autonomy.data.Dockerfiles.dev.watcher"></a>

# autonomy.data.Dockerfiles.dev.watcher

Watcher script and wrapper container for agent.

<a id="autonomy.data.Dockerfiles.dev.watcher.write"></a>

#### write

```python
def write(line: str) -> None
```

Write to console.

<a id="autonomy.data.Dockerfiles.dev.watcher.call_vote"></a>

#### call`_`vote

```python
def call_vote() -> None
```

Call vote.

Since there's a lot of resource sharing between docker containers one of the
environments can fallback during `base_setup` so to make sure there's no error
caused by one of the agents left behind this method will help.

<a id="autonomy.data.Dockerfiles.dev.watcher.AEARunner"></a>

## AEARunner Objects

```python
class AEARunner()
```

AEA Runner.

<a id="autonomy.data.Dockerfiles.dev.watcher.AEARunner.process"></a>

#### process

nosec

<a id="autonomy.data.Dockerfiles.dev.watcher.AEARunner.__init__"></a>

#### `__`init`__`

```python
def __init__() -> None
```

Initialize runner.

<a id="autonomy.data.Dockerfiles.dev.watcher.AEARunner.restart_tendermint"></a>

#### restart`_`tendermint

```python
@staticmethod
def restart_tendermint() -> None
```

Restart respective tendermint node.

<a id="autonomy.data.Dockerfiles.dev.watcher.AEARunner.start"></a>

#### start

```python
def start() -> None
```

Start AEA process.

<a id="autonomy.data.Dockerfiles.dev.watcher.AEARunner.stop"></a>

#### stop

```python
def stop() -> None
```

Stop AEA process.

<a id="autonomy.data.Dockerfiles.dev.watcher.EventHandler"></a>

## EventHandler Objects

```python
class EventHandler(FileSystemEventHandler)
```

Handle file updates.

<a id="autonomy.data.Dockerfiles.dev.watcher.EventHandler.__init__"></a>

#### `__`init`__`

```python
def __init__(aea_runner: AEARunner,
             fingerprint_on_restart: bool = True) -> None
```

Initialize object.

<a id="autonomy.data.Dockerfiles.dev.watcher.EventHandler.fingerprint_item"></a>

#### fingerprint`_`item

```python
@staticmethod
def fingerprint_item(src_path: str) -> None
```

Fingerprint items.

<a id="autonomy.data.Dockerfiles.dev.watcher.EventHandler.clean_up"></a>

#### clean`_`up

```python
@staticmethod
def clean_up() -> None
```

Clean up from previous run.

<a id="autonomy.data.Dockerfiles.dev.watcher.EventHandler.on_any_event"></a>

#### on`_`any`_`event

```python
def on_any_event(event: FileSystemEvent) -> None
```

This method reloads the agent when a change is detected in *.py file.

