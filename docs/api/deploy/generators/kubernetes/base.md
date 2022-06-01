<a id="aea_swarm.deploy.generators.kubernetes.base"></a>

# aea`_`swarm.deploy.generators.kubernetes.base

Script to create environment for benchmarking n agents.

<a id="aea_swarm.deploy.generators.kubernetes.base.KubernetesGenerator"></a>

## KubernetesGenerator Objects

```python
class KubernetesGenerator(BaseDeploymentGenerator)
```

Kubernetes Deployment Generator.

<a id="aea_swarm.deploy.generators.kubernetes.base.KubernetesGenerator.__init__"></a>

#### `__`init`__`

```python
def __init__(deployment_spec: DeploymentSpec, build_dir: Path) -> None
```

Initialise the deployment generator.

<a id="aea_swarm.deploy.generators.kubernetes.base.KubernetesGenerator.build_agent_deployment"></a>

#### build`_`agent`_`deployment

```python
def build_agent_deployment(image_name: str, agent_ix: int, number_of_agents: int, agent_vars: Dict[str, Any]) -> str
```

Build agent deployment.

<a id="aea_swarm.deploy.generators.kubernetes.base.KubernetesGenerator.generate_config_tendermint"></a>

#### generate`_`config`_`tendermint

```python
def generate_config_tendermint() -> "KubernetesGenerator"
```

Build configuration job.

<a id="aea_swarm.deploy.generators.kubernetes.base.KubernetesGenerator.generate"></a>

#### generate

```python
def generate(dev_mode: bool = False) -> "KubernetesGenerator"
```

Generate the deployment.

<a id="aea_swarm.deploy.generators.kubernetes.base.KubernetesGenerator.write_config"></a>

#### write`_`config

```python
def write_config() -> "KubernetesGenerator"
```

Write output to build dir

<a id="aea_swarm.deploy.generators.kubernetes.base.KubernetesGenerator.populate_private_keys"></a>

#### populate`_`private`_`keys

```python
def populate_private_keys() -> "BaseDeploymentGenerator"
```

Populates private keys into a config map for the kubernetes deployment.

