<a id="packages.valory.skills.abstract_round_abci.behaviour_utils"></a>

# packages.valory.skills.abstract`_`round`_`abci.behaviour`_`utils

This module contains helper classes for behaviours.

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

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.AsyncBehaviour.try_send"></a>

#### try`_`send

```python
def try_send(message: Any) -> None
```

Try to send a message to a waiting behaviour.

It will be send only if the behaviour is actually
waiting for a message.

**Arguments**:

- `message`: a Python object.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.AsyncBehaviour.wait_for_condition"></a>

#### wait`_`for`_`condition

```python
@classmethod
def wait_for_condition(cls, condition: Callable[[], bool]) -> Any
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
def wait_for_message(condition: Callable = lambda message: True) -> Any
```

Wait for message.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.AsyncBehaviour.act"></a>

#### act

```python
def act() -> None
```

Do the act.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.BaseState"></a>

## BaseState Objects

```python
class BaseState(AsyncBehaviour,  State,  ABC)
```

Base class for FSM states.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.BaseState.__init__"></a>

#### `__`init`__`

```python
def __init__(**kwargs: Any)
```

Initialize a base state behaviour.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.BaseState.check_in_round"></a>

#### check`_`in`_`round

```python
def check_in_round(round_id: str) -> bool
```

Check that we entered in a specific round.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.BaseState.check_not_in_round"></a>

#### check`_`not`_`in`_`round

```python
def check_not_in_round(round_id: str) -> bool
```

Check that we are not in a specific round.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.BaseState.is_round_ended"></a>

#### is`_`round`_`ended

```python
def is_round_ended(round_id: str) -> Callable[[], bool]
```

Get a callable to check whether the current round has ended.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.BaseState.wait_until_round_end"></a>

#### wait`_`until`_`round`_`end

```python
def wait_until_round_end() -> Any
```

Wait until the ABCI application exits from a round.

:yield: None

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

Calls `_send_transaction` and uses the default stop condition (based on round id).

:param: payload: the payload to send
:yield: the responses

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.BaseState.async_act_wrapper"></a>

#### async`_`act`_`wrapper

```python
def async_act_wrapper() -> Generator
```

Do the act, supporting asynchronous execution.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.BaseState.default_callback_request"></a>

#### default`_`callback`_`request

```python
def default_callback_request(message: Message) -> None
```

Implement default callback request.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.BaseState.send_raw_transaction"></a>

#### send`_`raw`_`transaction

```python
def send_raw_transaction(transaction: RawTransaction) -> Generator[None, None, str]
```

Send raw transactions to the ledger for mining.

<a id="packages.valory.skills.abstract_round_abci.behaviour_utils.BaseState.get_contract_api_response"></a>

#### get`_`contract`_`api`_`response

```python
def get_contract_api_response(contract_address: Optional[str], contract_id: str, contract_callable: str, **kwargs: Any, ,) -> Generator[None, None, ContractApiMessage]
```

Request contract safe transaction hash

**Arguments**:

- `contract_address`: the contract address
- `contract_id`: the contract id
- `contract_callable`: the collable to call on the contract
- `kwargs`: keyword argument for the contract api request

**Returns**:

the contract api response

