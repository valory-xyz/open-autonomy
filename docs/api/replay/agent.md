<a id="autonomy.replay.agent"></a>

# autonomy.replay.agent

Tools to build and run agents from existing deployments.

<a id="autonomy.replay.agent.AgentRunner"></a>

## AgentRunner Objects

```python
class AgentRunner()
```

Agent runner.

<a id="autonomy.replay.agent.AgentRunner.process"></a>

#### process

nosec

<a id="autonomy.replay.agent.AgentRunner.__init__"></a>

#### `__`init`__`

```python
def __init__(agent_id: int, agent_data: Dict, registry_path: Path) -> None
```

Initialize object.

<a id="autonomy.replay.agent.AgentRunner.start"></a>

#### start

```python
def start() -> None
```

Start process.

<a id="autonomy.replay.agent.AgentRunner.stop"></a>

#### stop

```python
def stop() -> None
```

Stop the process.

