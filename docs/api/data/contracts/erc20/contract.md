<a id="autonomy.data.contracts.erc20.contract"></a>

# autonomy.data.contracts.erc20.contract

This module contains the ERC20 contract definition.

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
def get_approve_tx(cls,
                   ledger_api: LedgerApi,
                   contract_address: str,
                   spender: str,
                   amount: int,
                   sender: str,
                   raise_on_try: bool = False) -> JSONLike
```

Get approve tx.

<a id="autonomy.data.contracts.erc20.contract.ERC20TokenContract.get_events"></a>

#### get`_`events

```python
@classmethod
def get_events(cls, ledger_api: LedgerApi, contract_address: str, event: str,
               receipt: JSONLike) -> JSONLike
```

Process receipt for events.

<a id="autonomy.data.contracts.erc20.contract.ERC20TokenContract.check_balance"></a>

#### check`_`balance

```python
@classmethod
def check_balance(cls, ledger_api: EthereumApi, contract_address: str,
                  account: str) -> JSONLike
```

Check the balance of the given account.

<a id="autonomy.data.contracts.erc20.contract.ERC20TokenContract.get_allowance"></a>

#### get`_`allowance

```python
@classmethod
def get_allowance(cls, ledger_api: EthereumApi, contract_address: str,
                  owner: str, spender: str) -> JSONLike
```

Check the balance of the given account.

<a id="autonomy.data.contracts.erc20.contract.ERC20TokenContract.build_deposit_tx"></a>

#### build`_`deposit`_`tx

```python
@classmethod
def build_deposit_tx(cls, ledger_api: EthereumApi,
                     contract_address: str) -> Dict[str, bytes]
```

Build a deposit transaction.

<a id="autonomy.data.contracts.erc20.contract.ERC20TokenContract.build_withdraw_tx"></a>

#### build`_`withdraw`_`tx

```python
@classmethod
def build_withdraw_tx(cls, ledger_api: EthereumApi, contract_address: str,
                      amount: int) -> Dict[str, bytes]
```

Build a deposit transaction.

<a id="autonomy.data.contracts.erc20.contract.ERC20TokenContract.build_approval_tx"></a>

#### build`_`approval`_`tx

```python
@classmethod
def build_approval_tx(cls, ledger_api: LedgerApi, contract_address: str,
                      spender: str, amount: int) -> Dict[str, bytes]
```

Build an ERC20 approval.

<a id="autonomy.data.contracts.erc20.contract.ERC20TokenContract.get_transfer_tx_data"></a>

#### get`_`transfer`_`tx`_`data

```python
@classmethod
def get_transfer_tx_data(cls, ledger_api: LedgerApi, contract_address: str,
                         receiver: str, amount: int) -> JSONLike
```

Returns the transaction to transfer tokens.

<a id="autonomy.data.contracts.erc20.contract.ERC20TokenContract.get_token_symbol"></a>

#### get`_`token`_`symbol

```python
@classmethod
def get_token_symbol(cls, ledger_api: EthereumApi,
                     contract_address: str) -> JSONLike
```

Check the balance of the given account.

<a id="autonomy.data.contracts.erc20.contract.ERC20TokenContract.get_total_supply"></a>

#### get`_`total`_`supply

```python
@classmethod
def get_total_supply(cls, ledger_api: EthereumApi,
                     contract_address: str) -> JSONLike
```

Get the total supply.

<a id="autonomy.data.contracts.erc20.contract.ERC20TokenContract.get_name"></a>

#### get`_`name

```python
@classmethod
def get_name(cls, ledger_api: EthereumApi, contract_address: str) -> JSONLike
```

Get the total supply.

<a id="autonomy.data.contracts.erc20.contract.ERC20TokenContract.get_token_decimals"></a>

#### get`_`token`_`decimals

```python
@classmethod
def get_token_decimals(cls, ledger_api: EthereumApi,
                       contract_address: str) -> JSONLike
```

Get the token decimals.

<a id="autonomy.data.contracts.erc20.contract.ERC20TokenContract.build_transfer_tx"></a>

#### build`_`transfer`_`tx

```python
@classmethod
def build_transfer_tx(cls, ledger_api: LedgerApi, contract_address: str,
                      to_address: str, amount: int) -> Dict[str, bytes]
```

Build an ERC20 transfer transaction.

