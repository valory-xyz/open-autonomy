<a id="packages.valory.skills.abstract_round_abci.dialogues"></a>

# packages.valory.skills.abstract`_`round`_`abci.dialogues

This module contains the classes required for dialogue management.

<a id="packages.valory.skills.abstract_round_abci.dialogues.AbciDialogues"></a>

## AbciDialogues Objects

```python
class AbciDialogues(Model, BaseAbciDialogues)
```

The dialogues class keeps track of all dialogues.

<a id="packages.valory.skills.abstract_round_abci.dialogues.AbciDialogues.__init__"></a>

#### `__`init`__`

```python
def __init__(**kwargs: Any) -> None
```

Initialize dialogues.

**Arguments**:

- `kwargs`: keyword arguments

<a id="packages.valory.skills.abstract_round_abci.dialogues.HttpDialogues"></a>

## HttpDialogues Objects

```python
class HttpDialogues(Model, BaseHttpDialogues)
```

This class keeps track of all http dialogues.

<a id="packages.valory.skills.abstract_round_abci.dialogues.HttpDialogues.__init__"></a>

#### `__`init`__`

```python
def __init__(**kwargs: Any) -> None
```

Initialize dialogues.

**Arguments**:

- `kwargs`: keyword arguments

<a id="packages.valory.skills.abstract_round_abci.dialogues.SigningDialogues"></a>

## SigningDialogues Objects

```python
class SigningDialogues(Model, BaseSigningDialogues)
```

This class keeps track of all signing dialogues.

<a id="packages.valory.skills.abstract_round_abci.dialogues.SigningDialogues.__init__"></a>

#### `__`init`__`

```python
def __init__(**kwargs: Any) -> None
```

Initialize dialogues.

**Arguments**:

- `kwargs`: keyword arguments

<a id="packages.valory.skills.abstract_round_abci.dialogues.LedgerApiDialogue"></a>

## LedgerApiDialogue Objects

```python
class LedgerApiDialogue(  # pylint: disable=too-few-public-methods
        BaseLedgerApiDialogue)
```

The dialogue class maintains state of a dialogue and manages it.

<a id="packages.valory.skills.abstract_round_abci.dialogues.LedgerApiDialogue.__init__"></a>

#### `__`init`__`

```python
def __init__(dialogue_label: BaseDialogueLabel,
             self_address: Address,
             role: BaseDialogue.Role,
             message_class: Type[LedgerApiMessage] = LedgerApiMessage) -> None
```

Initialize a dialogue.

**Arguments**:

- `dialogue_label`: the identifier of the dialogue
- `self_address`: the address of the entity for whom this dialogue is maintained
- `role`: the role of the agent this dialogue is maintained for
- `message_class`: the message class

<a id="packages.valory.skills.abstract_round_abci.dialogues.LedgerApiDialogue.terms"></a>

#### terms

```python
@property
def terms() -> Terms
```

Get the terms.

<a id="packages.valory.skills.abstract_round_abci.dialogues.LedgerApiDialogue.terms"></a>

#### terms

```python
@terms.setter
def terms(terms: Terms) -> None
```

Set the terms.

<a id="packages.valory.skills.abstract_round_abci.dialogues.LedgerApiDialogues"></a>

## LedgerApiDialogues Objects

```python
class LedgerApiDialogues(Model, BaseLedgerApiDialogues)
```

The dialogues class keeps track of all dialogues.

<a id="packages.valory.skills.abstract_round_abci.dialogues.LedgerApiDialogues.__init__"></a>

#### `__`init`__`

```python
def __init__(**kwargs: Any) -> None
```

Initialize dialogues.

**Arguments**:

- `kwargs`: keyword arguments

<a id="packages.valory.skills.abstract_round_abci.dialogues.ContractApiDialogue"></a>

## ContractApiDialogue Objects

```python
class ContractApiDialogue(  # pylint: disable=too-few-public-methods
        BaseContractApiDialogue)
```

The dialogue class maintains state of a dialogue and manages it.

<a id="packages.valory.skills.abstract_round_abci.dialogues.ContractApiDialogue.__init__"></a>

#### `__`init`__`

```python
def __init__(
        dialogue_label: BaseDialogueLabel,
        self_address: Address,
        role: BaseDialogue.Role,
        message_class: Type[ContractApiMessage] = ContractApiMessage) -> None
```

Initialize a dialogue.

**Arguments**:

- `dialogue_label`: the identifier of the dialogue
- `self_address`: the address of the entity for whom this dialogue is maintained
- `role`: the role of the agent this dialogue is maintained for
- `message_class`: the message class

<a id="packages.valory.skills.abstract_round_abci.dialogues.ContractApiDialogue.terms"></a>

#### terms

```python
@property
def terms() -> Terms
```

Get the terms.

<a id="packages.valory.skills.abstract_round_abci.dialogues.ContractApiDialogue.terms"></a>

#### terms

```python
@terms.setter
def terms(terms: Terms) -> None
```

Set the terms.

<a id="packages.valory.skills.abstract_round_abci.dialogues.ContractApiDialogues"></a>

## ContractApiDialogues Objects

```python
class ContractApiDialogues(Model, BaseContractApiDialogues)
```

The dialogues class keeps track of all dialogues.

<a id="packages.valory.skills.abstract_round_abci.dialogues.ContractApiDialogues.__init__"></a>

#### `__`init`__`

```python
def __init__(**kwargs: Any) -> None
```

Initialize dialogues.

<a id="packages.valory.skills.abstract_round_abci.dialogues.TendermintDialogues"></a>

## TendermintDialogues Objects

```python
class TendermintDialogues(Model, BaseTendermintDialogues)
```

The dialogues class keeps track of all dialogues.

<a id="packages.valory.skills.abstract_round_abci.dialogues.TendermintDialogues.__init__"></a>

#### `__`init`__`

```python
def __init__(**kwargs: Any) -> None
```

Initialize dialogues.

**Arguments**:

- `kwargs`: keyword arguments

<a id="packages.valory.skills.abstract_round_abci.dialogues.IpfsDialogues"></a>

## IpfsDialogues Objects

```python
class IpfsDialogues(Model, BaseIpfsDialogues)
```

A class to keep track of IPFS dialogues.

<a id="packages.valory.skills.abstract_round_abci.dialogues.IpfsDialogues.__init__"></a>

#### `__`init`__`

```python
def __init__(**kwargs: Any) -> None
```

Initialize dialogues.

**Arguments**:

- `kwargs`: keyword arguments

