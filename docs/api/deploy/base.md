<a id="aea_swarm.deploy.base"></a>

# aea`_`swarm.deploy.base

Base deployments module.

<a id="aea_swarm.deploy.base.ServiceSpecification"></a>

## ServiceSpecification Objects

```python
class ServiceSpecification()
```

Class to assist with generating deployments.

<a id="aea_swarm.deploy.base.ServiceSpecification.__init__"></a>

#### `__`init`__`

```python
def __init__(service_path: Path, keys: Path, packages_dir: Path, number_of_agents: Optional[int] = None) -> None
```

Initialize the Base Deployment.

<a id="aea_swarm.deploy.base.ServiceSpecification.read_keys"></a>

#### read`_`keys

```python
def __init__(path_to_deployment_spec: str, private_keys_file_path: Path, package_dir: Path, private_keys_password: Optional[str] = None, number_of_agents: Optional[int] = None) -> None
def read_keys(file_path: Path) -> None
```

Read in keys from a file on disk.

<a id="aea_swarm.deploy.base.ServiceSpecification.process_model_args_overrides"></a>

#### process`_`model`_`args`_`overrides

```python
def process_model_args_overrides(agent_n: int) -> Dict
```

Generates env vars based on model overrides.

<a id="aea_swarm.deploy.base.ServiceSpecification.generate_agents"></a>

#### generate`_`agents

```python
def generate_agents() -> List
```

Generate multiple agent.

<a id="aea_swarm.deploy.base.ServiceSpecification.generate_common_vars"></a>

#### generate`_`common`_`vars

```python
def generate_common_vars(agent_n: int) -> Dict
```

Retrieve vars common for valory apps.

<a id="aea_swarm.deploy.base.ServiceSpecification.generate_agent"></a>

#### generate`_`agent

```python
def generate_agent(agent_n: int) -> Dict[Any, Any]
```

Generate next agent.

<a id="aea_swarm.deploy.base.ServiceSpecification.load_agent"></a>

#### load`_`agent

```python
def load_agent() -> List[Dict[str, str]]
```

Using specified valory app, try to load the aea.

<a id="aea_swarm.deploy.base.ServiceSpecification.locate_agent_from_packages_directory"></a>

#### locate`_`agent`_`from`_`packages`_`directory

```python
def locate_agent_from_packages_directory(local_registry: bool = True) -> str
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
def __init__(service_spec: ServiceSpecification, build_dir: Path)
```

Initialise with only kwargs.

<a id="aea_swarm.deploy.base.BaseDeploymentGenerator.generate"></a>

#### generate

```python
@abc.abstractmethod
def generate(image_versions: Dict[str, str], dev_mode: bool = False) -> "BaseDeploymentGenerator"
```

Generate the deployment configuration.

<a id="aea_swarm.deploy.base.BaseDeploymentGenerator.generate_config_tendermint"></a>

#### generate`_`config`_`tendermint

```python
@abc.abstractmethod
def generate_config_tendermint(image_version: str = TENDERMINT_IMAGE_VERSION) -> "BaseDeploymentGenerator"
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

