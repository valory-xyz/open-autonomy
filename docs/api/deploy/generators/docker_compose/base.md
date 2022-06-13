<a id="autonomy.deploy.generators.docker_compose.base"></a>

# autonomy.deploy.generators.docker`_`compose.base

Docker-compose Deployment Generator.

<a id="autonomy.deploy.generators.docker_compose.base.build_tendermint_node_config"></a>

#### build`_`tendermint`_`node`_`config

```python
def build_tendermint_node_config(node_id: int, dev_mode: bool = False, image_version: str = TENDERMINT_IMAGE_VERSION) -> str
```

Build tendermint node config for docker compose.

<a id="autonomy.deploy.generators.docker_compose.base.build_agent_config"></a>

#### build`_`agent`_`config

```python
def build_agent_config(valory_app: str, node_id: int, number_of_agents: int, agent_vars: Dict, dev_mode: bool = False, package_dir: Path = Path.cwd().absolute() / "packages", open_aea_dir: Path = Path.cwd().absolute().parent / "open-aea", open_aea_image_name: str = OPEN_AEA_IMAGE_NAME, open_aea_image_version: str = IMAGE_VERSION) -> str
```

Build agent config.

<a id="autonomy.deploy.generators.docker_compose.base.DockerComposeGenerator"></a>

## DockerComposeGenerator Objects

```python
class DockerComposeGenerator(BaseDeploymentGenerator)
```

Class to automate the generation of Deployments.

<a id="autonomy.deploy.generators.docker_compose.base.DockerComposeGenerator.generate_config_tendermint"></a>

#### generate`_`config`_`tendermint

```python
def generate_config_tendermint(image_version: str = TENDERMINT_IMAGE_NAME) -> "DockerComposeGenerator"
```

Generate the command to configure tendermint testnet.

<a id="autonomy.deploy.generators.docker_compose.base.DockerComposeGenerator.generate"></a>

#### generate

```python
def generate(image_versions: Dict[str, str], dev_mode: bool = False) -> "DockerComposeGenerator"
```

Generate the new configuration.

<a id="autonomy.deploy.generators.docker_compose.base.DockerComposeGenerator.populate_private_keys"></a>

#### populate`_`private`_`keys

```python
def populate_private_keys() -> "DockerComposeGenerator"
```

Populate the private keys to the build directory for docker-compose mapping.

