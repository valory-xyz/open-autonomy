<a id="aea_swarm.deploy.base"></a>

# aea`_`swarm.deploy.base

Base deployments module.

<a id="aea_swarm.deploy.base.recurse"></a>

#### recurse

```python
def recurse(_obj_json: Dict[str, Any]) -> Dict[str, Any]
```

Recursively explore a json object until no dictionaries remain.

<a id="aea_swarm.deploy.base.DeploymentConfigValidator"></a>

## DeploymentConfigValidator Objects

```python
class DeploymentConfigValidator(validation.ConfigValidator)
```

Configuration validator implementation.

<a id="aea_swarm.deploy.base.DeploymentConfigValidator.__init__"></a>

#### `__`init`__`

```python
def __init__(schema_filename: str, env_vars_friendly: bool = False) -> None
```

Initialize the parser for configuration files.

**Arguments**:

- `schema_filename`: the path to the JSON-schema file in 'aea/configurations/schemas'.
- `env_vars_friendly`: whether or not it is env var friendly.

<a id="aea_swarm.deploy.base.DeploymentConfigValidator.validate_deployment"></a>

#### validate`_`deployment

```python
def validate_deployment(deployment_spec: Dict, overrides: List) -> bool
```

Sense check the deployment spec.

<a id="aea_swarm.deploy.base.DeploymentConfigValidator.check_overrides_match_spec"></a>

#### check`_`overrides`_`match`_`spec

```python
def check_overrides_match_spec() -> bool
```

Check that overrides are valid.

- number of overrides is 1
- number of overrides == number of agents in spec
- number of overrides is 0

**Returns**:

True if overrides are valid

<a id="aea_swarm.deploy.base.DeploymentConfigValidator.check_overrides_are_valid"></a>

#### check`_`overrides`_`are`_`valid

```python
def check_overrides_are_valid() -> Dict[ComponentId, Dict[Any, Any]]
```

Uses the aea helper libraries to check individual overrides.

<a id="aea_swarm.deploy.base.DeploymentConfigValidator.process_component_section"></a>

#### process`_`component`_`section

```python
def process_component_section(component_index: int, component_configuration_json: Dict) -> Tuple[ComponentId, Dict]
```

Process a component configuration in an agent configuration file.

It breaks down in:
- extract the component id
- validate the component configuration
- check that there are only configurable fields

**Arguments**:

- `component_index`: the index of the component in the file.
- `component_configuration_json`: the JSON object.

**Returns**:

the processed component configuration.

<a id="aea_swarm.deploy.base.DeploymentConfigValidator.try_to_process_singular_override"></a>

#### try`_`to`_`process`_`singular`_`override

```python
@staticmethod
def try_to_process_singular_override(component_id: ComponentId, config_class: ComponentConfiguration, component_configuration_json: Dict) -> Dict
```

Try to process component with a singular component overrides.

<a id="aea_swarm.deploy.base.DeploymentConfigValidator.try_to_process_nested_fields"></a>

#### try`_`to`_`process`_`nested`_`fields

```python
def try_to_process_nested_fields(component_id: ComponentId, component_index: int, config_class: ComponentConfiguration, component_configuration_json: Dict) -> Dict
```

Try to process component with nested overrides.

<a id="aea_swarm.deploy.base.DeploymentSpec"></a>

## DeploymentSpec Objects

```python
class DeploymentSpec()
```

Class to assist with generating deployments.

<a id="aea_swarm.deploy.base.DeploymentSpec.__init__"></a>

#### `__`init`__`

```python
def __init__(path_to_deployment_spec: str, private_keys_file_path: Path, package_dir: Path, private_keys_password: Optional[str] = None, number_of_agents: Optional[int] = None) -> None
```

Initialize the Base Deployment.

<a id="aea_swarm.deploy.base.DeploymentSpec.read_keys"></a>

#### read`_`keys

```python
def read_keys(file_path: Path) -> None
```

Read in keys from a file on disk.

<a id="aea_swarm.deploy.base.DeploymentSpec.generate_agents"></a>

#### generate`_`agents

```python
def generate_agents() -> List
```

Generate multiple agent.

<a id="aea_swarm.deploy.base.DeploymentSpec.generate_common_vars"></a>

#### generate`_`common`_`vars

```python
def generate_common_vars(agent_n: int) -> Dict
```

Retrieve vars common for valory apps.

<a id="aea_swarm.deploy.base.DeploymentSpec.generate_agent"></a>

#### generate`_`agent

```python
def generate_agent(agent_n: int) -> Dict[Any, Any]
```

Generate next agent.

<a id="aea_swarm.deploy.base.DeploymentSpec.load_agent"></a>

#### load`_`agent

```python
def load_agent() -> List[Dict[str, str]]
```

Using specified valory app, try to load the aea.

<a id="aea_swarm.deploy.base.DeploymentSpec.locate_agent_from_package_directory"></a>

#### locate`_`agent`_`from`_`package`_`directory

```python
def locate_agent_from_package_directory(local_registry: bool = True) -> str
```

Using the deployment id, locate the registry and retrieve the path.

<a id="aea_swarm.deploy.base.BaseDeploymentGenerator"></a>

## BaseDeploymentGenerator Objects

```python
class BaseDeploymentGenerator()
```

Base Deployment Class.

<a id="aea_swarm.deploy.base.BaseDeploymentGenerator.__init__"></a>

#### `__`init`__`

```python
def __init__(deployment_spec: DeploymentSpec, build_dir: Path)
```

Initialise with only kwargs.

<a id="aea_swarm.deploy.base.BaseDeploymentGenerator.generate"></a>

#### generate

```python
@abc.abstractmethod
def generate(dev_mode: bool = False) -> "BaseDeploymentGenerator"
```

Generate the deployment configuration.

<a id="aea_swarm.deploy.base.BaseDeploymentGenerator.generate_config_tendermint"></a>

#### generate`_`config`_`tendermint

```python
@abc.abstractmethod
def generate_config_tendermint() -> "BaseDeploymentGenerator"
```

Generate the deployment configuration.

<a id="aea_swarm.deploy.base.BaseDeploymentGenerator.populate_private_keys"></a>

#### populate`_`private`_`keys

```python
@abc.abstractmethod
def populate_private_keys() -> "BaseDeploymentGenerator"
```

Populate the private keys to the deployment.

<a id="aea_swarm.deploy.base.BaseDeploymentGenerator.get_deployment_network_configuration"></a>

#### get`_`deployment`_`network`_`configuration

```python
def get_deployment_network_configuration(agent_vars: List[Dict[str, Any]]) -> List
```

Retrieve the appropriate network configuration based on deployment & network.

<a id="aea_swarm.deploy.base.BaseDeploymentGenerator.write_config"></a>

#### write`_`config

```python
def write_config() -> "BaseDeploymentGenerator"
```

Write output to build dir

