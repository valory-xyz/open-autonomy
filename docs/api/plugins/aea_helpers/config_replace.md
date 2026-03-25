<a id="plugins.aea-helpers.aea_helpers.config_replace"></a>

# plugins.aea-helpers.aea`_`helpers.config`_`replace

Replace agent config values with environment variables using a mapping file.

<a id="plugins.aea-helpers.aea_helpers.config_replace.find_and_replace"></a>

#### find`_`and`_`replace

```python
def find_and_replace(config: list, path: list, new_value: Any) -> list
```

Find and replace a variable in the agent config.

Traverses a multi-document YAML config, finds sections containing
the specified path, and replaces the template value with new_value.
Handles ${type:value} format — preserves the type prefix.

**Arguments**:

- `config`: list of YAML documents from safe_load_all.
- `path`: list of keys forming the path to the value.
- `new_value`: the new value to substitute.

**Returns**:

the updated config list.

<a id="plugins.aea-helpers.aea_helpers.config_replace.load_mapping"></a>

#### load`_`mapping

```python
def load_mapping(mapping_path: Path) -> Dict[str, str]
```

Load a config mapping file (JSON or YAML).

<a id="plugins.aea-helpers.aea_helpers.config_replace.run_config_replace"></a>

#### run`_`config`_`replace

```python
def run_config_replace(mapping: Dict[str, str],
                       agent_dir: str = "agent",
                       env_file: str = ".env") -> None
```

Replace config values in agent's aea-config.yaml using env vars.

<a id="plugins.aea-helpers.aea_helpers.config_replace.config_replace"></a>

#### config`_`replace

```python
@click.command(name="config-replace")
@click.option(
    "--mapping",
    "mapping_path",
    required=True,
    type=click.Path(exists=True),
    help="Path to config mapping file (JSON or YAML).",
)
@click.option(
    "--env-file",
    default=".env",
    help="Path to .env file (default: .env).",
)
@click.option(
    "--agent-dir",
    default="agent",
    help="Agent directory name (default: agent).",
)
def config_replace(mapping_path: str, env_file: str, agent_dir: str) -> None
```

Replace agent config values with environment variables.

