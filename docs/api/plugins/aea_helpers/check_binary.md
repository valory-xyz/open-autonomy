<a id="plugins.aea-helpers.aea_helpers.check_binary"></a>

# plugins.aea-helpers.aea`_`helpers.check`_`binary

Check that a built agent runner binary starts correctly.

<a id="plugins.aea-helpers.aea_helpers.check_binary.run_binary_check"></a>

#### run`_`binary`_`check

```python
def run_binary_check(binary_path: str,
                     agent_dir: str = "agent",
                     timeout: int = 80,
                     search_string: str = "Starting AEA",
                     env_vars: Optional[Dict[str, str]] = None) -> bool
```

Spawn the agent runner binary and check for successful startup.

Runs the binary in a subprocess, monitoring stdout for a search string
that indicates the agent started successfully.

**Arguments**:

- `binary_path`: path to the compiled binary.
- `agent_dir`: path to agent directory.
- `timeout`: max seconds to wait for the search string.
- `search_string`: string indicating successful startup.
- `env_vars`: additional environment variables to set.

**Returns**:

True if search string found within timeout.

<a id="plugins.aea-helpers.aea_helpers.check_binary.check_binary"></a>

#### check`_`binary

```python
@click.command(name="check-binary")
@click.argument("binary_path", type=click.Path(exists=True))
@click.argument("agent_dir", type=click.Path(exists=True), default="agent")
@click.option(
    "--timeout",
    default=80,
    type=int,
    help="Max seconds to wait for the search string (default: 80).",
)
@click.option(
    "--search-string",
    default="Starting AEA",
    help='String indicating successful startup (default: "Starting AEA").',
)
@click.option(
    "--env-var",
    "env_vars_raw",
    multiple=True,
    help="Extra env vars as KEY=VALUE (repeatable).",
)
def check_binary(binary_path: str, agent_dir: str, timeout: int,
                 search_string: str, env_vars_raw: tuple) -> None
```

Check that a built agent runner binary starts correctly.

Spawns BINARY_PATH in a subprocess, monitors stdout for the search string,
and exits 0 on success or 1 on timeout.

**Arguments**:

- `binary_path`: path to the compiled binary.
- `agent_dir`: path to agent directory.
- `timeout`: max seconds to wait for the search string.
- `search_string`: string indicating successful startup.
- `env_vars_raw`: extra env vars as KEY=VALUE (repeatable).

