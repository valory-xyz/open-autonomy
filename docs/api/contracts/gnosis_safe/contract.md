<a id="packages.valory.contracts.gnosis_safe.contract"></a>

# packages.valory.contracts.gnosis`_`safe.contract

This module contains the class to connect to an Gnosis Safe contract.

<a id="packages.valory.contracts.gnosis_safe.contract.checksum_address"></a>

#### checksum`_`address

```python
def checksum_address(agent_address: str) -> ChecksumAddress
```

Get the checksum address.

<a id="packages.valory.contracts.gnosis_safe.contract.SafeOperation"></a>

## SafeOperation Objects

```python
class SafeOperation(Enum)
```

Operation types.

<a id="packages.valory.contracts.gnosis_safe.contract.GnosisSafeContract"></a>

## GnosisSafeContract Objects

```python
class GnosisSafeContract(Contract)
```

The Gnosis Safe contract.

<a id="packages.valory.contracts.gnosis_safe.contract.GnosisSafeContract.get_raw_transaction"></a>

#### get`_`raw`_`transaction

```python
@classmethod
def get_raw_transaction(cls, ledger_api: LedgerApi, contract_address: str,
                        **kwargs: Any) -> Optional[JSONLike]
```

Get the Safe transaction.

<a id="packages.valory.contracts.gnosis_safe.contract.GnosisSafeContract.get_raw_message"></a>

#### get`_`raw`_`message

```python
@classmethod
def get_raw_message(cls, ledger_api: LedgerApi, contract_address: str,
                    **kwargs: Any) -> Optional[bytes]
```

Get raw message.

<a id="packages.valory.contracts.gnosis_safe.contract.GnosisSafeContract.get_state"></a>

#### get`_`state

```python
@classmethod
def get_state(cls, ledger_api: LedgerApi, contract_address: str,
              **kwargs: Any) -> Optional[JSONLike]
```

Get state.

<a id="packages.valory.contracts.gnosis_safe.contract.GnosisSafeContract.get_deploy_transaction"></a>

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

<a id="packages.valory.contracts.gnosis_safe.contract.GnosisSafeContract.get_raw_safe_transaction_hash"></a>

#### get`_`raw`_`safe`_`transaction`_`hash

```python
@classmethod
def get_raw_safe_transaction_hash(cls,
                                  ledger_api: EthereumApi,
                                  contract_address: str,
                                  to_address: str,
                                  value: int,
                                  data: bytes,
                                  operation: int = SafeOperation.CALL.value,
                                  safe_tx_gas: int = 0,
                                  base_gas: int = 0,
                                  gas_price: int = 0,
                                  gas_token: str = NULL_ADDRESS,
                                  refund_receiver: str = NULL_ADDRESS,
                                  safe_nonce: Optional[int] = None,
                                  safe_version: Optional[str] = None,
                                  chain_id: Optional[int] = None) -> JSONLike
```

Get the hash of the raw Safe transaction.

Adapted from https://github.com/gnosis/gnosis-py/blob/69f1ee3263086403f6017effa0841c6a2fbba6d6/gnosis/safe/safe_tx.py#L125

Note, because safe_nonce is included in the tx_hash the agents implicitly agree on the order of txs if they agree on a tx_hash.

**Arguments**:

- `ledger_api`: the ledger API object
- `contract_address`: the contract address
- `to_address`: the tx recipient address
- `value`: the ETH value of the transaction
- `data`: the data of the transaction
- `operation`: Operation type of Safe transaction
- `safe_tx_gas`: Gas that should be used for the Safe transaction
- `base_gas`: Gas costs for that are independent of the transaction execution
(e.g. base transaction fee, signature check, payment of the refund)
- `gas_price`: Gas price that should be used for the payment calculation
- `gas_token`: Token address (or `0x000..000` if ETH) that is used for the payment
- `refund_receiver`: Address of receiver of gas payment (or `0x000..000`  if tx.origin).
- `safe_nonce`: Current nonce of the Safe. If not provided, it will be retrieved from network
- `safe_version`: Safe version 1.0.0 renamed `baseGas` to `dataGas`. Safe version 1.3.0 added `chainId` to the `domainSeparator`. If not provided, it will be retrieved from network
- `chain_id`: Ethereum network chain_id is used in hash calculation for Safes >= 1.3.0. If not provided, it will be retrieved from the provided ethereum_client

