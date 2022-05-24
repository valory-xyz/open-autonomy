<a id="aea_swarm.configurations.loader"></a>

# aea`_`swarm.configurations.loader

Service component base.

<a id="aea_swarm.configurations.loader.recurse"></a>

#### recurse

```python
def recurse(obj: Dict[str, Any]) -> Dict[str, Any]
```

Recursively explore a json object until no dictionaries remain.

<a id="aea_swarm.configurations.loader.ServiceConfigValidator"></a>

## ServiceConfigValidator Objects

```python
class ServiceConfigValidator(validation.ConfigValidator)
```

Configuration validator implementation.

<a id="aea_swarm.configurations.loader.ServiceConfigValidator.__init__"></a>

#### `__`init`__`

```python
def __init__(schema_filename: str, env_vars_friendly: bool = False) -> None
```

Initialize the parser for configuration files.

**Arguments**:

- `schema_filename`: the path to the JSON-schema file in 'aea/configurations/schemas'.
- `env_vars_friendly`: whether or not it is env var friendly.

<a id="aea_swarm.configurations.loader.ServiceConfigValidator.check_overrides_match_spec"></a>

#### check`_`overrides`_`match`_`spec

```python
@staticmethod
def check_overrides_match_spec(service_config: Dict, overrides: List) -> bool
```

Check that overrides are valid.

- number of overrides is 1
- number of overrides == number of agents in spec
- number of overrides is 0

**Arguments**:

- `service_config`: Service config
- `overrides`: List of overrides

**Returns**:

True if overrides are valid

<a id="aea_swarm.configurations.loader.ServiceConfigValidator.check_overrides_are_valid"></a>

#### check`_`overrides`_`are`_`valid

```python
def check_overrides_are_valid(service_config: Dict, overrides: List) -> Dict[ComponentId, Dict[Any, Any]]
```

Uses the aea helper libraries to check individual overrides.

<a id="aea_swarm.configurations.loader.ServiceConfigValidator.process_component_section"></a>

#### process`_`component`_`section

```python
@classmethod
def process_component_section(cls, component_index: int, component_configuration_json: Dict, service_config: Dict) -> Tuple[ComponentId, Dict]
```

Process a component configuration in an agent configuration file.

It breaks down in:
- extract the component id
- validate the component configuration
- check that there are only configurable fields

**Arguments**:

- `component_index`: the index of the component in the file.
- `component_configuration_json`: the JSON object.
- `service_config`: Service config

**Returns**:

the processed component configuration.

<a id="aea_swarm.configurations.loader.ServiceConfigValidator.try_to_process_singular_override"></a>

#### try`_`to`_`process`_`singular`_`override

```python
@staticmethod
def try_to_process_singular_override(component_id: ComponentId, config_class: ComponentConfiguration, component_configuration_json: Dict) -> Dict
```

Try to process component with a singular component overrides.

<a id="aea_swarm.configurations.loader.ServiceConfigValidator.try_to_process_nested_fields"></a>

#### try`_`to`_`process`_`nested`_`fields

```python
@staticmethod
def try_to_process_nested_fields(component_id: ComponentId, component_index: int, config_class: ComponentConfiguration, component_configuration_json: Dict, service_config: Dict) -> Dict
```

Try to process component with nested overrides.

<a id="aea_swarm.configurations.loader.load_service_config"></a>

#### load`_`service`_`config

```python
def load_service_config(service_path: Path) -> Tuple[Service, List]
```

Load service config from the path.

