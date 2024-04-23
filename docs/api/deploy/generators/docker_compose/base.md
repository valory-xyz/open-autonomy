<a id="autonomy.deploy.generators.docker_compose.base"></a>

# autonomy.deploy.generators.docker`_`compose.base

Docker-compose Deployment Generator.

<a id="autonomy.deploy.generators.docker_compose.base.get_docker_client"></a>

#### get`_`docker`_`client

```python
def get_docker_client() -> DockerClient
```

Load docker client.

<a id="autonomy.deploy.generators.docker_compose.base.build_tendermint_node_config"></a>

#### build`_`tendermint`_`node`_`config

```python
def build_tendermint_node_config(
        node_id: int,
        container_name: str,
        abci_node: str,
        network_name: str,
        network_address: str,
        dev_mode: bool = False,
        log_level: str = INFO,
        tendermint_ports: Optional[Dict[int, int]] = None) -> str
```

Build tendermint node config for docker compose.

<a id="autonomy.deploy.generators.docker_compose.base.build_agent_config"></a>

#### build`_`agent`_`config

```python
def build_agent_config(node_id: int,
                       container_name: str,
                       agent_vars: Dict,
                       runtime_image: str,
                       network_name: str,
                       network_address: str,
                       dev_mode: bool = False,
                       package_dir: Optional[Path] = None,
                       open_aea_dir: Optional[Path] = None,
                       agent_ports: Optional[Dict[int, int]] = None,
                       extra_volumes: Optional[Dict[str, str]] = None,
                       resources: Optional[Resources] = None) -> str
```

Build agent config.

<a id="autonomy.deploy.generators.docker_compose.base.Network"></a>

## Network Objects

```python
class Network()
```

Class to represent network of the service.

<a id="autonomy.deploy.generators.docker_compose.base.Network.__init__"></a>

#### `__`init`__`

```python
def __init__(name: str, base: ipaddress.IPv4Network = BASE_SUBNET) -> None
```

Initialize.

<a id="autonomy.deploy.generators.docker_compose.base.Network.next_subnet"></a>

#### next`_`subnet

```python
@staticmethod
def next_subnet(subnet: ipaddress.IPv4Network) -> ipaddress.IPv4Network
```

Calculat next available subnet.

<a id="autonomy.deploy.generators.docker_compose.base.Network.build"></a>

#### build

```python
def build() -> ipaddress.IPv4Network
```

Initialize network params.

<a id="autonomy.deploy.generators.docker_compose.base.Network.next_address"></a>

#### next`_`address

```python
@property
def next_address() -> str
```

Returns the next IP address string.

<a id="autonomy.deploy.generators.docker_compose.base.DockerComposeGenerator"></a>

## DockerComposeGenerator Objects

```python
class DockerComposeGenerator(BaseDeploymentGenerator)
```

Class to automate the generation of Deployments.

<a id="autonomy.deploy.generators.docker_compose.base.DockerComposeGenerator.generate_config_tendermint"></a>

#### generate`_`config`_`tendermint

```python
def generate_config_tendermint() -> "DockerComposeGenerator"
```

Generate the command to configure tendermint testnet.

<a id="autonomy.deploy.generators.docker_compose.base.DockerComposeGenerator.generate"></a>

#### generate

```python
def generate(image_version: Optional[str] = None,
             use_hardhat: bool = False,
             use_acn: bool = False) -> "DockerComposeGenerator"
```

Generate the new configuration.

<a id="autonomy.deploy.generators.docker_compose.base.DockerComposeGenerator.populate_private_keys"></a>

#### populate`_`private`_`keys

```python
def populate_private_keys() -> "DockerComposeGenerator"
```

Populate the private keys to the build directory for docker-compose mapping.