**Returns**:

the hash of the raw Safe transaction

<a id="packages.valory.contracts.gnosis_safe.contract.GnosisSafeContract.get_packed_signatures"></a>

#### get`_`packed`_`signatures

```python
@classmethod
def get_packed_signatures(cls, owners: Tuple[str],
                          signatures_by_owner: Dict[str, str]) -> bytes
```

Get the packed signatures.

<a id="packages.valory.contracts.gnosis_safe.contract.GnosisSafeContract.get_raw_safe_transaction"></a>

#### get`_`raw`_`safe`_`transaction

```python
@classmethod
def get_raw_safe_transaction(cls,
                             ledger_api: EthereumApi,
                             contract_address: str,
                             sender_address: str,
                             owners: Tuple[str],
                             to_address: str,
                             value: int,
                             data: bytes,
                             signatures_by_owner: Dict[str, str],
                             operation: int = SafeOperation.CALL.value,
                             safe_tx_gas: int = 0,
                             base_gas: int = 0,
                             safe_gas_price: int = 0,
                             gas_token: str = NULL_ADDRESS,
                             refund_receiver: str = NULL_ADDRESS,
                             gas_price: Optional[int] = None,
                             nonce: Optional[Nonce] = None,
                             max_fee_per_gas: Optional[int] = None,
                             max_priority_fee_per_gas: Optional[int] = None,
                             old_price: Optional[Dict[str, Wei]] = None,
                             fallback_gas: int = 0) -> JSONLike
```

Get the raw Safe transaction

**Arguments**:

- `ledger_api`: the ledger API object
- `contract_address`: the contract address
- `sender_address`: the address of the sender
- `owners`: the sequence of owners
- `to_address`: Destination address of Safe transaction
- `value`: Ether value of Safe transaction
- `data`: Data payload of Safe transaction
- `signatures_by_owner`: mapping from owners to signatures
- `operation`: Operation type of Safe transaction
- `safe_tx_gas`: Gas that should be used for the Safe transaction
- `base_gas`: Gas costs for that are independent of the transaction execution
(e.g. base transaction fee, signature check, payment of the refund)
- `safe_gas_price`: Gas price that should be used for the payment calculation
- `gas_token`: Token address (or `0x000..000` if ETH) that is used for the payment
- `refund_receiver`: Address of receiver of gas payment (or `0x000..000`  if tx.origin).
- `gas_price`: gas price
- `nonce`: the nonce
- `max_fee_per_gas`: max
- `max_priority_fee_per_gas`: max
- `old_price`: the old gas price params in case that we are trying to resubmit a transaction.
- `fallback_gas`: (external) gas to spend when base_gas and safe_tx_gas are zero and no gas estimation is possible.

**Returns**:

the raw Safe transaction

<a id="packages.valory.contracts.gnosis_safe.contract.GnosisSafeContract.verify_contract"></a>

#### verify`_`contract

```python
@classmethod
def verify_contract(cls, ledger_api: LedgerApi,
                    contract_address: str) -> JSONLike
```

Verify the contract's bytecode

**Arguments**:

- `ledger_api`: the ledger API object
- `contract_address`: the contract address

**Returns**:

the verified status

<a id="packages.valory.contracts.gnosis_safe.contract.GnosisSafeContract.verify_tx"></a>

#### verify`_`tx

```python
@classmethod
def verify_tx(cls,
              ledger_api: EthereumApi,
              contract_address: str,
              tx_hash: str,
              owners: Tuple[str],
              to_address: str,
              value: int,
              data: bytes,
              signatures_by_owner: Dict[str, str],
              operation: int = SafeOperation.CALL.value,
              safe_tx_gas: int = 0,
              base_gas: int = 0,
              gas_price: int = 0,
              gas_token: str = NULL_ADDRESS,
              refund_receiver: str = NULL_ADDRESS,
              safe_version: Optional[str] = None) -> JSONLike
```

Verify a tx hash exists on the blockchain.

