<a id="autonomy.deploy.generators.localhost.tendermint.app"></a>

# autonomy.deploy.generators.localhost.tendermint.app

HTTP server to control the tendermint execution environment.

<a id="autonomy.deploy.generators.localhost.tendermint.app.load_genesis"></a>

#### load`_`genesis

```python
def load_genesis() -> Any
```

Load genesis file.

<a id="autonomy.deploy.generators.localhost.tendermint.app.get_defaults"></a>

#### get`_`defaults

```python
def get_defaults() -> Dict[str, str]
```

Get defaults from genesis file.

<a id="autonomy.deploy.generators.localhost.tendermint.app.override_config_toml"></a>

#### override`_`config`_`toml

```python
def override_config_toml() -> None
```

Update sync method.

<a id="autonomy.deploy.generators.localhost.tendermint.app.update_peers"></a>

#### update`_`peers

```python
def update_peers(validators: List[Dict], config_path: Path) -> None
```

Fix peers.

<a id="autonomy.deploy.generators.localhost.tendermint.app.update_external_address"></a>

#### update`_`external`_`address

```python
def update_external_address(external_address: str, config_path: Path) -> None
```

Update the external address.

<a id="autonomy.deploy.generators.localhost.tendermint.app.update_genesis_config"></a>

#### update`_`genesis`_`config

```python
def update_genesis_config(data: Dict) -> None
```

Update genesis.json file for the tendermint node.

<a id="autonomy.deploy.generators.localhost.tendermint.app.PeriodDumper"></a>

## PeriodDumper Objects

```python
class PeriodDumper()
```

Dumper for tendermint data.

<a id="autonomy.deploy.generators.localhost.tendermint.app.PeriodDumper.__init__"></a>

#### `__`init`__`

```python
def __init__(logger: logging.Logger, dump_dir: Optional[Path] = None) -> None
```

Initialize object.

<a id="autonomy.deploy.generators.localhost.tendermint.app.PeriodDumper.readonly_handler"></a>

#### readonly`_`handler

```python
@staticmethod
def readonly_handler(func: Callable, path: str, execinfo: Any) -> None
```

If permission is readonly, we change and retry.

<a id="autonomy.deploy.generators.localhost.tendermint.app.PeriodDumper.dump_period"></a>

#### dump`_`period

```python
def dump_period() -> None
```

Dump tendermint run data for replay

<a id="autonomy.deploy.generators.localhost.tendermint.app.create_app"></a>

#### create`_`app

```python
def create_app(dump_dir: Optional[Path] = None,
               debug: bool = False) -> Tuple[Flask, TendermintNode]
```

Create the Tendermint server app

<a id="autonomy.deploy.generators.localhost.tendermint.app.create_server"></a>

#### create`_`server

```python
def create_server() -> Any
```

Function to retrieve just the app to be used by flask entry point.

