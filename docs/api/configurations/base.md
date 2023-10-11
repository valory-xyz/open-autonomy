<a id="autonomy.configurations.base"></a>

# autonomy.configurations.base

Base configurations.

<a id="autonomy.configurations.base.load_dependencies"></a>

#### load`_`dependencies

```python
def load_dependencies(dependencies: Dict) -> Dependencies
```

Load dependencies.

<a id="autonomy.configurations.base.Service"></a>

## Service Objects

```python
class Service(PackageConfiguration)
```

Service package configuration.

<a id="autonomy.configurations.base.Service.__init__"></a>

#### `__`init`__`

```python
def __init__(name: SimpleIdOrStr,
             author: SimpleIdOrStr,
             agent: PublicId,
             version: str = "",
             license_: str = "",
             aea_version: str = "",
             fingerprint: Optional[Dict[str, str]] = None,
             fingerprint_ignore_patterns: Optional[Sequence[str]] = None,
             description: str = "",
             number_of_agents: int = 4,
             build_entrypoint: Optional[str] = None,
             overrides: Optional[List] = None,
             deployment: Optional[Dict] = None,
             dependencies: Optional[Dependencies] = None) -> None
```

Initialise object.

<a id="autonomy.configurations.base.Service.overrides"></a>

#### overrides

```python
@property
def overrides() -> List
```

Returns component overrides.

<a id="autonomy.configurations.base.Service.overrides"></a>

#### overrides

```python
@overrides.setter
def overrides(obj: List) -> None
```

Set overrides.

<a id="autonomy.configurations.base.Service.json"></a>

#### json

```python
@property
def json() -> Dict
```

Returns an ordered Dict for service config.

<a id="autonomy.configurations.base.Service.validate_config_data"></a>

#### validate`_`config`_`data

```python
@classmethod
def validate_config_data(cls,
                         json_data: Dict,
                         env_vars_friendly: bool = False) -> None
```

Validate config data.

<a id="autonomy.configurations.base.Service.check_overrides_valid"></a>

#### check`_`overrides`_`valid

```python
def check_overrides_valid(overrides: List,
                          env_vars_friendly: bool = False) -> None
```

Uses the AEA helper libraries to check individual overrides.

<a id="autonomy.configurations.base.Service.process_metadata"></a>

#### process`_`metadata

```python
@staticmethod
def process_metadata(configuration: Dict) -> Tuple[Dict, ComponentId, bool]
```

Process component override metadata.

<a id="autonomy.configurations.base.Service.process_component_overrides"></a>

#### process`_`component`_`overrides

```python
def process_component_overrides(agent_idx: int,
                                component_configuration_json: Dict) -> Dict
```

Process a component configuration in an agent configuration file.

**Arguments**:

- `agent_idx`: Index of the agent.
- `component_configuration_json`: the JSON object.

**Returns**:

the processed component configuration.

<a id="autonomy.configurations.base.Service.generate_environment_variables"></a>

#### generate`_`environment`_`variables

```python
@staticmethod
def generate_environment_variables(component_id: ComponentId,
                                   component_configuration_json: Dict) -> Dict
```

Try to process component with a singular component overrides.

