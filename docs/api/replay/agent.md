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

**Arguments**:

- `agent_id`: numeric id of the agent service entry.
- `agent_data`: docker-compose service block for the agent.
- `registry_path`: local registry path used when fetching the agent package.

**Raises**:

- `ValueError`: if the service block is missing ``environment`` or
an env entry is not formatted as ``KEY=VALUE``.

<a id="autonomy.replay.agent.AgentRunner.start"></a>

#### start

```python
def start() -> None
```

Start process.

**Raises**:

- `ValueError`: if ``AEA_AGENT`` is not present in the
docker-compose service block. A common cause is replaying
against a build dir generated before the
``VALORY_APPLICATION`` → ``AEA_AGENT`` rename.
- `ValueError`: if ``AEA_KEY`` is not present in the
docker-compose service block.

<a id="autonomy.replay.agent.AgentRunner.stop"></a>

#### stop

```python
def stop() -> None
```

Stop the process.

