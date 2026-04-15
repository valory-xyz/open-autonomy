<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers"></a>

# packages.valory.skills.abstract`_`round`_`abci.tests.test`_`handlers

Test the handlers.py module of the skill.

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.test_exception_to_info_msg"></a>

#### test`_`exception`_`to`_`info`_`msg

```python
def test_exception_to_info_msg() -> None
```

Test 'exception_to_info_msg' helper function.

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.TestABCIRoundHandler"></a>

## TestABCIRoundHandler Objects

```python
class TestABCIRoundHandler()
```

Test 'ABCIRoundHandler'.

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.TestABCIRoundHandler.setup_method"></a>

#### setup`_`method

```python
def setup_method() -> None
```

Set up the tests.

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.TestABCIRoundHandler.test_info"></a>

#### test`_`info

```python
def test_info() -> None
```

Test the 'info' handler method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.TestABCIRoundHandler.test_init_chain"></a>

#### test`_`init`_`chain

```python
@pytest.mark.parametrize("app_hash", (b"", b"test"))
def test_init_chain(app_hash: bytes) -> None
```

Test the 'init_chain' handler method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.TestABCIRoundHandler.test_begin_block"></a>

#### test`_`begin`_`block

```python
def test_begin_block() -> None
```

Test the 'begin_block' handler method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.TestABCIRoundHandler.test_check_tx"></a>

#### test`_`check`_`tx

```python
@mock.patch.object(handlers, "Transaction")
def test_check_tx(*_: Any) -> None
```

Test the 'check_tx' handler method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.TestABCIRoundHandler.test_check_tx_negative"></a>

#### test`_`check`_`tx`_`negative

```python
@mock.patch.object(
    Transaction,
    "decode",
    side_effect=SignatureNotValidError,
)
def test_check_tx_negative(*_: Any) -> None
```

Test the 'check_tx' handler method, negative case.

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.TestABCIRoundHandler.test_deliver_tx"></a>

#### test`_`deliver`_`tx

```python
@mock.patch.object(handlers, "Transaction")
def test_deliver_tx(*_: Any) -> None
```

Test the 'deliver_tx' handler method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.TestABCIRoundHandler.test_deliver_tx_negative"></a>

#### test`_`deliver`_`tx`_`negative

```python
@mock.patch.object(
    Transaction,
    "decode",
    side_effect=SignatureNotValidError,
)
def test_deliver_tx_negative(*_: Any) -> None
```

Test the 'deliver_tx' handler method, negative case.

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.TestABCIRoundHandler.test_deliver_bad_tx"></a>

#### test`_`deliver`_`bad`_`tx

```python
@mock.patch.object(handlers, "Transaction")
def test_deliver_bad_tx(*_: Any) -> None
```

Test the 'deliver_tx' handler method, when the transaction is not ok.

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.TestABCIRoundHandler.test_end_block"></a>

#### test`_`end`_`block

```python
@pytest.mark.parametrize("request_height", tuple(range(3)))
def test_end_block(request_height: int) -> None
```

Test the 'end_block' handler method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.TestABCIRoundHandler.test_commit"></a>

#### test`_`commit

```python
def test_commit() -> None
```

Test the 'commit' handler method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.TestABCIRoundHandler.test_commit_negative"></a>

#### test`_`commit`_`negative

```python
def test_commit_negative() -> None
```

Test the 'commit' handler method, negative case.

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.ConcreteResponseHandler"></a>

## ConcreteResponseHandler Objects

```python
class ConcreteResponseHandler(AbstractResponseHandler)
```

A concrete response handler for testing purposes.

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.TestAbstractResponseHandler"></a>

## TestAbstractResponseHandler Objects

```python
class TestAbstractResponseHandler()
```

Test 'AbstractResponseHandler'.

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.TestAbstractResponseHandler.setup_method"></a>

#### setup`_`method

```python
def setup_method() -> None
```

Set up the tests.

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.TestAbstractResponseHandler.test_handle"></a>

#### test`_`handle

```python
def test_handle() -> None
```

Test the 'handle' method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.TestAbstractResponseHandler.test_handle_negative_cannot_recover_dialogues"></a>

#### test`_`handle`_`negative`_`cannot`_`recover`_`dialogues

```python
@mock.patch.object(AbstractResponseHandler,
                   "_recover_protocol_dialogues",
                   return_value=None)
def test_handle_negative_cannot_recover_dialogues(*_: Any) -> None
```

Test the 'handle' method, negative case (cannot recover dialogues).

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.TestAbstractResponseHandler.test_handle_negative_cannot_update_dialogues"></a>

#### test`_`handle`_`negative`_`cannot`_`update`_`dialogues

```python
@mock.patch.object(AbstractResponseHandler, "_recover_protocol_dialogues")
def test_handle_negative_cannot_update_dialogues(
        mock_dialogues_fn: Any) -> None
```

Test the 'handle' method, negative case (cannot update dialogues).

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.TestAbstractResponseHandler.test_handle_negative_performative_not_allowed"></a>

