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
class RegistrationPayload(BaseTxPayload)
```

Represent a transaction payload of type 'registration'.

<a id="packages.valory.skills.registration_abci.payloads.RegistrationPayload.__init__"></a>

#### `__`init`__`

```python
def __init__(sender: str, initialisation: Optional[str] = None, **kwargs: Any) -> None
```

Initialize an 'select_keeper' transaction payload.

**Arguments**:

- `sender`: the sender (Ethereum) address
- `initialisation`: the initialisation data
- `kwargs`: the keyword arguments

<a id="packages.valory.skills.registration_abci.payloads.RegistrationPayload.initialisation"></a>

#### initialisation

```python
@property
def initialisation() -> Optional[str]
```

Get the initialisation.

<a id="packages.valory.skills.registration_abci.payloads.RegistrationPayload.data"></a>

#### data

```python
@property
def data() -> Dict
```

Get the data.

