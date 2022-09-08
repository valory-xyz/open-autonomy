<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils"></a>

# packages.valory.skills.abstract`_`round`_`abci.tests.test`_`behaviours`_`utils

Test the behaviours_utils.py module of the skill.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.hypothesis_cleanup"></a>

#### hypothesis`_`cleanup

```python
@pytest.fixture(scope="session", autouse=True)
def hypothesis_cleanup() -> Generator
```

Fixture to remove hypothesis directory after tests.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.yield_and_return_bool_wrapper"></a>

#### yield`_`and`_`return`_`bool`_`wrapper

```python
def yield_and_return_bool_wrapper(flag_value: bool) -> Callable[[], Generator[None, None, Optional[bool]]]
```

Wrapper for a Dummy generator that returns a `bool`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.AsyncBehaviourTest"></a>

## AsyncBehaviourTest Objects

```python
class AsyncBehaviourTest(AsyncBehaviour,  ABC)
```

Concrete AsyncBehaviour class for testing purposes.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.AsyncBehaviourTest.async_act_wrapper"></a>

#### async`_`act`_`wrapper

```python
def async_act_wrapper() -> Generator
```

Do async act wrapper. Forwards to 'async_act'.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.AsyncBehaviourTest.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Do 'async_act'.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.async_behaviour_initial_state_is_ready"></a>

#### async`_`behaviour`_`initial`_`state`_`is`_`ready

```python
def async_behaviour_initial_state_is_ready() -> None
```

Check that the initial async state is "READY".

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.test_async_behaviour_ticks"></a>

#### test`_`async`_`behaviour`_`ticks

```python
def test_async_behaviour_ticks() -> None
```

Test "AsyncBehaviour", only ticks.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.test_async_behaviour_wait_for_message"></a>

#### test`_`async`_`behaviour`_`wait`_`for`_`message

```python
def test_async_behaviour_wait_for_message() -> None
```

Test 'wait_for_message'.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.test_async_behaviour_wait_for_message_raises_timeout_exception"></a>

#### test`_`async`_`behaviour`_`wait`_`for`_`message`_`raises`_`timeout`_`exception

```python
def test_async_behaviour_wait_for_message_raises_timeout_exception() -> None
```

Test 'wait_for_message' when it raises TimeoutException.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.test_async_behaviour_wait_for_condition"></a>

#### test`_`async`_`behaviour`_`wait`_`for`_`condition

```python
def test_async_behaviour_wait_for_condition() -> None
```

Test 'wait_for_condition' method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.test_async_behaviour_wait_for_condition_with_timeout"></a>

#### test`_`async`_`behaviour`_`wait`_`for`_`condition`_`with`_`timeout

```python
def test_async_behaviour_wait_for_condition_with_timeout() -> None
```

Test 'wait_for_condition' method with timeout expired.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.test_async_behaviour_sleep"></a>

#### test`_`async`_`behaviour`_`sleep

```python
def test_async_behaviour_sleep() -> None
```

Test 'sleep' method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.test_async_behaviour_without_yield"></a>

#### test`_`async`_`behaviour`_`without`_`yield

```python
def test_async_behaviour_without_yield() -> None
```

Test AsyncBehaviour, async_act without yield/yield from.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.test_async_behaviour_raise_stopiteration"></a>

#### test`_`async`_`behaviour`_`raise`_`stopiteration

```python
def test_async_behaviour_raise_stopiteration() -> None
```

Test AsyncBehaviour, async_act raising 'StopIteration'.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.test_async_behaviour_stop"></a>

#### test`_`async`_`behaviour`_`stop

```python
def test_async_behaviour_stop() -> None
```

Test AsyncBehaviour.stop method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.RoundA"></a>

## RoundA Objects

```python
class RoundA(AbstractRound)
```

