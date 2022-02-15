<a id="packages.valory.skills.abstract_round_abci.behaviour_utils"></a>

# packages.valory.skills.abstract`_`round`_`abci.behaviour`_`utils

This module contains helper classes for behaviours.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.SendException"></a>

## SendException Objects

```python
class SendException(Exception)
```

Exception raised if the 'try_send' to an AsyncBehaviour failed.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.TimeoutException"></a>

## TimeoutException Objects

```python
class TimeoutException(Exception)
```

Exception raised when a timeout during AsyncBehaviour occurs.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.AsyncBehaviour"></a>

## AsyncBehaviour Objects

```python
class AsyncBehaviour(ABC)
```

MixIn behaviour class that support limited asynchronous programming.

An AsyncBehaviour can be in three states:
- READY: no suspended 'async_act' execution;
- RUNNING: 'act' called, and waiting for a message
- WAITING_TICK: 'act' called, and waiting for the next 'act' call

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.AsyncBehaviour.AsyncState"></a>

## AsyncState Objects

```python
class AsyncState(Enum)
```

Enumeration of AsyncBehaviour states.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.AsyncBehaviour.__init__"></a>

#### `__`init`__`

```python
def __init__() -> None
```

Initialize the async behaviour.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.AsyncBehaviour.async_act"></a>

#### async`_`act

```python
@abstractmethod
def async_act() -> Generator
```

Do the act, supporting asynchronous execution.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.AsyncBehaviour.async_act_wrapper"></a>

#### async`_`act`_`wrapper

```python
@abstractmethod
def async_act_wrapper() -> Generator
```

Do the act, supporting asynchronous execution.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.AsyncBehaviour.state"></a>

#### state

```python
@property
def state() -> AsyncState
```

Get the 'async state'.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.AsyncBehaviour.is_stopped"></a>

#### is`_`stopped

```python
@property
def is_stopped() -> bool
```

Check whether the behaviour has stopped.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.AsyncBehaviour.try_send"></a>

#### try`_`send

```python
def try_send(message: Any) -> None
```

Try to send a message to a waiting behaviour.

It will be sent only if the behaviour is actually waiting for a message,
and it was not already notified.

**Arguments**:

:raises: SendException if the behaviour was not waiting for a message,
    or if it was already notified.
- `message`: a Python object.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.AsyncBehaviour.wait_for_condition"></a>

#### wait`_`for`_`condition

```python
@classmethod
def wait_for_condition(cls, condition: Callable[[], bool], timeout: Optional[float] = None) -> Generator[None, None, None]
```

Wait for a condition to happen.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.AsyncBehaviour.sleep"></a>

#### sleep

```python
def sleep(seconds: float) -> Any
```

Delay execution for a given number of seconds.

The argument may be a floating point number for subsecond precision.

**Arguments**:

:yield: None
- `seconds`: the seconds

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.AsyncBehaviour.wait_for_message"></a>

#### wait`_`for`_`message

```python
def wait_for_message(condition: Callable = lambda message: True, timeout: Optional[float] = None) -> Any
```

Wait for message.

Care must be taken. This method does not handle concurrent requests.
Use directly after a request is being sent.

**Arguments**:

- `condition`: a callable
- `timeout`: max time to wait (in seconds)

**Returns**:

a message

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.AsyncBehaviour.setup"></a>

#### setup

```python
def setup() -> None
```

Setup behaviour.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.AsyncBehaviour.act"></a>

#### act

```python
def act() -> None
```

Do the act.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.AsyncBehaviour.stop"></a>

#### stop

```python
def stop() -> None
```

Stop the execution of the behaviour.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.CleanUpBehaviour"></a>

## CleanUpBehaviour Objects

```python
class CleanUpBehaviour(SimpleBehaviour,  ABC)
```

Class for clean-up related functionality of behaviours.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.CleanUpBehaviour.__init__"></a>

#### `__`init`__`

```python
def __init__(**kwargs: Any)
```

Initialize a base state behaviour.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.CleanUpBehaviour.clean_up"></a>

#### clean`_`up

```python
def clean_up() -> None
```

Clean up the resources due to a 'stop' event.

It can be optionally implemented by the concrete classes.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.CleanUpBehaviour.handle_late_messages"></a>

#### handle`_`late`_`messages

```python
def handle_late_messages(message: Message) -> None
```

Handle late arriving messages.

Runs from another behaviour, even if the behaviour implementing the method has been exited.
It can be optionally implemented by the concrete classes.

**Arguments**:

- `message`: the late arriving message to handle.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.BaseState"></a>

## BaseState Objects

```python
class BaseState(AsyncBehaviour,  CleanUpBehaviour,  ABC)
```

Base class for FSM states.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.BaseState.__init__"></a>

#### `__`init`__`

```python
def __init__(**kwargs: Any)
```

Initialize a base state behaviour.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.BaseState.params"></a>

#### params

```python
@property
def params() -> BaseParams
```

Return the params.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.BaseState.period_state"></a>

#### period`_`state

```python
@property
def period_state() -> BasePeriodState
```

Return the period state.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.BaseState.check_in_round"></a>

#### check`_`in`_`round

```python
def check_in_round(round_id: str) -> bool
```

Check that we entered a specific round.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.BaseState.check_in_last_round"></a>

#### check`_`in`_`last`_`round

```python
def check_in_last_round(round_id: str) -> bool
```

Check that we entered a specific round.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.BaseState.check_not_in_round"></a>

#### check`_`not`_`in`_`round

```python
def check_not_in_round(round_id: str) -> bool
```

Check that we are not in a specific round.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.BaseState.check_not_in_last_round"></a>

#### check`_`not`_`in`_`last`_`round

```python
def check_not_in_last_round(round_id: str) -> bool
```

Check that we are not in a specific round.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.BaseState.check_round_has_finished"></a>

#### check`_`round`_`has`_`finished

```python
def check_round_has_finished(round_id: str) -> bool
```

Check that the round has finished.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.BaseState.check_round_height_has_changed"></a>

#### check`_`round`_`height`_`has`_`changed

```python
def check_round_height_has_changed(round_height: int) -> bool
```

Check that the round height has changed.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.BaseState.is_round_ended"></a>

#### is`_`round`_`ended

```python
def is_round_ended(round_id: str) -> Callable[[], bool]
```

Get a callable to check whether the current round has ended.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.BaseState.wait_until_round_end"></a>

#### wait`_`until`_`round`_`end

```python
def wait_until_round_end(timeout: Optional[float] = None) -> Generator[None, None, None]
```

Wait until the ABCI application exits from a round.

**Arguments**:

:yield: None
- `timeout`: the timeout for the wait

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.BaseState.wait_from_last_timestamp"></a>

#### wait`_`from`_`last`_`timestamp

```python
def wait_from_last_timestamp(seconds: float) -> Any
```

Delay execution for a given number of seconds from the last timestamp.

The argument may be a floating point number for subsecond precision.

**Arguments**:

:yield: None
- `seconds`: the seconds

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.BaseState.is_done"></a>

#### is`_`done

```python
def is_done() -> bool
```

Check whether the state is done.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.BaseState.set_done"></a>

#### set`_`done

```python
def set_done() -> None
```

Set the behaviour to done.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.BaseState.send_a2a_transaction"></a>

#### send`_`a2a`_`transaction

```python
def send_a2a_transaction(payload: BaseTxPayload) -> Generator
```

Send transaction and wait for the response, and repeat until not successful.

:param: payload: the payload to send
:yield: the responses

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.BaseState.async_act_wrapper"></a>

#### async`_`act`_`wrapper

```python
def async_act_wrapper() -> Generator
```

Do the act, supporting asynchronous execution.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.BaseState.get_callback_request"></a>

#### get`_`callback`_`request

```python
def get_callback_request() -> Callable[[Message, BasePeriodState], None]
```

Wrapper for callback request which depends on whether the message has not been handled on time.

**Returns**:

the request callback.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.BaseState.get_http_response"></a>

#### get`_`http`_`response

```python
def get_http_response(method: str, url: str, content: Optional[bytes] = None, headers: Optional[List[OrderedDict[str, str]]] = None, parameters: Optional[List[Tuple[str, str]]] = None) -> Generator[None, None, HttpMessage]
```

Send an http request message from the skill context.

This method is skill-specific, and therefore
should not be used elsewhere.

Happy-path full flow of the messages.

_do_request:
    AbstractRoundAbci skill -> (HttpMessage | REQUEST) -> Http client connection
    Http client connection -> (HttpMessage | RESPONSE) -> AbstractRoundAbci skill

**Arguments**:

:yield: HttpMessage object
- `method`: the http request method (i.e. 'GET' or 'POST').
- `url`: the url to send the message to.
- `content`: the payload.
- `headers`: headers to be included.
- `parameters`: url query parameters.

**Returns**:

the http message and the http dialogue

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.BaseState.get_signature"></a>

#### get`_`signature

