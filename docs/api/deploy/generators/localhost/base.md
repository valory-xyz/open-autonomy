<a id="autonomy.deploy.generators.localhost.base"></a>

# autonomy.deploy.generators.localhost.base

Localhost Deployment Generator.

<a id="autonomy.deploy.generators.localhost.base.HostDeploymentGenerator"></a>

## HostDeploymentGenerator Objects

```python
class HostDeploymentGenerator(BaseDeploymentGenerator)
```

Localhost deployment.

<a id="autonomy.deploy.generators.localhost.base.HostDeploymentGenerator.agent_dir"></a>

#### agent`_`dir

```python
@property
def agent_dir() -> Path
```

Path to the agent directory.

<a id="autonomy.deploy.generators.localhost.base.HostDeploymentGenerator.generate_config_tendermint"></a>

#### generate`_`config`_`tendermint

```python
def generate_config_tendermint() -> "HostDeploymentGenerator"
```

Generate tendermint configuration.

<a id="autonomy.deploy.generators.localhost.base.HostDeploymentGenerator.generate"></a>

#### generate

```python
def generate(image_version: t.Optional[str] = None,
             use_hardhat: bool = False,
             use_acn: bool = False) -> "HostDeploymentGenerator"
```

Generate agent and tendermint configurations

<a id="autonomy.deploy.generators.localhost.base.HostDeploymentGenerator.populate_private_keys"></a>

#### populate`_`private`_`keys

```python
def populate_private_keys() -> "HostDeploymentGenerator"
```

Populate the private keys to the build directory for host mapping.

<a id="autonomy.deploy.generators.localhost.base.HostDeploymentGenerator.write_config"></a>

#### write`_`config

```python
def write_config() -> "BaseDeploymentGenerator"
```

Write output to build dir

