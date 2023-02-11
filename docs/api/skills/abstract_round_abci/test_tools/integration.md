<a id="packages.valory.skills.abstract_round_abci.test_tools.integration"></a>

# packages.valory.skills.abstract`_`round`_`abci.test`_`tools.integration

Integration tests for various transaction settlement skill's failure modes.

<a id="packages.valory.skills.abstract_round_abci.test_tools.integration.IntegrationBaseCase"></a>

## IntegrationBaseCase Objects

```python
class IntegrationBaseCase(FSMBehaviourBaseCase, ABC)
```

Base test class for integration tests.

<a id="packages.valory.skills.abstract_round_abci.test_tools.integration.IntegrationBaseCase.setup_class"></a>

#### setup`_`class

```python
@classmethod
def setup_class(cls, **kwargs: Any) -> None
```

Setup.

<a id="packages.valory.skills.abstract_round_abci.test_tools.integration.IntegrationBaseCase.teardown_class"></a>

#### teardown`_`class

```python
@classmethod
def teardown_class(cls) -> None
```

Tear down the multiplexer.

<a id="packages.valory.skills.abstract_round_abci.test_tools.integration.IntegrationBaseCase.get_message_from_decision_maker_inbox"></a>

#### get`_`message`_`from`_`decision`_`maker`_`inbox

```python
def get_message_from_decision_maker_inbox() -> Optional[Message]
```

Get message from decision maker inbox.

<a id="packages.valory.skills.abstract_round_abci.test_tools.integration.IntegrationBaseCase.process_message_cycle"></a>

#### process`_`message`_`cycle

```python
def process_message_cycle(
        handler: Optional[Handler] = None,
        expected_content: Optional[Dict] = None,
        expected_types: Optional[Dict] = None,
        mining_interval_secs: float = 0) -> Optional[Message]
```

Processes one request-response type message cycle.

Steps:
1. Calls act on behaviour to generate outgoing message
2. Checks for message in outbox
3. Sends message to multiplexer and waits for response.
4. Passes message to handler
5. Calls act on behaviour to process incoming message

**Arguments**:

- `handler`: the handler to handle a potential incoming message
- `expected_content`: the content to be expected
- `expected_types`: the types to be expected
- `mining_interval_secs`: the mining interval used in the tests

**Returns**:

the incoming message

<a id="packages.valory.skills.abstract_round_abci.test_tools.integration.IntegrationBaseCase.process_n_messages"></a>

#### process`_`n`_`messages

```python
def process_n_messages(
        ncycles: int,
        synchronized_data: Optional[BaseSynchronizedData] = None,
        behaviour_id: Optional[str] = None,
        handlers: Optional[HandlersType] = None,
        expected_content: Optional[ExpectedContentType] = None,
        expected_types: Optional[ExpectedTypesType] = None,
        fail_send_a2a: bool = False,
        mining_interval_secs: float = 0) -> Tuple[Optional[Message], ...]
```

Process n message cycles.

**Arguments**:

- `behaviour_id`: the behaviour to fast forward to
- `ncycles`: the number of message cycles to process
- `synchronized_data`: a synchronized_data
- `handlers`: a list of handlers
- `expected_content`: the expected_content
- `expected_types`: the expected type
- `fail_send_a2a`: flag that indicates whether we want to simulate a failure in the `send_a2a_transaction`
- `mining_interval_secs`: the mining interval used in the tests.

**Returns**:

tuple of incoming messages

<a id="packages.valory.skills.abstract_round_abci.test_tools.integration.HardHatHelperIntegration"></a>

## HardHatHelperIntegration Objects

```python
class HardHatHelperIntegration(IntegrationBaseCase, ABC)
```

Base test class for integration tests with HardHat provider.

<a id="packages.valory.skills.abstract_round_abci.test_tools.integration.HardHatHelperIntegration.setup_class"></a>

#### setup`_`class

```python
@classmethod
def setup_class(cls, **kwargs: Any) -> None
```

Setup.

