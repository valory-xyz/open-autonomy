<a id="autonomy.deploy.base"></a>

# autonomy.deploy.base

Base deployments module.

<a id="autonomy.deploy.base.NotValidKeysFile"></a>

## NotValidKeysFile Objects

```python
class NotValidKeysFile(Exception)
```

Raise when provided keys file is not valid.

<a id="autonomy.deploy.base.ServiceBuilder"></a>

## ServiceBuilder Objects

```python
class ServiceBuilder()
```

Class to assist with generating deployments.

<a id="autonomy.deploy.base.ServiceBuilder.__init__"></a>

#### `__`init`__`

```python
def __init__(service: Service,
             keys: Optional[List[Dict[str, str]]] = None,
             private_keys_password: Optional[str] = None,
             agent_instances: Optional[List[str]] = None,
             apply_environment_variables: bool = False) -> None
```

Initialize the Base Deployment.

<a id="autonomy.deploy.base.ServiceBuilder.private_keys_password"></a>

#### private`_`keys`_`password

```python
@property
def private_keys_password() -> Optional[str]
```

Service password for agent keys.

<a id="autonomy.deploy.base.ServiceBuilder.agent_instances"></a>

#### agent`_`instances

```python
@property
def agent_instances() -> Optional[List[str]]
```

Agent instances.

<a id="autonomy.deploy.base.ServiceBuilder.agent_instances"></a>

#### agent`_`instances

```python
@agent_instances.setter
def agent_instances(instances: List[str]) -> None
```

Agent instances setter.

<a id="autonomy.deploy.base.ServiceBuilder.keys"></a>

#### keys

```python
@property
def keys() -> List[Dict[str, str]]
```

Keys.

<a id="autonomy.deploy.base.ServiceBuilder.from_dir"></a>

#### from`_`dir

```python
@classmethod
def from_dir(cls,
             path: Path,
             keys_file: Optional[Path] = None,
             number_of_agents: Optional[int] = None,
             private_keys_password: Optional[str] = None,
             agent_instances: Optional[List[str]] = None,
             apply_environment_variables: bool = False) -> "ServiceBuilder"
```

Service builder from path.

<a id="autonomy.deploy.base.ServiceBuilder.verify_agent_instances"></a>

#### verify`_`agent`_`instances

```python
@staticmethod
def verify_agent_instances(keys: List[Dict[str, str]],
                           agent_instances: List[str]) -> None
```

Cross verify agent instances with the keys.

<a id="autonomy.deploy.base.ServiceBuilder.read_keys"></a>

#### read`_`keys

```python
def read_keys(keys_file: Path) -> None
```

Read in keys from a file on disk.

<a id="autonomy.deploy.base.ServiceBuilder.try_update_runtime_params"></a>

#### try`_`update`_`runtime`_`params

```python
def try_update_runtime_params(
        multisig_address: Optional[str] = None,
        agent_instances: Optional[List[str]] = None,
        consensus_threshold: Optional[int] = None) -> None
```

Try and update setup parameters.

<a id="autonomy.deploy.base.ServiceBuilder.process_component_overrides"></a>

#### process`_`component`_`overrides

```python
def process_component_overrides(agent_n: int) -> Dict
```

Generates env vars based on model overrides.

<a id="autonomy.deploy.base.ServiceBuilder.generate_agents"></a>

#### generate`_`agents

```python
def generate_agents() -> List
```

Generate multiple agent.

<a id="autonomy.deploy.base.ServiceBuilder.generate_common_vars"></a>

#### generate`_`common`_`vars

```python
def generate_common_vars(agent_n: int) -> Dict
```

Retrieve vars common for agent.

<a id="autonomy.deploy.base.ServiceBuilder.generate_agent"></a>

#### generate`_`agent

```python
def generate_agent(agent_n: int,
                   override_idx: Optional[int] = None) -> Dict[Any, Any]
```

Generate next agent.

<a id="autonomy.deploy.base.BaseDeploymentGenerator"></a>

## BaseDeploymentGenerator Objects

```python
class BaseDeploymentGenerator(abc.ABC)
```

Base Deployment Class.

<a id="autonomy.deploy.base.BaseDeploymentGenerator.__init__"></a>

#### `__`init`__`

```python
def __init__(service_builder: ServiceBuilder,
             build_dir: Path,
             use_tm_testnet_setup: bool = False,
             dev_mode: bool = False,
             packages_dir: Optional[Path] = None,
             open_aea_dir: Optional[Path] = None,
             open_autonomy_dir: Optional[Path] = None,
             image_author: Optional[str] = None)
```

Initialise with only kwargs.

<a id="autonomy.deploy.base.BaseDeploymentGenerator.generate"></a>

#### generate

```python
@abc.abstractmethod
def generate(image_version: Optional[str] = None,
             use_hardhat: bool = False,
             use_acn: bool = False) -> "BaseDeploymentGenerator"
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