Concrete ABCI round.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.RoundA.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BaseSynchronizedData, Enum]]
```

Handle end block.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.RoundA.check_payload"></a>

#### check`_`payload

```python
def check_payload(payload: BaseTxPayload) -> None
```

Check payload.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.RoundA.process_payload"></a>

#### process`_`payload

```python
def process_payload(payload: BaseTxPayload) -> None
```

Process payload.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.BehaviourATest"></a>

## BehaviourATest Objects

```python
class BehaviourATest(BaseBehaviour)
```

Concrete BaseBehaviour class.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.BehaviourATest.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Do the 'async_act'.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour"></a>

## TestBaseBehaviour Objects

```python
class TestBaseBehaviour()
```

Tests for the 'BaseBehaviour' class.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.setup"></a>

#### setup

```python
def setup() -> None
```

Set up the tests.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_params_property"></a>

#### test`_`params`_`property

```python
def test_params_property() -> None
```

Test the 'params' property.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_synchronized_data_property"></a>

#### test`_`synchronized`_`data`_`property

```python
def test_synchronized_data_property() -> None
```

Test the 'synchronized_data' property.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_check_in_round"></a>

#### test`_`check`_`in`_`round

```python
def test_check_in_round() -> None
```

Test 'BaseBehaviour' initialization.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_check_in_last_round"></a>

#### test`_`check`_`in`_`last`_`round

```python
def test_check_in_last_round() -> None
```

Test 'BaseBehaviour' initialization.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_check_round_height_has_changed"></a>

#### test`_`check`_`round`_`height`_`has`_`changed

```python
def test_check_round_height_has_changed() -> None
```

Test 'check_round_height_has_changed'.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_wait_until_round_end_negative_last_round_or_matching_round"></a>

#### test`_`wait`_`until`_`round`_`end`_`negative`_`last`_`round`_`or`_`matching`_`round

```python
def test_wait_until_round_end_negative_last_round_or_matching_round() -> None
```

Test 'wait_until_round_end' method, negative case (not in matching nor last round).

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_wait_until_round_end_positive"></a>

#### test`_`wait`_`until`_`round`_`end`_`positive

```python
@mock.patch.object(BaseBehaviour, "wait_for_condition")
@mock.patch.object(BaseBehaviour, "check_not_in_round", return_value=False)
@mock.patch.object(BaseBehaviour, "check_not_in_last_round", return_value=False)
def test_wait_until_round_end_positive(*_: Any) -> None
```

Test 'wait_until_round_end' method, positive case.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_wait_from_last_timestamp"></a>

#### test`_`wait`_`from`_`last`_`timestamp

```python
def test_wait_from_last_timestamp() -> None
```

Test 'wait_from_last_timestamp'.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_wait_from_last_timestamp_negative"></a>

#### test`_`wait`_`from`_`last`_`timestamp`_`negative

```python
def test_wait_from_last_timestamp_negative() -> None
```

Test 'wait_from_last_timestamp'.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_set_done"></a>

#### test`_`set`_`done

```python
def test_set_done() -> None
```

Test 'set_done' method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_send_a2a_transaction_positive"></a>

#### test`_`send`_`a2a`_`transaction`_`positive

```python
@mock.patch.object(BaseBehaviour, "_send_transaction")
def test_send_a2a_transaction_positive(*_: Any) -> None
```

Test 'send_a2a_transaction' method, positive case.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test__check_tm_communication"></a>

#### test`__`check`_`tm`_`communication

```python
@mock.patch.object(
        BaseBehaviour,
        "tm_communication_unhealthy",
        new_callable=mock.PropertyMock,
        return_value=True,
    )
@pytest.mark.parametrize("tm_reset_success", (True, False))
def test__check_tm_communication(_: mock._patch, tm_reset_success: bool) -> None
```

Test `__check_tm_communication`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_async_act_wrapper_communication"></a>

#### test`_`async`_`act`_`wrapper`_`communication

```python
@pytest.mark.parametrize("communication_is_healthy", (True, False))
def test_async_act_wrapper_communication(communication_is_healthy: bool) -> None
```

Test 'async_act_wrapper' when tm communication is unhealthy.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_sync_state"></a>

#### test`_`sync`_`state

```python
def test_sync_state() -> None
```

Test `_sync_state`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_async_act_wrapper_agent_sync_mode"></a>

#### test`_`async`_`act`_`wrapper`_`agent`_`sync`_`mode

```python
@pytest.mark.parametrize(
        "expected_round_count, expected_reset_index",
        ((None, None), (0, 0), (123, 4), (235235, 754)),
    )
@mock.patch.object(
        BehaviourATest,
        "_BaseBehaviour__check_tm_communication",
        side_effect=yield_and_return_bool_wrapper(True),
    )
