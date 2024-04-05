<a id="autonomy.cli.helpers.chain"></a>

# autonomy.cli.helpers.chain

On-chain interaction helpers.

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
             hwi: bool = False,
             timeout: Optional[float] = None,
             retries: Optional[int] = None,
             sleep: Optional[float] = None,
             dry_run: bool = False) -> None
```

Initialize object.

<a id="autonomy.cli.helpers.chain.OnChainHelper.load_hwi_plugin"></a>

#### load`_`hwi`_`plugin

```python
@staticmethod
def load_hwi_plugin() -> Type[LedgerApi]
```

Load HWI Plugin.

<a id="autonomy.cli.helpers.chain.OnChainHelper.load_crypto"></a>

#### load`_`crypto

```python
@staticmethod
def load_crypto(file: Path, password: Optional[str] = None) -> Crypto
```

Load crypto object.

<a id="autonomy.cli.helpers.chain.OnChainHelper.get_ledger_and_crypto_objects"></a>

#### get`_`ledger`_`and`_`crypto`_`objects

```python
@classmethod
def get_ledger_and_crypto_objects(
        cls,
        chain_type: ChainType,
        key: Optional[Path] = None,
        password: Optional[str] = None,
        hwi: bool = False) -> Tuple[LedgerApi, Crypto]
```

Create ledger_api and crypto objects

<a id="autonomy.cli.helpers.chain.OnChainHelper.check_required_enviroment_variables"></a>

#### check`_`required`_`enviroment`_`variables

```python
def check_required_enviroment_variables(
        configs: Tuple[ContractConfig, ...]) -> None
```

Check for required enviroment variables when working with the custom chain.

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
             update_token: Optional[int] = None,
             timeout: Optional[float] = None,
             retries: Optional[int] = None,
             sleep: Optional[float] = None,
             subgraph: Optional[str] = None,
             dry_run: bool = False) -> None
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

<a id="autonomy.cli.helpers.chain.MintHelper.fetch_component_dependencies"></a>

#### fetch`_`component`_`dependencies

```python
def fetch_component_dependencies() -> "MintHelper"
```

Verify component dependencies.

<a id="autonomy.cli.helpers.chain.MintHelper.verify_service_dependencies"></a>

#### verify`_`service`_`dependencies

```python
def verify_service_dependencies(agent_id: int) -> "MintHelper"
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
                 threshold: Optional[int] = None,
                 token: Optional[str] = None,
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
def update_service(number_of_slots: int,
                   cost_of_bond: int,
                   threshold: Optional[int] = None,
                   token: Optional[str] = None) -> None
```

Update service

<a id="autonomy.cli.helpers.chain.ServiceHelper"></a>

## ServiceHelper Objects

```python
class ServiceHelper(OnChainHelper)
```

Service helper.

<a id="autonomy.cli.helpers.chain.ServiceHelper.__init__"></a>

#### `__`init`__`

```python
def __init__(service_id: int,
             chain_type: ChainType,
             key: Optional[Path] = None,
             password: Optional[str] = None,
             hwi: bool = False,
             timeout: Optional[float] = None,
             retries: Optional[int] = None,
             sleep: Optional[float] = None,
             dry_run: bool = False) -> None
```

Initialize object.

<a id="autonomy.cli.helpers.chain.ServiceHelper.check_is_service_token_secured"></a>

#### check`_`is`_`service`_`token`_`secured

```python
def check_is_service_token_secured(
        token: Optional[str] = None) -> "ServiceHelper"
```

Check if service

<a id="autonomy.cli.helpers.chain.ServiceHelper.approve_erc20_usage"></a>

#### approve`_`erc20`_`usage

```python
def approve_erc20_usage(amount: int, spender: str) -> "ServiceHelper"
```

Approve ERC20 usage.

<a id="autonomy.cli.helpers.chain.ServiceHelper.activate_service"></a>

#### activate`_`service

```python
def activate_service() -> None
```

Activate on-chain service

<a id="autonomy.cli.helpers.chain.ServiceHelper.register_instance"></a>

#### register`_`instance

```python
def register_instance(instances: List[str], agent_ids: List[int]) -> None
```

Register agents instances on an activated service

<a id="autonomy.cli.helpers.chain.ServiceHelper.deploy_service"></a>

#### deploy`_`service

```python
def deploy_service(reuse_multisig: bool = False,
                   fallback_handler: Optional[str] = None) -> None
```

Deploy a service with registration activated

<a id="autonomy.cli.helpers.chain.ServiceHelper.terminate_service"></a>

#### terminate`_`service

```python
def terminate_service() -> None
```

Terminate a service

<a id="autonomy.cli.helpers.chain.ServiceHelper.unbond_service"></a>

#### unbond`_`service

```python
def unbond_service() -> None
```

Unbond a service

<a id="autonomy.cli.helpers.chain.print_service_info"></a>

#### print`_`service`_`info

```python
def print_service_info(service_id: int, chain_type: ChainType) -> None
```

Print service information

