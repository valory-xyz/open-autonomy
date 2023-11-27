<a id="autonomy.chain.tx"></a>

# autonomy.chain.tx

Tx settlement helper.

<a id="autonomy.chain.tx.should_retry"></a>

#### should`_`retry

```python
def should_retry(error: str) -> bool
```

Check an error message to check if we should raise an error or retry the tx

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
             timeout: Optional[float] = None,
             retries: Optional[int] = None,
             sleep: Optional[float] = None) -> None
```

Initialize object.

<a id="autonomy.chain.tx.TxSettler.wait"></a>

#### wait

```python
def wait(waitable: Callable) -> Any
```

Wait for a chain interaction.

<a id="autonomy.chain.tx.TxSettler.build"></a>

#### build

```python
def build(method: Callable[[], Dict], contract: str, kwargs: Dict) -> Dict
```

Build transaction.

<a id="autonomy.chain.tx.TxSettler.transact"></a>

#### transact

```python
def transact(tx: Dict) -> Dict
```

Make a transaction and return a receipt

<a id="autonomy.chain.tx.TxSettler.process"></a>

#### process

```python
def process(event: str, receipt: Dict, contract: PublicId) -> Dict
```

Process tx receipt.
