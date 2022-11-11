<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.payloads"></a>

# packages.valory.skills.abstract`_`round`_`abci.tests.data.dummy`_`abci.payloads

This module contains the transaction payloads of the DummyAbciApp.

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.payloads.TransactionType"></a>

## TransactionType Objects

```python
class TransactionType(Enum)
```

Enumeration of transaction types.

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.payloads.TransactionType.__str__"></a>

#### `__`str`__`

```python
def __str__() -> str
```

Get the string value of the transaction type.

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.payloads.BaseDummyPayload"></a>

## BaseDummyPayload Objects

```python
class BaseDummyPayload(BaseTxPayload,  ABC)
```

Base payload for DummyAbciApp.

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.payloads.BaseDummyPayload.__init__"></a>

#### `__`init`__`

```python
def __init__(sender: str, content: Hashable, **kwargs: Any) -> None
```

Initialize a transaction payload.

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.payloads.BaseDummyPayload.data"></a>

#### data

```python
@property
def data() -> Dict[str, Hashable]
```

Get the data.

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.payloads.DummyStartingPayload"></a>

## DummyStartingPayload Objects

```python
class DummyStartingPayload(BaseDummyPayload)
```

Represent a transaction payload for the DummyStartingRound.

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.payloads.DummyRandomnessPayload"></a>

## DummyRandomnessPayload Objects

```python
class DummyRandomnessPayload(BaseTxPayload)
```

Represent a transaction payload for the DummyRandomnessRound.

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.payloads.DummyRandomnessPayload.__init__"></a>

#### `__`init`__`

```python
def __init__(sender: str, round_id: int, randomness: str, **kwargs: Any) -> None
```

Initialize DummyRandomnessPayload

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.payloads.DummyRandomnessPayload.round_id"></a>

#### round`_`id

```python
@property
def round_id() -> int
```

Get the round id.

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.payloads.DummyRandomnessPayload.randomness"></a>

#### randomness

```python
@property
def randomness() -> str
```

Get the randomness.

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.payloads.DummyRandomnessPayload.data"></a>

#### data

```python
@property
def data() -> Dict
```

Get the data.

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.payloads.DummyKeeperSelectionPayload"></a>

## DummyKeeperSelectionPayload Objects

```python
class DummyKeeperSelectionPayload(BaseDummyPayload)
```

Represent a transaction payload for the DummyKeeperSelectionRound.

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.payloads.DummyFinalPayload"></a>

## DummyFinalPayload Objects

```python
class DummyFinalPayload(BaseDummyPayload)
```

Represent a transaction payload for the DummyFinalRound.