def test_async_act_wrapper_agent_sync_mode(_: mock._patch, expected_round_count: Optional[int], expected_reset_index: Optional[int]) -> None
```

Test 'async_act_wrapper' in sync mode.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_async_act_wrapper_agent_sync_mode_where_height_dont_match"></a>

#### test`_`async`_`act`_`wrapper`_`agent`_`sync`_`mode`_`where`_`height`_`dont`_`match

```python
@mock.patch.object(BaseBehaviour, "_get_status", _get_status_wrong_patch)
def test_async_act_wrapper_agent_sync_mode_where_height_dont_match() -> None
```

Test 'async_act_wrapper' in sync mode.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_async_act_wrapper_exception"></a>

#### test`_`async`_`act`_`wrapper`_`exception

```python
@mock.patch.object(
        BehaviourATest,
        "_BaseBehaviour__check_tm_communication",
        side_effect=yield_and_return_bool_wrapper(True),
    )
@pytest.mark.parametrize("exception_cls", [StopIteration])
def test_async_act_wrapper_exception(_: mock._patch, exception_cls: Exception) -> None
```

Test 'async_act_wrapper'.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_get_request_nonce_from_dialogue"></a>

#### test`_`get`_`request`_`nonce`_`from`_`dialogue

```python
def test_get_request_nonce_from_dialogue() -> None
```

Test '_get_request_nonce_from_dialogue' helper method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_send_transaction_stop_condition"></a>

#### test`_`send`_`transaction`_`stop`_`condition

```python
@mock.patch.object(BaseBehaviour, "_send_signing_request")
@mock.patch.object(Transaction, "encode", return_value=MagicMock())
@mock.patch.object(
        BaseBehaviour,
        "_build_http_request_message",
        return_value=(MagicMock(), MagicMock()),
    )
@mock.patch.object(BaseBehaviour, "_check_http_return_code_200", return_value=False)
def test_send_transaction_stop_condition(*_: Any) -> None
```

Test '_send_transaction' method's `stop_condition` as provided by `send_a2a_transaction`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_send_transaction_positive_false_condition"></a>

#### test`_`send`_`transaction`_`positive`_`false`_`condition

```python
def test_send_transaction_positive_false_condition() -> None
```

Test '_send_transaction', positive case (false condition)

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_send_transaction_positive"></a>

#### test`_`send`_`transaction`_`positive

```python
@mock.patch.object(BaseBehaviour, "_send_signing_request")
@mock.patch.object(Transaction, "encode", return_value=MagicMock())
@mock.patch.object(
        BaseBehaviour,
        "_build_http_request_message",
        return_value=(MagicMock(), MagicMock()),
    )
@mock.patch.object(BaseBehaviour, "_check_http_return_code_200", return_value=True)
def test_send_transaction_positive(*_: Any) -> None
```

Test '_send_transaction', positive case.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_send_transaction_invalid_transaction"></a>

#### test`_`send`_`transaction`_`invalid`_`transaction

```python
@mock.patch.object(BaseBehaviour, "_send_signing_request")
@mock.patch.object(Transaction, "encode", return_value=MagicMock())
@mock.patch.object(
        BaseBehaviour,
        "_build_http_request_message",
        return_value=(MagicMock(), MagicMock()),
    )
@mock.patch.object(BaseBehaviour, "_check_http_return_code_200", return_value=True)
@mock.patch.object(
        BaseBehaviour,
        "_wait_until_transaction_delivered",
        new=_wait_until_transaction_delivered_patch,
    )
def test_send_transaction_invalid_transaction(*_: Any) -> None
```

Test '_send_transaction', positive case.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_send_transaction_valid_transaction"></a>

#### test`_`send`_`transaction`_`valid`_`transaction

```python
@mock.patch.object(BaseBehaviour, "_send_signing_request")
@mock.patch.object(BaseBehaviour, "_is_invalid_transaction", return_value=False)
@mock.patch.object(BaseBehaviour, "_tx_not_found", return_value=True)
@mock.patch.object(Transaction, "encode", return_value=MagicMock())
@mock.patch.object(
        BaseBehaviour,
        "_build_http_request_message",
        return_value=(MagicMock(), MagicMock()),
    )
