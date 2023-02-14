<a id="packages.valory.protocols.abci.dialogues"></a>

# packages.valory.protocols.abci.dialogues

This module contains the classes required for abci dialogue management.

- AbciDialogue: The dialogue class maintains state of a dialogue and manages it.
- AbciDialogues: The dialogues class keeps track of all dialogues.

<a id="packages.valory.protocols.abci.dialogues.AbciDialogue"></a>

## AbciDialogue Objects

```python
class AbciDialogue(Dialogue)
```

The abci dialogue class maintains state of a dialogue and manages it.

<a id="packages.valory.protocols.abci.dialogues.AbciDialogue.Role"></a>

## Role Objects

```python
class Role(Dialogue.Role)
```

This class defines the agent's role in a abci dialogue.

<a id="packages.valory.protocols.abci.dialogues.AbciDialogue.EndState"></a>

## EndState Objects

```python
class EndState(Dialogue.EndState)
```

This class defines the end states of a abci dialogue.

<a id="packages.valory.protocols.abci.dialogues.AbciDialogue.__init__"></a>

#### `__`init`__`

```python
def __init__(dialogue_label: DialogueLabel,
             self_address: Address,
             role: Dialogue.Role,
             message_class: Type[AbciMessage] = AbciMessage) -> None
```

Initialize a dialogue.

**Arguments**:

- `dialogue_label`: the identifier of the dialogue
- `self_address`: the address of the entity for whom this dialogue is maintained
- `role`: the role of the agent this dialogue is maintained for
- `message_class`: the message class used

<a id="packages.valory.protocols.abci.dialogues.AbciDialogues"></a>

## AbciDialogues Objects

```python
class AbciDialogues(Dialogues, ABC)
```

This class keeps track of all abci dialogues.

<a id="packages.valory.protocols.abci.dialogues.AbciDialogues.__init__"></a>

#### `__`init`__`

```python
def __init__(self_address: Address,
             role_from_first_message: Callable[[Message, Address],
                                               Dialogue.Role],
             dialogue_class: Type[AbciDialogue] = AbciDialogue) -> None
```

Initialize dialogues.

**Arguments**:

- `self_address`: the address of the entity for whom dialogues are maintained
- `dialogue_class`: the dialogue class used
- `role_from_first_message`: the callable determining role from first message

