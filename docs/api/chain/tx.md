<a id="autonomy.chain.tx"></a>

# autonomy.chain.tx

Tx settlement helper.

<a id="autonomy.chain.tx.should_retry"></a>

#### should`_`retry

```python
def should_retry(error: str) -> bool
```

Check an error message to check if we should raise an error or retry the tx

<a id="autonomy.chain.tx.should_reprice"></a>

#### should`_`reprice

```python
def should_reprice(error: str) -> bool
```

Check an error message to check if we should reprice the transaction

<a id="autonomy.chain.tx.already_known"></a>

#### already`_`known

```python
def already_known(error: str) -> bool
```

Check if the transaction is already sent

<a id="autonomy.chain.tx.TxSettler"></a>

## TxSettler Objects

```python
class TxSettler()
```

Tx settlement helper

<a id="autonomy.chain.tx.TxSettler.__init__"></a>

#### `__`init`__`

```python
def __init__(ledger_api: LedgerApi,
             crypto: Crypto,
             chain_type: ChainType,
             tx_builder: Callable[[], Dict],
             timeout: Optional[float] = None,
             retries: Optional[int] = None,
             sleep: Optional[float] = None) -> None
```

Initialize object.

<a id="autonomy.chain.tx.TxSettler.transact"></a>

#### transact

```python
def transact(dry_run: bool = False) -> "TxSettler"
```

Make a transaction and return a receipt

<a id="autonomy.chain.tx.TxSettler.settle"></a>

#### settle

```python
def settle() -> "TxSettler"
```

Wait for the tx to be mined.

<a id="autonomy.chain.tx.TxSettler.get_events"></a>

#### get`_`events

```python
def get_events(contract: "Contract",
               event_name: str) -> tuple["EventData", ...]
```

Get events from the tx receipt.

<a id="autonomy.chain.tx.TxSettler.verify_events"></a>

#### verify`_`events

```python
def verify_events(contract: "Contract", event_name: str,
                  expected_event_arg_name: str,
                  expected_event_arg_value: Any) -> "TxSettler"
```

Verify that an event is in the tx receipt.