```python
def get_signature(message: bytes, is_deprecated_mode: bool = False) -> Generator[None, None, str]
```

Get signature for message.

Happy-path full flow of the messages.

_send_signing_request:
    AbstractRoundAbci skill -> (SigningMessage | SIGN_MESSAGE) -> DecisionMaker
    DecisionMaker -> (SigningMessage | SIGNED_MESSAGE) -> AbstractRoundAbci skill

**Arguments**:

:yield: SigningMessage object
- `message`: message bytes
- `is_deprecated_mode`: is deprecated mode flag

**Returns**:

message signature

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.BaseState.send_raw_transaction"></a>

#### send`_`raw`_`transaction

```python
def send_raw_transaction(transaction: RawTransaction) -> Generator[None, None, Optional[str]]
```

Send raw transactions to the ledger for mining.

Happy-path full flow of the messages.

_send_transaction_signing_request:
        AbstractRoundAbci skill -> (SigningMessage | SIGN_TRANSACTION) -> DecisionMaker
        DecisionMaker -> (SigningMessage | SIGNED_TRANSACTION) -> AbstractRoundAbci skill

_send_transaction_request:
    AbstractRoundAbci skill -> (LedgerApiMessage | SEND_SIGNED_TRANSACTION) -> Ledger connection
    Ledger connection -> (LedgerApiMessage | TRANSACTION_DIGEST) -> AbstractRoundAbci skill

**Arguments**:

:yield: SigningMessage object
- `transaction`: transaction data

**Returns**:

transaction hash

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.BaseState.get_transaction_receipt"></a>

#### get`_`transaction`_`receipt

```python
def get_transaction_receipt(tx_digest: str, retry_timeout: Optional[int] = None, retry_attempts: Optional[int] = None) -> Generator[None, None, Optional[Dict]]
```

Get transaction receipt.

Happy-path full flow of the messages.

_send_transaction_receipt_request:
    AbstractRoundAbci skill -> (LedgerApiMessage | GET_TRANSACTION_RECEIPT) -> Ledger connection
    Ledger connection -> (LedgerApiMessage | TRANSACTION_RECEIPT) -> AbstractRoundAbci skill

**Arguments**:

:yield: LedgerApiMessage object
- `tx_digest`: transaction digest received from raw transaction.
- `retry_timeout`: retry timeout.
- `retry_attempts`: number of retry attempts allowed.

**Returns**:

transaction receipt data

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.BaseState.get_ledger_api_response"></a>

#### get`_`ledger`_`api`_`response

```python
def get_ledger_api_response(performative: LedgerApiMessage.Performative, ledger_callable: str, **kwargs: Any, ,) -> Generator[None, None, LedgerApiMessage]
```

Request data from ledger api

Happy-path full flow of the messages.

AbstractRoundAbci skill -> (LedgerApiMessage | LedgerApiMessage.Performative) -> Ledger connection
Ledger connection -> (LedgerApiMessage | LedgerApiMessage.Performative) -> AbstractRoundAbci skill

**Arguments**:

- `performative`: the message performative
- `ledger_callable`: the callable to call on the contract
- `kwargs`: keyword argument for the contract api request

**Returns**:

the contract api response

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.BaseState.get_contract_api_response"></a>

#### get`_`contract`_`api`_`response

```python
def get_contract_api_response(performative: ContractApiMessage.Performative, contract_address: Optional[str], contract_id: str, contract_callable: str, **kwargs: Any, ,) -> Generator[None, None, ContractApiMessage]
```

Request contract safe transaction hash

Happy-path full flow of the messages.

AbstractRoundAbci skill -> (ContractApiMessage | ContractApiMessage.Performative) -> Ledger connection (contract dispatcher)
Ledger connection (contract dispatcher) -> (ContractApiMessage | ContractApiMessage.Performative) -> AbstractRoundAbci skill

**Arguments**:

- `performative`: the message performative
- `contract_address`: the contract address
- `contract_id`: the contract id
- `contract_callable`: the callable to call on the contract
- `kwargs`: keyword argument for the contract api request

**Returns**:

the contract api response

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.DegenerateState"></a>

## DegenerateState Objects

```python
class DegenerateState(BaseState,  ABC)
```

An abstract matching behaviour for final and degenerate rounds.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.DegenerateState.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Raise a RuntimeError.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.make_degenerate_state"></a>

#### make`_`degenerate`_`state

```python
def make_degenerate_state(round_id: str) -> Type[DegenerateState]
```

Make a degenerate state class.