@mock.patch.object(BaseBehaviour, "_check_http_return_code_200", return_value=True)
@mock.patch.object(
        BaseBehaviour,
        "_wait_until_transaction_delivered",
        new=_wait_until_transaction_delivered_patch,
    )
def test_send_transaction_valid_transaction(*_: Any) -> None
```

Test '_send_transaction', positive case.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_tx_not_found"></a>

#### test`_`tx`_`not`_`found

```python
def test_tx_not_found(*_: Any) -> None
```

Test _tx_not_found

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_send_transaction_signing_error"></a>

#### test`_`send`_`transaction`_`signing`_`error

```python
@mock.patch.object(BaseBehaviour, "_send_signing_request")
def test_send_transaction_signing_error(*_: Any) -> None
```

Test '_send_transaction', signing error.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_send_transaction_timeout_exception_submit_tx"></a>

#### test`_`send`_`transaction`_`timeout`_`exception`_`submit`_`tx

```python
@mock.patch.object(BaseBehaviour, "_send_signing_request")
@mock.patch.object(Transaction, "encode", return_value=MagicMock())
@mock.patch.object(
        BaseBehaviour,
        "_build_http_request_message",
        return_value=(MagicMock(), MagicMock()),
    )
def test_send_transaction_timeout_exception_submit_tx(*_: Any) -> None
```

Test '_send_transaction', timeout exception.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_send_transaction_timeout_exception_wait_until_transaction_delivered"></a>

#### test`_`send`_`transaction`_`timeout`_`exception`_`wait`_`until`_`transaction`_`delivered

```python
@mock.patch.object(BaseBehaviour, "_send_signing_request")
@mock.patch.object(Transaction, "encode", return_value=MagicMock())
@mock.patch.object(
        BaseBehaviour,
        "_build_http_request_message",
        return_value=(MagicMock(), MagicMock()),
    )
@mock.patch.object(BaseBehaviour, "_check_http_return_code_200", return_value=True)
def test_send_transaction_timeout_exception_wait_until_transaction_delivered(*_: Any) -> None
```

Test '_send_transaction', timeout exception.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_send_transaction_transaction_not_delivered"></a>

#### test`_`send`_`transaction`_`transaction`_`not`_`delivered

```python
@mock.patch.object(BaseBehaviour, "_send_signing_request")
@mock.patch.object(Transaction, "encode", return_value=MagicMock())
@mock.patch.object(
        BaseBehaviour,
        "_build_http_request_message",
        return_value=(MagicMock(), MagicMock()),
    )
@mock.patch.object(BaseBehaviour, "_check_http_return_code_200", return_value=True)
def test_send_transaction_transaction_not_delivered(*_: Any) -> None
```

Test '_send_transaction', timeout exception.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_send_transaction_wrong_ok_code"></a>

#### test`_`send`_`transaction`_`wrong`_`ok`_`code

```python
@mock.patch.object(BaseBehaviour, "_send_signing_request")
@mock.patch.object(Transaction, "encode", return_value=MagicMock())
@mock.patch.object(
        BaseBehaviour,
        "_build_http_request_message",
        return_value=(MagicMock(), MagicMock()),
    )
@mock.patch.object(BaseBehaviour, "_check_http_return_code_200", return_value=True)
def test_send_transaction_wrong_ok_code(*_: Any) -> None
```

Test '_send_transaction', positive case.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_send_transaction_wait_delivery_timeout_exception"></a>

#### test`_`send`_`transaction`_`wait`_`delivery`_`timeout`_`exception

```python
@pytest.mark.skip
@mock.patch.object(BaseBehaviour, "_send_signing_request")
@mock.patch.object(Transaction, "encode", return_value=MagicMock())
@mock.patch.object(
        BaseBehaviour,
        "_build_http_request_message",
        return_value=(MagicMock(), MagicMock()),
    )
@mock.patch.object(
        BaseBehaviour,
        "_check_http_return_code_200",
        return_value=True,
    )
@mock.patch("json.loads")
def test_send_transaction_wait_delivery_timeout_exception(*_: Any) -> None
```

Test '_send_transaction', timeout exception on tx delivery.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_send_transaction_error_status_code"></a>

#### test`_`send`_`transaction`_`error`_`status`_`code

```python
@pytest.mark.parametrize("resetting", (True, False))
@pytest.mark.parametrize(
        "non_200_count",
        (
            0,
            NON_200_RETURN_CODE_DURING_RESET_THRESHOLD,
            NON_200_RETURN_CODE_DURING_RESET_THRESHOLD + 1,
        ),
    )
