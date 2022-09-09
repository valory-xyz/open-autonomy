<a id="autonomy.deploy.base"></a>

# autonomy.deploy.base

Base deployments module.

<a id="autonomy.deploy.base.ServiceSpecification"></a>

## ServiceSpecification Objects

```python
class ServiceSpecification()
```

Class to assist with generating deployments.

<a id="autonomy.deploy.base.ServiceSpecification.__init__"></a>

#### `__`init`__`

```python
def __init__(service_path: Path, keys: Path, number_of_agents: Optional[int] = None, private_keys_password: Optional[str] = None, agent_instances: Optional[List[str]] = None, log_level: str = INFO, substitute_env_vars: bool = False) -> None
```

Initialize the Base Deployment.

<a id="autonomy.deploy.base.ServiceSpecification.read_keys"></a>

#### read`_`keys

```python
def read_keys(file_path: Path) -> None
```

Read in keys from a file on disk.

<a id="autonomy.deploy.base.ServiceSpecification.process_model_args_overrides"></a>

#### process`_`model`_`args`_`overrides

```python
def process_model_args_overrides(agent_n: int) -> Dict
```

Generates env vars based on model overrides.

<a id="autonomy.deploy.base.ServiceSpecification.generate_agents"></a>

#### generate`_`agents

```python
def generate_agents() -> List
```

Generate multiple agent.

<a id="autonomy.deploy.base.ServiceSpecification.generate_common_vars"></a>

#### generate`_`common`_`vars

```python
def generate_common_vars(agent_n: int) -> Dict
```

Retrieve vars common for valory apps.

<a id="autonomy.deploy.base.ServiceSpecification.generate_agent"></a>

#### generate`_`agent

```python
def generate_agent(agent_n: int, override_idx: Optional[int] = None) -> Dict[Any, Any]
```

Generate next agent.

<a id="autonomy.deploy.base.BaseDeploymentGenerator"></a>

## BaseDeploymentGenerator Objects

```python
class BaseDeploymentGenerator()
```

Base Deployment Class.

<a id="autonomy.deploy.base.BaseDeploymentGenerator.__init__"></a>

#### `__`init`__`

```python
def __init__(service_spec: ServiceSpecification, build_dir: Path, dev_mode: bool = False, packages_dir: Optional[Path] = None, open_aea_dir: Optional[Path] = None, open_autonomy_dir: Optional[Path] = None)
```

Initialise with only kwargs.

<a id="autonomy.deploy.base.BaseDeploymentGenerator.generate"></a>

#### generate

```python
@abc.abstractmethod
def generate(image_version: Optional[str] = None) -> "BaseDeploymentGenerator"
```

Generate the deployment configuration.

<a id="autonomy.deploy.base.BaseDeploymentGenerator.generate_config_tendermint"></a>

#### generate`_`config`_`tendermint

```python
@abc.abstractmethod
def generate_config_tendermint() -> "BaseDeploymentGenerator"
```

Generate the deployment configuration.

<a id="autonomy.deploy.base.BaseDeploymentGenerator.populate_private_keys"></a>

#### populate`_`private`_`keys

```python
@abc.abstractmethod
def populate_private_keys() -> "BaseDeploymentGenerator"
```

Populate the private keys to the deployment.

<a id="autonomy.deploy.base.BaseDeploymentGenerator.write_config"></a>

#### write`_`config

```python
def write_config() -> "BaseDeploymentGenerator"
```

Write output to build dir