Currently, the implementation is an overkill as most of the verification is implicit by the acceptance of the transaction in the Safe.

**Arguments**:

- `ledger_api`: the ledger API object
- `contract_address`: the contract address
- `tx_hash`: the transaction hash
- `owners`: the sequence of owners
- `to_address`: Destination address of Safe transaction
- `value`: Ether value of Safe transaction
- `data`: Data payload of Safe transaction
- `signatures_by_owner`: mapping from owners to signatures
- `operation`: Operation type of Safe transaction
- `safe_tx_gas`: Gas that should be used for the Safe transaction
- `base_gas`: Gas costs for that are independent of the transaction execution
(e.g. base transaction fee, signature check, payment of the refund)
- `gas_price`: Gas price that should be used for the payment calculation
- `gas_token`: Token address (or `0x000..000` if ETH) that is used for the payment
- `refund_receiver`: Address of receiver of gas payment (or `0x000..000`  if tx.origin).
- `safe_version`: Safe version 1.0.0 renamed `baseGas` to `dataGas`. Safe version 1.3.0 added `chainId` to the `domainSeparator`. If not provided, it will be retrieved from network

**Returns**:

the verified status

<a id="packages.valory.contracts.gnosis_safe.contract.GnosisSafeContract.revert_reason"></a>

#### revert`_`reason

```python
@classmethod
def revert_reason(cls, ledger_api: EthereumApi, contract_address: str,
                  tx: TxData) -> JSONLike
```

Check the revert reason of a transaction.

**Arguments**:

- `ledger_api`: the ledger API object.
- `contract_address`: the contract address
- `tx`: the transaction for which we want to get the revert reason.

**Returns**:

the revert reason message.

<a id="packages.valory.contracts.gnosis_safe.contract.GnosisSafeContract.get_safe_nonce"></a>

#### get`_`safe`_`nonce

```python
@classmethod
def get_safe_nonce(cls, ledger_api: EthereumApi,
                   contract_address: str) -> JSONLike
```

Retrieve the safe's nonce

**Arguments**:

- `ledger_api`: the ledger API object
- `contract_address`: the contract address

**Returns**:

the safe nonce

<a id="packages.valory.contracts.gnosis_safe.contract.GnosisSafeContract.get_ingoing_transfers"></a>

#### get`_`ingoing`_`transfers

```python
@classmethod
def get_ingoing_transfers(cls,
                          ledger_api: EthereumApi,
                          contract_address: str,
                          from_block: Optional[str] = None,
                          to_block: Optional[str] = "latest") -> JSONLike
```

A list of transfers into the contract.

**Arguments**:

- `ledger_api`: the ledger API object
- `contract_address`: the contract address,
- `from_block`: from which block to start tje search
- `to_block`: at which block to end the search

**Returns**:

list of transfers

<a id="packages.valory.contracts.gnosis_safe.contract.GnosisSafeContract.get_balance"></a>

#### get`_`balance

```python
@classmethod
def get_balance(cls, ledger_api: EthereumApi,
                contract_address: str) -> JSONLike
```

Retrieve the safe's balance

**Arguments**:

- `ledger_api`: the ledger API object
- `contract_address`: the contract address

**Returns**:

the safe balance (in wei)

<a id="packages.valory.contracts.gnosis_safe.contract.GnosisSafeContract.get_amount_spent"></a>

#### get`_`amount`_`spent

```python
@classmethod
def get_amount_spent(cls, ledger_api: EthereumApi, contract_address: str,
                     tx_hash: str) -> JSONLike
```

Get the amount of ether spent in a tx.

**Arguments**:

- `ledger_api`: the ledger API object
- `contract_address`: the contract address (not used)
- `tx_hash`: the settled tx hash

**Returns**:

the safe balance (in wei)

<a id="packages.valory.contracts.gnosis_safe.contract.GnosisSafeContract.get_safe_txs"></a>

#### get`_`safe`_`txs

```python
@classmethod
def get_safe_txs(cls,
                 ledger_api: EthereumApi,
                 contract_address: str,
                 from_block: BlockIdentifier = "earliest",
                 to_block: BlockIdentifier = "latest") -> JSONLike
```

