<a id="autonomy.data.contracts.multisend.contract"></a>

# autonomy.data.contracts.multisend.contract

This module contains the class to connect to an Gnosis Safe contract.

<a id="autonomy.data.contracts.multisend.contract.MultiSendOperation"></a>

## MultiSendOperation Objects

```python
class MultiSendOperation(Enum)
```

Operation types.

<a id="autonomy.data.contracts.multisend.contract.encode_data"></a>

#### encode`_`data

```python
def encode_data(tx: Dict) -> bytes
```

Encodes multisend transaction.

<a id="autonomy.data.contracts.multisend.contract.decode_data"></a>

#### decode`_`data

```python
def decode_data(encoded_tx: bytes) -> Tuple[Dict, int]
```

Decodes multisend transaction.

<a id="autonomy.data.contracts.multisend.contract.to_bytes"></a>

#### to`_`bytes

```python
def to_bytes(multi_send_txs: List[Dict]) -> bytes
```

Multi send tx list to bytes.

<a id="autonomy.data.contracts.multisend.contract.from_bytes"></a>

#### from`_`bytes

```python
def from_bytes(encoded_multisend_txs: bytes) -> List[Dict]
```

Encoded multi send tx to list.

<a id="autonomy.data.contracts.multisend.contract.MultiSendContract"></a>

## MultiSendContract Objects

```python
class MultiSendContract(Contract)
```

The MultiSend contract.

<a id="autonomy.data.contracts.multisend.contract.MultiSendContract.get_raw_transaction"></a>

#### get`_`raw`_`transaction

```python
@classmethod
def get_raw_transaction(cls, ledger_api: LedgerApi, contract_address: str,
                        **kwargs: Any) -> Optional[JSONLike]
```

Get the Safe transaction.

<a id="autonomy.data.contracts.multisend.contract.MultiSendContract.get_raw_message"></a>

#### get`_`raw`_`message

```python
@classmethod
def get_raw_message(cls, ledger_api: LedgerApi, contract_address: str,
                    **kwargs: Any) -> Optional[bytes]
```

Get raw message.

<a id="autonomy.data.contracts.multisend.contract.MultiSendContract.get_state"></a>

#### get`_`state

```python
@classmethod
def get_state(cls, ledger_api: LedgerApi, contract_address: str,
              **kwargs: Any) -> Optional[JSONLike]
```

Get state.

<a id="autonomy.data.contracts.multisend.contract.MultiSendContract.get_deploy_transaction"></a>

#### get`_`deploy`_`transaction

```python
@classmethod
def get_deploy_transaction(cls, ledger_api: LedgerApi, deployer_address: str,
                           **kwargs: Any) -> Optional[JSONLike]
```

Get deploy transaction.

<a id="autonomy.data.contracts.multisend.contract.MultiSendContract.get_tx_data"></a>

#### get`_`tx`_`data

```python
@classmethod
def get_tx_data(cls, ledger_api: LedgerApi, contract_address: str,
                multi_send_txs: List[Dict]) -> Optional[JSONLike]
```

Get a multisend transaction data from list.

**Arguments**:

- `ledger_api`: ledger API object.
- `contract_address`: the contract address.
- `multi_send_txs`: the multisend transaction list.

**Returns**:

an optional JSON-like object.

<a id="autonomy.data.contracts.multisend.contract.MultiSendContract.get_multisend_tx"></a>

#### get`_`multisend`_`tx

```python
@classmethod
def get_multisend_tx(cls, ledger_api: LedgerApi, contract_address: str,
                     txs: List[Dict]) -> Optional[JSONLike]
```

Get a multisend transaction data from list.

**Arguments**:

- `ledger_api`: ledger API object.
- `contract_address`: the contract address.
- `txs`: the multisend transaction list.

**Returns**:

an optional JSON-like object.

<a id="autonomy.data.contracts.multisend.contract.MultiSendContract.get_tx_list"></a>

#### get`_`tx`_`list

```python
@classmethod
def get_tx_list(cls, ledger_api: LedgerApi, contract_address: str,
                multi_send_data: str) -> Optional[JSONLike]
```

Get a multisend transaction list from encoded data.

**Arguments**:

- `ledger_api`: ledger API object.
- `contract_address`: the contract address.
- `multi_send_data`: the multisend transaction data.

**Returns**:

an optional JSON-like object.

