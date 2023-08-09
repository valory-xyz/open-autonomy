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

<a id="autonomy.cli.helpers.chain.mint_component"></a>

#### mint`_`component

```python
def mint_component(package_path: Path,
                   package_type: PackageType,
                   key: Optional[Path],
                   chain_type: ChainType,
                   dependencies: List[int],
                   nft: Optional[NFTHashOrPath] = None,
                   owner: Optional[str] = None,
                   password: Optional[str] = None,
                   skip_hash_check: bool = False,
                   skip_dependencies_check: bool = False,
                   timeout: Optional[float] = None,
                   hwi: bool = False) -> None
```

Mint component.

<a id="autonomy.cli.helpers.chain.mint_service"></a>

#### mint`_`service

```python
def mint_service(package_path: Path,
                 key: Optional[Path],
                 chain_type: ChainType,
                 agent_id: int,
                 number_of_slots: int,
                 cost_of_bond: int,
                 threshold: int,
                 nft: Optional[NFTHashOrPath] = None,
                 owner: Optional[str] = None,
                 password: Optional[str] = None,
                 skip_hash_check: bool = False,
                 skip_dependencies_check: bool = False,
                 timeout: Optional[float] = None,
                 hwi: bool = False) -> None
```

Mint service

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

