<a id="autonomy.deploy.generators.kubernetes.base"></a>

# autonomy.deploy.generators.kubernetes.base

Script to create environment for benchmarking n agents.

<a id="autonomy.deploy.generators.kubernetes.base.KubernetesGenerator"></a>

## KubernetesGenerator Objects

```python
class KubernetesGenerator(BaseDeploymentGenerator)
```

Kubernetes Deployment Generator.

<a id="autonomy.deploy.generators.kubernetes.base.KubernetesGenerator.__init__"></a>

#### `__`init`__`

```python
def __init__(service_builder: ServiceBuilder,
             build_dir: Path,
             dev_mode: bool = False,
             packages_dir: Optional[Path] = None,
             open_aea_dir: Optional[Path] = None,
             open_autonomy_dir: Optional[Path] = None,
             use_tm_testnet_setup: bool = False,
             image_author: Optional[str] = None) -> None
```

Initialise the deployment generator.

<a id="autonomy.deploy.generators.kubernetes.base.KubernetesGenerator.build_agent_deployment"></a>

#### build`_`agent`_`deployment

```python
def build_agent_deployment(runtime_image: str, agent_ix: int,
                           number_of_agents: int,
                           agent_vars: Dict[str, Any]) -> str
```

Build agent deployment.

<a id="autonomy.deploy.generators.kubernetes.base.KubernetesGenerator.generate_config_tendermint"></a>

#### generate`_`config`_`tendermint

```python
def generate_config_tendermint() -> "KubernetesGenerator"
```

Build configuration job.

<a id="autonomy.deploy.generators.kubernetes.base.KubernetesGenerator.generate"></a>

#### generate

```python
def generate(image_version: Optional[str] = None,
             use_hardhat: bool = False,
             use_acn: bool = False) -> "KubernetesGenerator"
```

Generate the deployment.

<a id="autonomy.deploy.generators.kubernetes.base.KubernetesGenerator.write_config"></a>

#### write`_`config

```python
def write_config() -> "KubernetesGenerator"
```

Write output to build dir

<a id="autonomy.deploy.generators.kubernetes.base.KubernetesGenerator.populate_private_keys"></a>

#### populate`_`private`_`keys

```python
def populate_private_keys() -> "BaseDeploymentGenerator"
```

Populates private keys into a config map for the kubernetes deployment.