#### test`_`handle`_`negative`_`performative`_`not`_`allowed

```python
def test_handle_negative_performative_not_allowed() -> None
```

Test the 'handle' method, negative case (performative not allowed).

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.TestAbstractResponseHandler.test_handle_negative_cannot_find_callback"></a>

#### test`_`handle`_`negative`_`cannot`_`find`_`callback

```python
def test_handle_negative_cannot_find_callback() -> None
```

Test the 'handle' method, negative case (cannot find callback).

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.TestTendermintHandler"></a>

## TestTendermintHandler Objects

```python
class TestTendermintHandler()
```

Test Tendermint Handler

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.TestTendermintHandler.setup_method"></a>

#### setup`_`method

```python
def setup_method() -> None
```

Set up the tests.

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.TestTendermintHandler.dummy_validator_config"></a>

#### dummy`_`validator`_`config

```python
@property
def dummy_validator_config() -> Dict[str, Dict[str, str]]
```

Dummy validator config

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.TestTendermintHandler.make_error_message"></a>

#### make`_`error`_`message

```python
@staticmethod
def make_error_message() -> TendermintMessage
```

Make dummy error message

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.TestTendermintHandler.test_handle_unidentified_tendermint_dialogue"></a>

#### test`_`handle`_`unidentified`_`tendermint`_`dialogue

```python
def test_handle_unidentified_tendermint_dialogue(
        caplog: LogCaptureFixture) -> None
```

Test unidentified tendermint dialogue

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.TestTendermintHandler.test_handle_no_addresses_retrieved_yet"></a>

#### test`_`handle`_`no`_`addresses`_`retrieved`_`yet

```python
def test_handle_no_addresses_retrieved_yet(caplog: LogCaptureFixture) -> None
```

Test handle request no registered addresses

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.TestTendermintHandler.test_handle_not_in_registered_addresses"></a>

#### test`_`handle`_`not`_`in`_`registered`_`addresses

```python
def test_handle_not_in_registered_addresses(caplog: LogCaptureFixture) -> None
```

Test handle response sender not in registered addresses

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.TestTendermintHandler.test_handle_get_genesis_info"></a>

#### test`_`handle`_`get`_`genesis`_`info

```python
def test_handle_get_genesis_info(caplog: LogCaptureFixture) -> None
```

Test handle request for genesis info

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.TestTendermintHandler.test_handle_response_invalid_addresses"></a>

#### test`_`handle`_`response`_`invalid`_`addresses

```python
def test_handle_response_invalid_addresses(caplog: LogCaptureFixture) -> None
```

Test handle response for genesis info with invalid address.

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.TestTendermintHandler.test_handle_genesis_info"></a>

#### test`_`handle`_`genesis`_`info

```python
def test_handle_genesis_info(caplog: LogCaptureFixture) -> None
```

Test handle response for genesis info with valid address

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.TestTendermintHandler.test_recovery_params"></a>

#### test`_`recovery`_`params

```python
@pytest.mark.parametrize("registered", (True, False))
@pytest.mark.parametrize(
    "performative",
    (
        TendermintMessage.Performative.RECOVERY_PARAMS,
        TendermintMessage.Performative.GET_RECOVERY_PARAMS,
    ),
)
def test_recovery_params(registered: bool,
                         performative: TendermintMessage.Performative,
                         caplog: LogCaptureFixture) -> None
```

Test handle response for recovery parameters.

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.TestTendermintHandler.test_recovery_params_error"></a>

#### test`_`recovery`_`params`_`error

```python
@pytest.mark.parametrize(
    "side_effect, expected_exception",
    (
        (
            json.decoder.JSONDecodeError("", "", 0),
            ": line 1 column 1 (char 0)",
        ),
        (
            {"not a dict"},
            "argument after ** must be a mapping, not str",
        ),
    ),
)
def test_recovery_params_error(side_effect: Any, expected_exception: str,
                               caplog: LogCaptureFixture) -> None
```

Test handle response for recovery parameters.

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.TestTendermintHandler.test_handle_error"></a>

#### test`_`handle`_`error

```python
def test_handle_error(caplog: LogCaptureFixture) -> None
```

Test handle error

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.TestTendermintHandler.test_handle_error_no_target_message_retrieved"></a>

#### test`_`handle`_`error`_`no`_`target`_`message`_`retrieved

```python
def test_handle_error_no_target_message_retrieved(
        caplog: LogCaptureFixture) -> None
```

Test handle error no target message retrieved

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.TestTendermintHandler.test_handle_performative_not_recognized"></a>

#### test`_`handle`_`performative`_`not`_`recognized

```python
def test_handle_performative_not_recognized(caplog: LogCaptureFixture) -> None
```

Test performative no recognized

<a id="packages.valory.skills.abstract_round_abci.tests.test_handlers.TestTendermintHandler.test_sender_not_in_registered_addresses"></a>

#### test`_`sender`_`not`_`in`_`registered`_`addresses

```python
def test_sender_not_in_registered_addresses(caplog: LogCaptureFixture) -> None
```

Test sender not in registered addresses.

