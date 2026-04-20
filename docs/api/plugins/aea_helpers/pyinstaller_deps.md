<a id="plugins.aea-helpers.aea_helpers.pyinstaller_deps"></a>

# plugins.aea-helpers.aea`_`helpers.pyinstaller`_`deps

Generate PyInstaller hidden-import and collect-all flags from agent dependencies.

<a id="plugins.aea-helpers.aea_helpers.pyinstaller_deps.get_modules_from_dist"></a>

#### get`_`modules`_`from`_`dist

```python
def get_modules_from_dist(dist) -> List[str]
```

Get top-level modules from dist metadata, fallback to directory names.

**Arguments**:

- `dist`: an importlib.metadata Distribution object.

**Returns**:

sorted list of unique module names.

<a id="plugins.aea-helpers.aea_helpers.pyinstaller_deps.get_agent_dependency_modules"></a>

#### get`_`agent`_`dependency`_`modules

```python
def get_agent_dependency_modules(agent_dir: str) -> List[str]
```

Read agent config and resolve installed modules for all dependencies.

**Arguments**:

- `agent_dir`: path to the agent directory.

**Returns**:

sorted list of module names.

<a id="plugins.aea-helpers.aea_helpers.pyinstaller_deps.filter_modules"></a>

#### filter`_`modules

```python
def filter_modules(modules: List[str]) -> List[str]
```

Remove test-related and problematic modules.

**Arguments**:

- `modules`: list of module names.

**Returns**:

filtered list.

<a id="plugins.aea-helpers.aea_helpers.pyinstaller_deps.build_pyinstaller_flags"></a>

#### build`_`pyinstaller`_`flags

```python
def build_pyinstaller_flags(modules: List[str]) -> str
```

Build --hidden-import and --collect-all flags for PyInstaller.

**Arguments**:

- `modules`: list of module names.

**Returns**:

space-separated flag string.

<a id="plugins.aea-helpers.aea_helpers.pyinstaller_deps.build_binary_deps"></a>

#### build`_`binary`_`deps

```python
@click.command(name="build-binary-deps")
@click.argument("agent_dir", type=click.Path(exists=True), default="agent")
def build_binary_deps(agent_dir: str) -> None
```

Print PyInstaller dependency flags for an agent.

Reads the agent's aea-config.yaml, resolves all installed dependencies,
and outputs --hidden-import and --collect-all flags for PyInstaller.

**Arguments**:

- `agent_dir`: path to the agent directory.

<a id="plugins.aea-helpers.aea_helpers.pyinstaller_deps.bin_template_path"></a>

#### bin`_`template`_`path

```python
@click.command(name="bin-template-path")
def bin_template_path() -> None
```

Print the filesystem path to the PyInstaller entry point template.

Agent repos can pass this directly to pyinstaller's --onefile flag
instead of maintaining a local copy of the template.

