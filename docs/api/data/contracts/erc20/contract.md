<a id="autonomy.data.contracts.erc20.contract"></a>

# autonomy.data.contracts.erc20.contract

This module contains the scaffold contract definition.

<a id="autonomy.data.contracts.erc20.contract.ERC20TokenContract"></a>

## ERC20TokenContract Objects

```python
class ERC20TokenContract(Contract)
```

ERC20 token contract.

<a id="autonomy.data.contracts.erc20.contract.ERC20TokenContract.get_raw_transaction"></a>

#### get`_`raw`_`transaction

```python
@classmethod
def get_raw_transaction(cls, ledger_api: LedgerApi, contract_address: str,
                        **kwargs: Any) -> JSONLike
```

Handler method for the 'GET_RAW_TRANSACTION' requests.

Implement this method in the sub class if you want
to handle the contract requests manually.

**Arguments**:

- `ledger_api`: the ledger apis.
- `contract_address`: the contract address.
- `kwargs`: the keyword arguments.

**Returns**:

the tx  # noqa: DAR202

<a id="autonomy.data.contracts.erc20.contract.ERC20TokenContract.get_raw_message"></a>

#### get`_`raw`_`message

```python
@classmethod
def get_raw_message(cls, ledger_api: LedgerApi, contract_address: str,
                    **kwargs: Any) -> bytes
```

Handler method for the 'GET_RAW_MESSAGE' requests.

Implement this method in the sub class if you want
to handle the contract requests manually.

**Arguments**:

- `ledger_api`: the ledger apis.
- `contract_address`: the contract address.
- `kwargs`: the keyword arguments.

**Returns**:

the tx  # noqa: DAR202

<a id="autonomy.data.contracts.erc20.contract.ERC20TokenContract.get_state"></a>

#### get`_`state

```python
@classmethod
def get_state(cls, ledger_api: LedgerApi, contract_address: str,
              **kwargs: Any) -> JSONLike
```

Handler method for the 'GET_STATE' requests.

Implement this method in the sub class if you want
to handle the contract requests manually.

**Arguments**:

- `ledger_api`: the ledger apis.
- `contract_address`: the contract address.
- `kwargs`: the keyword arguments.

**Returns**:

the tx  # noqa: DAR202

<a id="autonomy.data.contracts.erc20.contract.ERC20TokenContract.get_approve_tx"></a>

#### get`_`approve`_`tx

```python
@classmethod
def get_approve_tx(cls, ledger_api: LedgerApi, contract_address: str,
                   spender: str, amount: int, sender: str) -> JSONLike
```

Get approve tx.

<a id="autonomy.data.contracts.erc20.contract.ERC20TokenContract.get_approval_events"></a>

#### get`_`approval`_`events

```python
@classmethod
def get_approval_events(cls, ledger_api: LedgerApi, contract_address: str,
                        tx_receipt: JSONLike) -> JSONLike
```

Get approve tx.

