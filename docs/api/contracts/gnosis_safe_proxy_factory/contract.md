<a id="packages.valory.contracts.gnosis_safe_proxy_factory.contract"></a>

# packages.valory.contracts.gnosis`_`safe`_`proxy`_`factory.contract

This module contains the class to connect to an Gnosis Safe Proxy Factory contract.

<a id="packages.valory.contracts.gnosis_safe_proxy_factory.contract.GnosisSafeProxyFactoryContract"></a>

## GnosisSafeProxyFactoryContract Objects

```python
class GnosisSafeProxyFactoryContract(Contract)
```

The Gnosis Safe Proxy Factory contract.

<a id="packages.valory.contracts.gnosis_safe_proxy_factory.contract.GnosisSafeProxyFactoryContract.get_raw_transaction"></a>

#### get`_`raw`_`transaction

```python
@classmethod
def get_raw_transaction(cls, ledger_api: LedgerApi, contract_address: str,
                        **kwargs: Any) -> Optional[JSONLike]
```

Get the raw transaction.

<a id="packages.valory.contracts.gnosis_safe_proxy_factory.contract.GnosisSafeProxyFactoryContract.get_raw_message"></a>

#### get`_`raw`_`message

```python
@classmethod
def get_raw_message(cls, ledger_api: LedgerApi, contract_address: str,
                    **kwargs: Any) -> Optional[bytes]
```

Get raw message.

<a id="packages.valory.contracts.gnosis_safe_proxy_factory.contract.GnosisSafeProxyFactoryContract.get_state"></a>

#### get`_`state

```python
@classmethod
def get_state(cls, ledger_api: LedgerApi, contract_address: str,
              **kwargs: Any) -> Optional[JSONLike]
```

Get state.

<a id="packages.valory.contracts.gnosis_safe_proxy_factory.contract.GnosisSafeProxyFactoryContract.get_deploy_transaction"></a>

#### get`_`deploy`_`transaction

```python
@classmethod
def get_deploy_transaction(cls, ledger_api: LedgerApi, deployer_address: str,
                           **kwargs: Any) -> Optional[JSONLike]
```

Get deploy transaction.

**Arguments**:

- `ledger_api`: ledger API object.
- `deployer_address`: the deployer address.
- `kwargs`: the keyword arguments.

**Returns**:

an optional JSON-like object.

<a id="packages.valory.contracts.gnosis_safe_proxy_factory.contract.GnosisSafeProxyFactoryContract.build_tx_deploy_proxy_contract_with_nonce"></a>

#### build`_`tx`_`deploy`_`proxy`_`contract`_`with`_`nonce

```python
@classmethod
def build_tx_deploy_proxy_contract_with_nonce(
        cls,
        ledger_api: EthereumApi,
        proxy_factory_address: str,
        master_copy: str,
        address: str,
        initializer: bytes,
        salt_nonce: int,
        gas: int = MIN_GAS,
        gas_price: Optional[int] = None,
        max_fee_per_gas: Optional[int] = None,
        max_priority_fee_per_gas: Optional[int] = None,
        nonce: Optional[int] = None) -> Tuple[TxParams, str]
```

Deploy proxy contract via Proxy Factory using `createProxyWithNonce` (create2)

**Arguments**:

- `ledger_api`: ledger API object
- `proxy_factory_address`: the address of the proxy factory
- `address`: Ethereum address
- `master_copy`: Address the proxy will point at
- `initializer`: Data for safe creation
- `salt_nonce`: Uint256 for `create2` salt
- `gas`: Gas
- `gas_price`: Gas Price
- `max_fee_per_gas`: max
- `max_priority_fee_per_gas`: max
- `nonce`: Nonce

**Returns**:

Tuple(tx-hash, tx, deployed contract address)

<a id="packages.valory.contracts.gnosis_safe_proxy_factory.contract.GnosisSafeProxyFactoryContract.verify_contract"></a>

#### verify`_`contract

```python
@classmethod
def verify_contract(cls, ledger_api: EthereumApi,
                    contract_address: str) -> JSONLike
```

Verify the contract's bytecode

**Arguments**:

- `ledger_api`: the ledger API object
- `contract_address`: the contract address

**Returns**:

the verified status

