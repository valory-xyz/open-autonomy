<a id="packages.valory.skills.abstract_round_abci.handlers"></a>

# packages.valory.skills.abstract`_`round`_`abci.handlers

This module contains the handler for the 'abstract_round_abci' skill.

<a id="packages.valory.skills.abstract_round_abci.handlers.exception_to_info_msg"></a>

#### exception`_`to`_`info`_`msg

```python
def exception_to_info_msg(exception: Exception) -> str
```

Trnasform an exception to an info string message.

<a id="packages.valory.skills.abstract_round_abci.handlers.HandlerUtils"></a>

## HandlerUtils Objects

```python
class HandlerUtils(ABC)
```

MixIn class with handler utils.

<a id="packages.valory.skills.abstract_round_abci.handlers.ABCIRoundHandler"></a>

## ABCIRoundHandler Objects

```python
class ABCIRoundHandler(HandlerUtils,  ABCIHandler)
```

ABCI handler.

<a id="packages.valory.skills.abstract_round_abci.handlers.ABCIRoundHandler.info"></a>

#### info

```python
def info(message: AbciMessage, dialogue: AbciDialogue) -> AbciMessage
```

Handle the 'info' request.

<a id="packages.valory.skills.abstract_round_abci.handlers.ABCIRoundHandler.begin_block"></a>

#### begin`_`block

```python
def begin_block(message: AbciMessage, dialogue: AbciDialogue) -> AbciMessage
```

Handle the 'begin_block' request.

<a id="packages.valory.skills.abstract_round_abci.handlers.ABCIRoundHandler.check_tx"></a>

#### check`_`tx

```python
def check_tx(message: AbciMessage, dialogue: AbciDialogue) -> AbciMessage
```

Handle the 'check_tx' request.

<a id="packages.valory.skills.abstract_round_abci.handlers.ABCIRoundHandler.deliver_tx"></a>

#### deliver`_`tx

```python
def deliver_tx(message: AbciMessage, dialogue: AbciDialogue) -> AbciMessage
```

Handle the 'deliver_tx' request.

<a id="packages.valory.skills.abstract_round_abci.handlers.ABCIRoundHandler.end_block"></a>

#### end`_`block

```python
def end_block(message: AbciMessage, dialogue: AbciDialogue) -> AbciMessage
```

Handle the 'end_block' request.

<a id="packages.valory.skills.abstract_round_abci.handlers.ABCIRoundHandler.commit"></a>

#### commit

```python
def commit(message: AbciMessage, dialogue: AbciDialogue) -> AbciMessage
```

Handle the 'commit' request.

<a id="packages.valory.skills.abstract_round_abci.handlers.HttpHandler"></a>

## HttpHandler Objects

```python
class HttpHandler(HandlerUtils,  Handler)
```

The HTTP response handler.

<a id="packages.valory.skills.abstract_round_abci.handlers.HttpHandler.setup"></a>

#### setup

```python
def setup() -> None
```

Set up the handler.

<a id="packages.valory.skills.abstract_round_abci.handlers.HttpHandler.teardown"></a>

#### teardown

```python
def teardown() -> None
```

Tear down the handler.

<a id="packages.valory.skills.abstract_round_abci.handlers.HttpHandler.handle"></a>

#### handle

```python
def handle(message: Message) -> None
```

Handle a message.

<a id="packages.valory.skills.abstract_round_abci.handlers.SigningHandler"></a>

## SigningHandler Objects

```python
class SigningHandler(HandlerUtils,  Handler)
```

Implement the transaction handler.

<a id="packages.valory.skills.abstract_round_abci.handlers.SigningHandler.setup"></a>

#### setup

```python
def setup() -> None
```

Implement the setup for the handler.

<a id="packages.valory.skills.abstract_round_abci.handlers.SigningHandler.teardown"></a>

#### teardown

```python
def teardown() -> None
```

Implement the handler teardown.

<a id="packages.valory.skills.abstract_round_abci.handlers.SigningHandler.handle"></a>

#### handle

```python
def handle(message: Message) -> None
```

Implement the reaction to a message.

**Arguments**:

- `message`: the message

<a id="packages.valory.skills.abstract_round_abci.handlers.LedgerApiHandler"></a>

## LedgerApiHandler Objects

```python
class LedgerApiHandler(HandlerUtils,  Handler)
```

Implement the ledger handler.

<a id="packages.valory.skills.abstract_round_abci.handlers.LedgerApiHandler.setup"></a>

#### setup

```python
def setup() -> None
```

Implement the setup for the handler.

<a id="packages.valory.skills.abstract_round_abci.handlers.LedgerApiHandler.handle"></a>

#### handle

```python
def handle(message: Message) -> None
```

Implement the reaction to a message.

**Arguments**:

- `message`: the message

**Returns**:

None

<a id="packages.valory.skills.abstract_round_abci.handlers.LedgerApiHandler.teardown"></a>

#### teardown

```python
def teardown() -> None
```

Implement the handler teardown.

<a id="packages.valory.skills.abstract_round_abci.handlers.ContractApiHandler"></a>

## ContractApiHandler Objects

```python
class ContractApiHandler(HandlerUtils,  Handler)
```

Implement the contract api handler.

<a id="packages.valory.skills.abstract_round_abci.handlers.ContractApiHandler.setup"></a>

#### setup

```python
def setup() -> None
```

Implement the setup for the handler.

<a id="packages.valory.skills.abstract_round_abci.handlers.ContractApiHandler.handle"></a>

#### handle

```python
def handle(message: Message) -> None
```

Implement the reaction to a message.

**Arguments**:

- `message`: the message

**Returns**:

None

<a id="packages.valory.skills.abstract_round_abci.handlers.ContractApiHandler.teardown"></a>

#### teardown

```python
def teardown() -> None
```

Implement the handler teardown.

