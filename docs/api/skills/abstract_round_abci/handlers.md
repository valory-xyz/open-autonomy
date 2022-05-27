<a id="packages.valory.skills.abstract_round_abci.handlers"></a>

# packages.valory.skills.abstract`_`round`_`abci.handlers

This module contains the handler for the 'abstract_round_abci' skill.

<a id="packages.valory.skills.abstract_round_abci.handlers.exception_to_info_msg"></a>

#### exception`_`to`_`info`_`msg

```python
def exception_to_info_msg(exception: Exception) -> str
```

Transform an exception to an info string message.

<a id="packages.valory.skills.abstract_round_abci.handlers.ABCIRoundHandler"></a>

## ABCIRoundHandler Objects

```python
class ABCIRoundHandler(ABCIHandler)
```

ABCI handler.

<a id="packages.valory.skills.abstract_round_abci.handlers.ABCIRoundHandler.info"></a>

#### info

```python
def info(message: AbciMessage, dialogue: AbciDialogue) -> AbciMessage
```

Handle the 'info' request.

<a id="packages.valory.skills.abstract_round_abci.handlers.ABCIRoundHandler.init_chain"></a>

#### init`_`chain

```python
def init_chain(message: AbciMessage, dialogue: AbciDialogue) -> AbciMessage
```

Handle a message of REQUEST_INIT_CHAIN performative.

**Arguments**:

- `message`: the ABCI request.
- `dialogue`: the ABCI dialogue.

**Returns**:

the response.

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

<a id="packages.valory.skills.abstract_round_abci.handlers.AbstractResponseHandler"></a>

## AbstractResponseHandler Objects

```python
class AbstractResponseHandler(Handler,  ABC)
```

Abstract response Handler.

This abstract handler works in tandem with the 'Requests' model.
Whenever a message of 'response' type arrives, the handler
tries to dispatch it to a pending request previously registered
in 'Requests' by some other code in the same skill.

The concrete classes must set the 'allowed_response_performatives'
class attribute to the (frozen)set of performative the developer
wants the handler to handle.

<a id="packages.valory.skills.abstract_round_abci.handlers.AbstractResponseHandler.setup"></a>

#### setup

```python
def setup() -> None
```

Set up the handler.

<a id="packages.valory.skills.abstract_round_abci.handlers.AbstractResponseHandler.teardown"></a>

#### teardown

```python
def teardown() -> None
```

Tear down the handler.

<a id="packages.valory.skills.abstract_round_abci.handlers.AbstractResponseHandler.handle"></a>

#### handle

```python
def handle(message: Message) -> None
```

Handle the response message.

Steps:
1. Try to recover the 'dialogues' instance, for the protocol
of this handler, from the skill context. The attribute name used to
read the attribute is computed by '_get_dialogues_attribute_name()'
method. If no dialogues instance is found, log a message and return.
2. Try to recover the dialogue; if no dialogue is present, log a message
and return.
3. Check whether the performative is in the set of allowed performative;
if not, log a message and return.
4. Try to recover the callback of the request associated to the response
from the 'Requests' model; if no callback is present, log a message
and return.
5. If the above check have passed, then call the callback with the
received message.

**Arguments**:

- `message`: the message to handle.

<a id="packages.valory.skills.abstract_round_abci.handlers.HttpHandler"></a>

## HttpHandler Objects

```python
class HttpHandler(AbstractResponseHandler)
```

The HTTP response handler.

<a id="packages.valory.skills.abstract_round_abci.handlers.SigningHandler"></a>

## SigningHandler Objects

```python
class SigningHandler(AbstractResponseHandler)
```

Implement the transaction handler.

<a id="packages.valory.skills.abstract_round_abci.handlers.LedgerApiHandler"></a>

## LedgerApiHandler Objects

```python
class LedgerApiHandler(AbstractResponseHandler)
```

Implement the ledger handler.

<a id="packages.valory.skills.abstract_round_abci.handlers.ContractApiHandler"></a>

## ContractApiHandler Objects

```python
class ContractApiHandler(AbstractResponseHandler)
```

Implement the contract api handler.

