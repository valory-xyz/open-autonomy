<a id="aea_swarm.deploy.generators.docker_compose.base"></a>

# aea`_`swarm.deploy.generators.docker`_`compose.base

Docker-compose Deployment Generator.

<a id="aea_swarm.deploy.generators.docker_compose.base.build_tendermint_node_config"></a>

#### build`_`tendermint`_`node`_`config

```python
def build_tendermint_node_config(node_id: int) -> str
```

Build tendermint node config for docker compose.

<a id="aea_swarm.deploy.generators.docker_compose.base.build_abci_node_config"></a>

#### build`_`abci`_`node`_`config

```python
def build_abci_node_config(node_id: int, max_participants: int) -> str
```

Build tendermint node config for docker compose.

<a id="aea_swarm.deploy.generators.docker_compose.base.build_docker_compose_yml"></a>

#### build`_`docker`_`compose`_`yml

```python
def build_docker_compose_yml(max_participants: int) -> str
```

Build content for `docker-compose.yml`.

<a id="aea_swarm.deploy.generators.docker_compose.base.build_agent_config"></a>

#### build`_`agent`_`config

```python
def build_agent_config(node_id: int, number_of_agents: int, agent_vars: Dict) -> str
```

Build agent config.

<a id="aea_swarm.deploy.generators.docker_compose.base.DockerComposeGenerator"></a>

## DockerComposeGenerator Objects

```python
class DockerComposeGenerator(BaseDeploymentGenerator)
```

Class to automate the generation of Deployments.

<a id="aea_swarm.deploy.generators.docker_compose.base.DockerComposeGenerator.__init__"></a>

#### `__`init`__`

```python
def __init__(deployment_spec: BaseDeployment, build_dir: Path) -> None
```

Initialise the deployment generator.

<a id="aea_swarm.deploy.generators.docker_compose.base.DockerComposeGenerator.generate_config_tendermint"></a>

#### generate`_`config`_`tendermint

```python
def generate_config_tendermint(valory_application: Type[BaseDeployment]) -> str
```

Generate the command to configure tendermint testnet.

<a id="aea_swarm.deploy.generators.docker_compose.base.DockerComposeGenerator.generate"></a>

#### generate

```python
def generate(valory_application: Type[BaseDeployment]) -> str
```

Generate the new configuration.