@mock.patch.object(BaseBehaviour, "_send_signing_request")
@mock.patch.object(Transaction, "encode", return_value=MagicMock())
@mock.patch.object(
        BaseBehaviour,
        "_build_http_request_message",
        return_value=(MagicMock(), MagicMock()),
    )
@mock.patch("json.loads")
def test_send_transaction_error_status_code(_: Any, __: Any, ___: Any, ____: Any, resetting: bool, non_200_count: int) -> None
```

Test '_send_transaction', error status code.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_send_signing_request"></a>

#### test`_`send`_`signing`_`request

```python
@mock.patch.object(BaseBehaviour, "_get_request_nonce_from_dialogue")
@mock.patch.object(behaviour_utils, "RawMessage")
@mock.patch.object(behaviour_utils, "Terms")
def test_send_signing_request(*_: Any) -> None
```

Test '_send_signing_request'.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_fuzz_send_signing_request"></a>

#### test`_`fuzz`_`send`_`signing`_`request

```python
@pytest.mark.skip
def test_fuzz_send_signing_request() -> None
```

Test '_send_signing_request'.

Do not run this test through pytest. Add the following lines at the bottom
of the file and run it as a script:
t = TestBaseBehaviour()
t.setup()
t.test_fuzz_send_signing_request()

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_send_transaction_signing_request"></a>

#### test`_`send`_`transaction`_`signing`_`request

```python
@mock.patch.object(BaseBehaviour, "_get_request_nonce_from_dialogue")
@mock.patch.object(behaviour_utils, "RawMessage")
@mock.patch.object(behaviour_utils, "Terms")
def test_send_transaction_signing_request(*_: Any) -> None
```

Test '_send_signing_request'.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_send_transaction_request"></a>

#### test`_`send`_`transaction`_`request

```python
def test_send_transaction_request() -> None
```

Test '_send_transaction_request'.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_send_transaction_receipt_request"></a>

#### test`_`send`_`transaction`_`receipt`_`request

```python
def test_send_transaction_receipt_request() -> None
```

Test '_send_transaction_receipt_request'.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_build_http_request_message"></a>

#### test`_`build`_`http`_`request`_`message

```python
def test_build_http_request_message(*_: Any) -> None
```

Test '_build_http_request_message'.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_wait_until_transaction_delivered"></a>

#### test`_`wait`_`until`_`transaction`_`delivered

```python
@mock.patch.object(Transaction, "encode", return_value=MagicMock())
@mock.patch.object(
        BaseBehaviour,
        "_build_http_request_message",
        return_value=(MagicMock(), MagicMock()),
    )
@mock.patch.object(BaseBehaviour, "_check_http_return_code_200", return_value=True)
@mock.patch.object(BaseBehaviour, "sleep")
@mock.patch("json.loads")
def test_wait_until_transaction_delivered(*_: Any) -> None
```

Test '_wait_until_transaction_delivered' method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_wait_until_transaction_delivered_failed"></a>

#### test`_`wait`_`until`_`transaction`_`delivered`_`failed

```python
@mock.patch.object(Transaction, "encode", return_value=MagicMock())
@mock.patch.object(
        BaseBehaviour,
        "_build_http_request_message",
        return_value=(MagicMock(), MagicMock()),
    )
