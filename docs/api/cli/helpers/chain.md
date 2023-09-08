<a id="autonomy.cli.helpers.chain"></a>

# autonomy.cli.helpers.chain

On-chain interaction helpers.

<a id="autonomy.cli.helpers.chain.get_ledger_and_crypto_objects"></a>

#### get`_`ledger`_`and`_`crypto`_`objects

```python
def get_ledger_and_crypto_objects(
        chain_type: ChainType,
        key: Optional[Path] = None,
        password: Optional[str] = None,
        hwi: bool = False) -> Tuple[LedgerApi, Crypto]
```

Create ledger_api and crypto objects

<a id="autonomy.cli.helpers.chain.activate_service"></a>

#### activate`_`service

```python
def activate_service(service_id: int,
                     key: Path,
                     chain_type: ChainType,
                     password: Optional[str] = None,
                     timeout: Optional[float] = None,
                     hwi: bool = False) -> None
```

Activate on-chain service

<a id="autonomy.cli.helpers.chain.register_instance"></a>

#### register`_`instance

```python
def register_instance(service_id: int,
                      instances: List[str],
                      agent_ids: List[int],
                      key: Path,
                      chain_type: ChainType,
                      password: Optional[str] = None,
                      timeout: Optional[float] = None,
                      hwi: bool = False) -> None
```

Register agents instances on an activated service

<a id="autonomy.cli.helpers.chain.deploy_service"></a>

#### deploy`_`service

```python
def deploy_service(service_id: int,
                   key: Path,
                   chain_type: ChainType,
                   deployment_payload: Optional[str] = None,
                   password: Optional[str] = None,
                   timeout: Optional[float] = None,
                   hwi: bool = False) -> None
```

Deploy a service with registration activated

<a id="autonomy.cli.helpers.chain.terminate_service"></a>

#### terminate`_`service

```python
def terminate_service(service_id: int,
                      key: Path,
                      chain_type: ChainType,
                      password: Optional[str] = None,
                      hwi: bool = False) -> None
```

Terminate a service

<a id="autonomy.cli.helpers.chain.unbond_service"></a>

#### unbond`_`service

```python
def unbond_service(service_id: int,
                   key: Path,
                   chain_type: ChainType,
                   password: Optional[str] = None,
                   hwi: bool = False) -> None
```

Terminate a service

<a id="autonomy.cli.helpers.chain.print_service_info"></a>

#### print`_`service`_`info

```python
def print_service_info(service_id: int, chain_type: ChainType) -> None
```

Terminate a service

<a id="autonomy.cli.helpers.chain.OnChainHelper"></a>

## OnChainHelper Objects

```python
class OnChainHelper()
```

On-chain interaction helper.

<a id="autonomy.cli.helpers.chain.OnChainHelper.__init__"></a>

#### `__`init`__`

```python
def __init__(chain_type: ChainType,
             key: Optional[Path] = None,
             password: Optional[str] = None,
             hwi: bool = False) -> None
```

Initialize object.

<a id="autonomy.cli.helpers.chain.OnChainHelper.get_ledger_and_crypto_objects"></a>

#### get`_`ledger`_`and`_`crypto`_`objects

```python
@staticmethod
def get_ledger_and_crypto_objects(
        chain_type: ChainType,
        key: Optional[Path] = None,
        password: Optional[str] = None,
        hwi: bool = False) -> Tuple[LedgerApi, Crypto]
```

Create ledger_api and crypto objects

<a id="autonomy.cli.helpers.chain.MintHelper"></a>

## MintHelper Objects

```python
class MintHelper(OnChainHelper)
```

Mint helper.

<a id="autonomy.cli.helpers.chain.MintHelper.__init__"></a>

#### `__`init`__`

```python
def __init__(chain_type: ChainType,
             key: Optional[Path] = None,
             password: Optional[str] = None,
             hwi: bool = False,
             update_token: Optional[int] = None) -> None
```

Initialize object.

<a id="autonomy.cli.helpers.chain.MintHelper.load_package_configuration"></a>

#### load`_`package`_`configuration

```python
def load_package_configuration(package_path: Path,
                               package_type: PackageType) -> "MintHelper"
```

Load package configuration.

<a id="autonomy.cli.helpers.chain.MintHelper.load_metadata"></a>

#### load`_`metadata

```python
def load_metadata() -> "MintHelper"
```

Load metadata when updating a mint.

<a id="autonomy.cli.helpers.chain.MintHelper.verify_nft"></a>

#### verify`_`nft

```python
def verify_nft(nft: Optional[NFTHashOrPath] = None) -> "MintHelper"
```

Verify NFT image.

<a id="autonomy.cli.helpers.chain.MintHelper.verify_component_dependencies"></a>

#### verify`_`component`_`dependencies

```python
def verify_component_dependencies(
        dependencies: Tuple[str],
        skip_dependencies_check: bool = False,
        skip_hash_check: bool = False) -> "MintHelper"
```

Verify component dependencies.

<a id="autonomy.cli.helpers.chain.MintHelper.verify_service_dependencies"></a>

#### verify`_`service`_`dependencies

```python
def verify_service_dependencies(agent_id: int,
                                skip_dependencies_check: bool = False,
                                skip_hash_check: bool = False) -> "MintHelper"
```

Verify component dependencies.

<a id="autonomy.cli.helpers.chain.MintHelper.publish_metadata"></a>

#### publish`_`metadata

```python
def publish_metadata() -> "MintHelper"
```

Publish metadata.

<a id="autonomy.cli.helpers.chain.MintHelper.mint_component"></a>

#### mint`_`component

```python
def mint_component(owner: Optional[str] = None,
                   component_type: UnitType = UnitType.COMPONENT) -> None
```

Mint component.

<a id="autonomy.cli.helpers.chain.MintHelper.mint_agent"></a>

#### mint`_`agent

```python
def mint_agent(owner: Optional[str] = None) -> None
```

Mint agent.

<a id="autonomy.cli.helpers.chain.MintHelper.mint_service"></a>

#### mint`_`service

```python
def mint_service(number_of_slots: int,
                 cost_of_bond: int,
                 threshold: int,
                 owner: Optional[str] = None) -> None
```

Mint service

<a id="autonomy.cli.helpers.chain.MintHelper.update_component"></a>

#### update`_`component

```python
def update_component(component_type: UnitType = UnitType.COMPONENT) -> None
```

Update component.

<a id="autonomy.cli.helpers.chain.MintHelper.update_agent"></a>

#### update`_`agent

```python
def update_agent() -> None
```

Update agent.

<a id="autonomy.cli.helpers.chain.MintHelper.update_service"></a>

#### update`_`service

```python
def update_service(number_of_slots: int, cost_of_bond: int,
                   threshold: int) -> None
```

Update service