Get all the safe tx hashes.

**Arguments**:

- `ledger_api`: the ledger API object
- `contract_address`: the contract address (not used)
- `from_block`: from which block to search for events
- `to_block`: to which block to search for events
:return: the safe txs

<a id="packages.valory.contracts.gnosis_safe.contract.GnosisSafeContract.get_removed_owner_events"></a>

#### get`_`removed`_`owner`_`events

```python
@classmethod
def get_removed_owner_events(cls,
                             ledger_api: EthereumApi,
                             contract_address: str,
                             removed_owner: Optional[str] = None,
                             from_block: BlockIdentifier = "earliest",
                             to_block: BlockIdentifier = "latest") -> JSONLike
```

Get all RemovedOwner events for a safe contract.

**Arguments**:

- `ledger_api`: the ledger API object
- `contract_address`: the contract address
- `removed_owner`: the owner to check for, any owner qualifies if not provided.
- `from_block`: from which block to search for events
- `to_block`: to which block to search for events

**Returns**:

the added owner events

<a id="packages.valory.contracts.gnosis_safe.contract.GnosisSafeContract.get_zero_transfer_events"></a>

#### get`_`zero`_`transfer`_`events

```python
@classmethod
def get_zero_transfer_events(cls,
                             ledger_api: EthereumApi,
                             contract_address: str,
                             sender_address: str,
                             from_block: BlockIdentifier = "earliest",
                             to_block: BlockIdentifier = "latest") -> JSONLike
```

Get all zero transfer events from a given sender to the safe address.

**Arguments**:

- `ledger_api`: the ledger API object
- `contract_address`: the contract address
- `sender_address`: the owner of the service, ie the address that triggers termination
- `from_block`: from which block to search for events
- `to_block`: to which block to search for events
:return: the zero transfer events

<a id="packages.valory.contracts.gnosis_safe.contract.GnosisSafeContract.get_remove_owner_data"></a>

#### get`_`remove`_`owner`_`data

```python
@classmethod
def get_remove_owner_data(cls, ledger_api: EthereumApi, contract_address: str,
                          owner: str, threshold: int) -> JSONLike
```

Get a removeOwner() encoded tx.

This method acts as a wrapper for `removeOwner()`
https://github.com/safe-global/safe-contracts/blob/v1.3.0/contracts/base/OwnerManager.sol#L70

**Arguments**:

- `ledger_api`: the ledger API object
- `contract_address`: the contract address
- `owner`: the owner to be removed
- `threshold`: the new safe threshold to be set

**Returns**:

the zero transfer events

<a id="packages.valory.contracts.gnosis_safe.contract.GnosisSafeContract.get_swap_owner_data"></a>

#### get`_`swap`_`owner`_`data

```python
@classmethod
def get_swap_owner_data(cls, ledger_api: EthereumApi, contract_address: str,
                        old_owner: str, new_owner: str) -> JSONLike
```

Get a swapOwner() encoded tx.

This method acts as a wrapper for `swapOwner()`
https://github.com/safe-global/safe-contracts/blob/v1.3.0/contracts/base/OwnerManager.sol#L94

**Arguments**:

- `ledger_api`: the ledger API object
- `contract_address`: the contract address
- `old_owner`: the owner to be replaced
- `new_owner`: owner to replace old_owner

**Returns**:

the zero transfer events

<a id="packages.valory.contracts.gnosis_safe.contract.GnosisSafeContract.get_owners"></a>

#### get`_`owners

```python
@classmethod
def get_owners(cls, ledger_api: EthereumApi,
               contract_address: str) -> JSONLike
```

Get the safe owners.

**Arguments**:

- `ledger_api`: the ledger API object
- `contract_address`: the contract address

**Returns**:

the safe owners

<a id="packages.valory.contracts.gnosis_safe.contract.GnosisSafeContract.get_approve_hash_tx"></a>

#### get`_`approve`_`hash`_`tx

```python
@classmethod
def get_approve_hash_tx(cls, ledger_api: EthereumApi, contract_address: str,
                        tx_hash: str, sender: str) -> JSONLike
```

Get approve has tx.