@mock.patch.object(BaseBehaviour, "_check_http_return_code_200", return_value=True)
@mock.patch.object(BaseBehaviour, "sleep")
@mock.patch("json.loads")
def test_wait_until_transaction_delivered_failed(*_: Any) -> None
```

Test '_wait_until_transaction_delivered' method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_wait_until_transaction_delivered_raises_timeout"></a>

#### test`_`wait`_`until`_`transaction`_`delivered`_`raises`_`timeout

```python
def test_wait_until_transaction_delivered_raises_timeout(*_: Any) -> None
```

Test '_wait_until_transaction_delivered' method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_get_default_terms"></a>

#### test`_`get`_`default`_`terms

```python
@mock.patch.object(behaviour_utils, "Terms")
def test_get_default_terms(*_: Any) -> None
```

Test '_get_default_terms'.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_send_raw_transaction"></a>

#### test`_`send`_`raw`_`transaction

```python
@mock.patch.object(BaseBehaviour, "_send_transaction_signing_request")
@mock.patch.object(BaseBehaviour, "_send_transaction_request")
@mock.patch.object(BaseBehaviour, "_send_transaction_receipt_request")
@mock.patch.object(behaviour_utils, "Terms")
def test_send_raw_transaction(*_: Any) -> None
```

Test 'send_raw_transaction'.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_send_raw_transaction_with_wrong_signing_performative"></a>

#### test`_`send`_`raw`_`transaction`_`with`_`wrong`_`signing`_`performative

```python
@mock.patch.object(BaseBehaviour, "_send_transaction_signing_request")
@mock.patch.object(BaseBehaviour, "_send_transaction_request")
@mock.patch.object(BaseBehaviour, "_send_transaction_receipt_request")
@mock.patch.object(behaviour_utils, "Terms")
def test_send_raw_transaction_with_wrong_signing_performative(*_: Any) -> None
```

Test 'send_raw_transaction'.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_send_raw_transaction_errors"></a>

#### test`_`send`_`raw`_`transaction`_`errors

```python
@pytest.mark.parametrize(
        "message, expected_rpc_status",
        (
            ("replacement transaction underpriced", RPCResponseStatus.UNDERPRICED),
            ("nonce too low", RPCResponseStatus.INCORRECT_NONCE),
            ("insufficient funds", RPCResponseStatus.INSUFFICIENT_FUNDS),
            ("already known", RPCResponseStatus.ALREADY_KNOWN),
            ("test", RPCResponseStatus.UNCLASSIFIED_ERROR),
        ),
    )
@mock.patch.object(BaseBehaviour, "_send_transaction_signing_request")
@mock.patch.object(BaseBehaviour, "_send_transaction_request")
@mock.patch.object(BaseBehaviour, "_send_transaction_receipt_request")
@mock.patch.object(behaviour_utils, "Terms")
def test_send_raw_transaction_errors(_: Any, __: Any, ___: Any, ____: Any, message: str, expected_rpc_status: RPCResponseStatus) -> None
```

Test 'send_raw_transaction'.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_send_raw_transaction_hashes_mismatch"></a>

#### test`_`send`_`raw`_`transaction`_`hashes`_`mismatch

```python
@mock.patch.object(BaseBehaviour, "_send_transaction_signing_request")
@mock.patch.object(BaseBehaviour, "_send_transaction_request")
@mock.patch.object(BaseBehaviour, "_send_transaction_receipt_request")
@mock.patch.object(behaviour_utils, "Terms")
def test_send_raw_transaction_hashes_mismatch(*_: Any) -> None
```

Test 'send_raw_transaction' when signature and tx responses' hashes mismatch.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_get_contract_api_response"></a>

#### test`_`get`_`contract`_`api`_`response

```python
@pytest.mark.parametrize("contract_address", [None, "contract_address"])
def test_get_contract_api_response(contract_address: Optional[str]) -> None
```

Test 'get_contract_api_response'.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_get_status"></a>

#### test`_`get`_`status

```python
@mock.patch.object(
        BaseBehaviour, "_build_http_request_message", return_value=(None, None)
    )
def test_get_status(_: mock.Mock) -> None
```

Test '_get_status'.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_default_callback_request_stopped"></a>

#### test`_`default`_`callback`_`request`_`stopped

```python
def test_default_callback_request_stopped() -> None
```

Test 'default_callback_request' when stopped.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_default_callback_late_arriving_message"></a>

#### test`_`default`_`callback`_`late`_`arriving`_`message

```python
def test_default_callback_late_arriving_message(*_: Any) -> None
```

Test 'default_callback_request' when a message arrives late.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_default_callback_request_waiting_message"></a>

#### test`_`default`_`callback`_`request`_`waiting`_`message

```python
def test_default_callback_request_waiting_message(*_: Any) -> None
```

Test 'default_callback_request' when waiting message.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_default_callback_request_else"></a>

#### test`_`default`_`callback`_`request`_`else

```python
def test_default_callback_request_else(*_: Any) -> None
```

Test 'default_callback_request' else branch.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_stop"></a>

#### test`_`stop

```python
def test_stop() -> None
```

Test the stop method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.dummy_sleep"></a>

#### dummy`_`sleep

```python
@staticmethod
def dummy_sleep(*_: Any) -> Generator[None, None, None]
```

Dummy `sleep` method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_start_reset"></a>

#### test`_`start`_`reset

```python
def test_start_reset() -> None
```

Test the `_start_reset` method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_end_reset"></a>

#### test`_`end`_`reset

```python
def test_end_reset() -> None
```

Test the `_end_reset` method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_is_timeout_expired"></a>

#### test`_`is`_`timeout`_`expired

```python
@pytest.mark.parametrize(
        "check_started, is_healthy, timeout, expiration_expected",
        (
            (None, True, 0, False),
            (None, False, 0, False),
            (datetime(1, 1, 1), True, 0, False),
            (datetime.now(), False, 3000, False),
            (datetime(1, 1, 1), False, 0, True),
        ),
    )
