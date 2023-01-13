<a id="packages.valory.skills.transaction_settlement_abci.payloads"></a>

# packages.valory.skills.transaction`_`settlement`_`abci.payloads

This module contains the transaction payloads for common apps.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.RandomnessPayload"></a>

## RandomnessPayload Objects

```python
@dataclass(frozen=True)
class RandomnessPayload(BaseTxPayload)
```

Represent a transaction payload of type 'randomness'.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.SelectKeeperPayload"></a>

## SelectKeeperPayload Objects

```python
@dataclass(frozen=True)
class SelectKeeperPayload(BaseTxPayload)
```

Represent a transaction payload of type 'select_keeper'.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.ValidatePayload"></a>

## ValidatePayload Objects

```python
@dataclass(frozen=True)
class ValidatePayload(BaseTxPayload)
```

Represent a transaction payload of type 'validate'.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.CheckTransactionHistoryPayload"></a>

## CheckTransactionHistoryPayload Objects

```python
@dataclass(frozen=True)
class CheckTransactionHistoryPayload(BaseTxPayload)
```

Represent a transaction payload of type 'check'.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.SynchronizeLateMessagesPayload"></a>

## SynchronizeLateMessagesPayload Objects

```python
@dataclass(frozen=True)
class SynchronizeLateMessagesPayload(BaseTxPayload)
```

Represent a transaction payload of type 'synchronize'.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.SignaturePayload"></a>

## SignaturePayload Objects

```python
@dataclass(frozen=True)
class SignaturePayload(BaseTxPayload)
```

Represent a transaction payload of type 'signature'.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.FinalizationTxPayload"></a>

## FinalizationTxPayload Objects

```python
@dataclass(frozen=True)
class FinalizationTxPayload(BaseTxPayload)
```

Represent a transaction payload of type 'finalization'.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.ResetPayload"></a>

## ResetPayload Objects

```python
@dataclass(frozen=True)
class ResetPayload(BaseTxPayload)
```

Represent a transaction payload of type 'reset'.

