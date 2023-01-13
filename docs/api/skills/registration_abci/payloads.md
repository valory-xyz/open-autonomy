<a id="packages.valory.skills.registration_abci.payloads"></a>

# packages.valory.skills.registration`_`abci.payloads

This module contains the transaction payloads for common apps.

<a id="packages.valory.skills.registration_abci.payloads.TransactionType"></a>

## TransactionType Objects

```python
class TransactionType(Enum)
```

Enumeration of transaction types.

<a id="packages.valory.skills.registration_abci.payloads.TransactionType.__str__"></a>

#### `__`str`__`

```python
def __str__() -> str
```

Get the string value of the transaction type.

<a id="packages.valory.skills.registration_abci.payloads.RegistrationPayload"></a>

## RegistrationPayload Objects

```python
@dataclass(frozen=True)
class RegistrationPayload(BaseTxPayload)
```

Represent a transaction payload of type 'registration'.