def test_is_timeout_expired(check_started: Optional[datetime], is_healthy: bool, timeout: float, expiration_expected: bool) -> None
```

Test the `_is_timeout_expired` method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_get_reset_params"></a>

#### test`_`get`_`reset`_`params

```python
@pytest.mark.parametrize("default", (True, False))
@given(st.datetimes(), st.integers(), st.integers())
def test_get_reset_params(default: bool, timestamp: datetime, height: int, interval: int) -> None
```

Test `_get_reset_params` method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_reset_tendermint_with_wait_timeout_expired"></a>

#### test`_`reset`_`tendermint`_`with`_`wait`_`timeout`_`expired

```python
@mock.patch.object(BaseBehaviour, "_start_reset")
@mock.patch.object(BaseBehaviour, "_is_timeout_expired")
def test_reset_tendermint_with_wait_timeout_expired(*_: mock.Mock) -> None
```

Test tendermint reset.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_reset_tendermint_with_wait"></a>

#### test`_`reset`_`tendermint`_`with`_`wait

```python
@mock.patch.object(BaseBehaviour, "_start_reset")
@mock.patch.object(
        BaseBehaviour, "_build_http_request_message", return_value=(None, None)
    )
@pytest.mark.parametrize(
        "reset_response, status_response, local_height, n_iter, expecting_success",
        (
            (
                {"message": "Tendermint reset was successful.", "status": True},
                {"result": {"sync_info": {"latest_block_height": 1}}},
                1,
                3,
                True,
            ),
            (
                {"message": "Tendermint reset was successful.", "status": True},
                {"result": {"sync_info": {"latest_block_height": 1}}},
                3,
                3,
                False,
            ),
            (
                {"message": "Error resetting tendermint.", "status": False},
                {},
                0,
                2,
                False,
            ),
            ("wrong_response", {}, 0, 2, False),
            (
                {"message": "Reset Successful.", "status": True},
                "not_accepting_txs_yet",
                0,
                3,
                False,
            ),
        ),
    )
def test_reset_tendermint_with_wait(build_http_request_message_mock: mock.Mock, _start_reset: mock.Mock, reset_response: Union[Dict[str, Union[bool, str]], str], status_response: Union[Dict[str, Union[int, str]], str], local_height: int, n_iter: int, expecting_success: bool) -> None
```

Test tendermint reset.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.TestBaseBehaviour.test_fuzz_submit_tx"></a>

#### test`_`fuzz`_`submit`_`tx

```python
@pytest.mark.skip
def test_fuzz_submit_tx() -> None
```

Test '_submit_tx'.

Do not run this test through pytest. Add the following lines at the bottom
of the file and run it as a script:
t = TestBaseBehaviour()
t.setup()
t.test_fuzz_submit_tx()

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.test_degenerate_behaviour_async_act"></a>

#### test`_`degenerate`_`behaviour`_`async`_`act

```python
@mock.patch.object(
    DegenerateBehaviour,
    "_BaseBehaviour__check_tm_communication",
    side_effect=yield_and_return_bool_wrapper(True),
)
def test_degenerate_behaviour_async_act(_: mock._patch) -> None
```

Test DegenerateBehaviour.async_act.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours_utils.test_make_degenerate_behaviour"></a>

#### test`_`make`_`degenerate`_`behaviour

```python
def test_make_degenerate_behaviour() -> None
```

Test 'make_degenerate_behaviour'.

