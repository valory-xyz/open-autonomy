<a id="aea_swarm.configurations.base"></a>

# aea`_`swarm.configurations.base

Base configurations.

<a id="aea_swarm.configurations.base.Service"></a>

## Service Objects

```python
class Service(PackageConfiguration)
```

Service package configuration.

<a id="aea_swarm.configurations.base.Service.__init__"></a>

#### `__`init`__`

```python
def __init__(name: SimpleIdOrStr, author: SimpleIdOrStr, agent: PublicId, version: str = "", license_: str = "", aea_version: str = "", description: str = "", number_of_agents: int = 4, network: Optional[str] = None, build_entrypoint: Optional[str] = None) -> None
```

Initialise object.

<a id="aea_swarm.configurations.base.Service.json"></a>

#### json

```python
@property
def json() -> Dict
```

Returns an ordered Dict for service config.

<a id="aea_swarm.configurations.base.Service.from_json"></a>

#### from`_`json

```python
@classmethod
def from_json(cls, obj: Dict) -> "Service"
```

Initialize object from json.

