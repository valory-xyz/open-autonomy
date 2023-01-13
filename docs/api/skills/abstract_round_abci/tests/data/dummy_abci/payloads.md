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

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.payloads.DummyStartingPayload"></a>

## DummyStartingPayload Objects

```python
@dataclass(frozen=True)
class DummyStartingPayload(BaseTxPayload)
```

Represent a transaction payload for the DummyStartingRound.

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.payloads.DummyRandomnessPayload"></a>

## DummyRandomnessPayload Objects

```python
@dataclass(frozen=True)
class DummyRandomnessPayload(BaseTxPayload)
```

Represent a transaction payload for the DummyRandomnessRound.

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.payloads.DummyKeeperSelectionPayload"></a>

## DummyKeeperSelectionPayload Objects

```python
@dataclass(frozen=True)
class DummyKeeperSelectionPayload(BaseTxPayload)
```

Represent a transaction payload for the DummyKeeperSelectionRound.

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.payloads.DummyFinalPayload"></a>

## DummyFinalPayload Objects

```python
@dataclass(frozen=True)
class DummyFinalPayload(BaseTxPayload)
```

Represent a transaction payload for the DummyFinalRound.

