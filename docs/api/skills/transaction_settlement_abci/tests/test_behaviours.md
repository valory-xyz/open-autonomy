<a id="packages.valory.skills.transaction_settlement_abci.tests.test_behaviours"></a>

# packages.valory.skills.transaction`_`settlement`_`abci.tests.test`_`behaviours

Tests for valory/registration_abci skill's behaviours.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_behaviours.TransactionSettlementFSMBehaviourBaseCase"></a>

## TransactionSettlementFSMBehaviourBaseCase Objects

```python
class TransactionSettlementFSMBehaviourBaseCase(FSMBehaviourBaseCase)
```

Base case for testing TransactionSettlement FSMBehaviour.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_behaviours.TestTransactionSettlementBaseBehaviour"></a>

## TestTransactionSettlementBaseBehaviour Objects

```python
class TestTransactionSettlementBaseBehaviour(FSMBehaviourBaseCase)
```

Test `TransactionSettlementBaseBehaviour`.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_behaviours.TestTransactionSettlementBaseBehaviour.test__get_tx_data"></a>

#### test`__`get`_`tx`_`data

```python
@pytest.mark.parametrize(
        "message, tx_digest, rpc_status, expected_data, replacement",
        (
            (
                MagicMock(
                    performative=ContractApiMessage.Performative.ERROR, message="GS026"
                ),
                None,
                RPCResponseStatus.SUCCESS,
                {
                    "blacklisted_keepers": set(),
                    "keeper_retries": 2,
                    "keepers": deque(("agent_1" + "-" * 35, "agent_3" + "-" * 35)),
                    "status": VerificationStatus.VERIFIED,
                    "tx_digest": "",
                },
                False,
            ),
            (
                MagicMock(
                    performative=ContractApiMessage.Performative.ERROR, message="test"
                ),
                None,
                RPCResponseStatus.SUCCESS,
                {
                    "blacklisted_keepers": set(),
                    "keeper_retries": 2,
                    "keepers": deque(("agent_1" + "-" * 35, "agent_3" + "-" * 35)),
                    "status": VerificationStatus.ERROR,
                    "tx_digest": "",
                },
                False,
            ),
            (
                MagicMock(performative=ContractApiMessage.Performative.RAW_MESSAGE),
                None,
                RPCResponseStatus.SUCCESS,
                {
                    "blacklisted_keepers": set(),
                    "keeper_retries": 2,
                    "keepers": deque(("agent_1" + "-" * 35, "agent_3" + "-" * 35)),
                    "status": VerificationStatus.PENDING,
                    "tx_digest": "",
                },
                False,
            ),
            (
                MagicMock(performative=ContractApiMessage.Performative.RAW_TRANSACTION),
                None,
                RPCResponseStatus.INCORRECT_NONCE,
                {
                    "blacklisted_keepers": set(),
                    "keeper_retries": 2,
                    "keepers": deque(("agent_1" + "-" * 35, "agent_3" + "-" * 35)),
                    "status": VerificationStatus.ERROR,
                    "tx_digest": "",
                },
                False,
            ),
            (
                MagicMock(performative=ContractApiMessage.Performative.RAW_TRANSACTION),
                None,
                RPCResponseStatus.INSUFFICIENT_FUNDS,
                {
                    "blacklisted_keepers": {"agent_1" + "-" * 35},
                    "keeper_retries": 1,
                    "keepers": deque(("agent_3" + "-" * 35,)),
                    "status": VerificationStatus.INSUFFICIENT_FUNDS,
                    "tx_digest": "",
                },
                False,
            ),
            (
                MagicMock(performative=ContractApiMessage.Performative.RAW_TRANSACTION),
                None,
                RPCResponseStatus.UNCLASSIFIED_ERROR,
                {
                    "blacklisted_keepers": set(),
                    "keeper_retries": 2,
                    "keepers": deque(("agent_1" + "-" * 35, "agent_3" + "-" * 35)),
                    "status": VerificationStatus.PENDING,
                    "tx_digest": "",
                },
                False,
            ),
            (
                MagicMock(performative=ContractApiMessage.Performative.RAW_TRANSACTION),
                None,
                RPCResponseStatus.UNDERPRICED,
                {
                    "blacklisted_keepers": set(),
                    "keeper_retries": 2,
                    "keepers": deque(("agent_1" + "-" * 35, "agent_3" + "-" * 35)),
                    "status": VerificationStatus.PENDING,
                    "tx_digest": "",
                },
                False,
            ),
            (
                MagicMock(performative=ContractApiMessage.Performative.RAW_TRANSACTION),
                "test_digest_0",
                RPCResponseStatus.ALREADY_KNOWN,
                {
                    "blacklisted_keepers": set(),
                    "keeper_retries": 2,
                    "keepers": deque(("agent_1" + "-" * 35, "agent_3" + "-" * 35)),
                    "status": VerificationStatus.PENDING,
                    "tx_digest": "test_digest_0",
                },
                False,
            ),
            (
                MagicMock(
                    performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                    raw_transaction=MagicMock(
                        body={
                            "nonce": 0,
                            "maxPriorityFeePerGas": 10,
                            "maxFeePerGas": 20,
                            "gas": 0,
                        }
                    ),
                ),
                "test_digest_1",
                RPCResponseStatus.SUCCESS,
                {
                    "blacklisted_keepers": set(),
                    "keeper_retries": 2,
                    "keepers": deque(("agent_1" + "-" * 35, "agent_3" + "-" * 35)),
                    "status": VerificationStatus.PENDING,
                    "tx_digest": "test_digest_1",
                },
                False,
            ),
            (
                MagicMock(
                    performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                    raw_transaction=MagicMock(
                        body={
                            "nonce": 0,
                            "maxPriorityFeePerGas": 10,
                            "maxFeePerGas": 20,
                            "gas": 0,
                        }
                    ),
                ),
                "test_digest_2",
                RPCResponseStatus.SUCCESS,
                {
                    "blacklisted_keepers": set(),
                    "keeper_retries": 2,
                    "keepers": deque(("agent_1" + "-" * 35, "agent_3" + "-" * 35)),
                    "status": VerificationStatus.PENDING,
                    "tx_digest": "test_digest_2",
                },
                True,
            ),
        ),
    )
def test__get_tx_data(message: ContractApiMessage, tx_digest: Optional[str], rpc_status: RPCResponseStatus, expected_data: TxDataType, replacement: bool, monkeypatch: MonkeyPatch) -> None
```

Test `_get_tx_data`.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_behaviours.TestTransactionSettlementBaseBehaviour.test_get_gas_price_params"></a>

#### test`_`get`_`gas`_`price`_`params

```python
@pytest.mark.parametrize(
        argnames=["tx_body", "expected_params"],
        argvalues=[
            [
                {"maxPriorityFeePerGas": "dummy", "maxFeePerGas": "dummy"},
                ["maxPriorityFeePerGas", "maxFeePerGas"],
            ],
            [{"gasPrice": "dummy"}, ["gasPrice"]],
            [
                {"maxPriorityFeePerGas": "dummy"},
                [],
            ],
            [
                {"maxFeePerGas": "dummy"},
                [],
            ],
            [
                {},
                [],
            ],
            [
                {
                    "maxPriorityFeePerGas": "dummy",
                    "maxFeePerGas": "dummy",
                    "gasPrice": "dummy",
                },
                ["maxPriorityFeePerGas", "maxFeePerGas"],
            ],
        ],
    )
def test_get_gas_price_params(tx_body: dict, expected_params: List[str]) -> None
```

Test the get_gas_price_params method

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_behaviours.TestTransactionSettlementBaseBehaviour.test_parse_revert_reason_successful"></a>

#### test`_`parse`_`revert`_`reason`_`successful

```python
def test_parse_revert_reason_successful() -> None
```

Test `_parse_revert_reason` method.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_behaviours.TestTransactionSettlementBaseBehaviour.test_parse_revert_reason_unsuccessful"></a>

#### test`_`parse`_`revert`_`reason`_`unsuccessful

```python
@pytest.mark.parametrize(
        "message",
        (
            MagicMock(
                performative=ContractApiMessage.Performative.ERROR,
                message="Non existing code should be invalid GS086.",
            ),
            MagicMock(
                performative=ContractApiMessage.Performative.ERROR,
                message="Code not matching the regex should be invalid GS0265.",
            ),
            MagicMock(
                performative=ContractApiMessage.Performative.ERROR,
                message="No code in the message should be invalid.",
            ),
            MagicMock(
                performative=ContractApiMessage.Performative.ERROR,
                message="",  # empty message should be invalid
            ),
            MagicMock(
                performative=ContractApiMessage.Performative.ERROR,
                message=None,  # `None` message should be invalid
            ),
        ),
    )
def test_parse_revert_reason_unsuccessful(message: ContractApiMessage) -> None
```

Test `_parse_revert_reason` method.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_behaviours.TestRandomnessInOperation"></a>

## TestRandomnessInOperation Objects

```python
class TestRandomnessInOperation(BaseRandomnessBehaviourTest)
```

Test randomness in operation.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_behaviours.TestSelectKeeperTransactionSubmissionBehaviourA"></a>

## TestSelectKeeperTransactionSubmissionBehaviourA Objects

```python
class TestSelectKeeperTransactionSubmissionBehaviourA(BaseSelectKeeperBehaviourTest)
```

Test SelectKeeperBehaviour.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_behaviours.TestSelectKeeperTransactionSubmissionBehaviourB"></a>

## TestSelectKeeperTransactionSubmissionBehaviourB Objects

```python
class TestSelectKeeperTransactionSubmissionBehaviourB(
    TestSelectKeeperTransactionSubmissionBehaviourA)
```

Test SelectKeeperBehaviour.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_behaviours.TestSelectKeeperTransactionSubmissionBehaviourB.test_select_keeper"></a>

#### test`_`select`_`keeper

```python
@mock.patch.object(
        TransactionSettlementSynchronizedSata,
        "keepers",
        new_callable=mock.PropertyMock,
    )
@mock.patch.object(
        TransactionSettlementSynchronizedSata,
        "keeper_retries",
        new_callable=mock.PropertyMock,
    )
@pytest.mark.parametrize(
        "keepers, keeper_retries, blacklisted_keepers",
        (
            (deque(f"keeper_{i}" for i in range(4)), 1, set()),
            (deque(("test_keeper",)), 2, set()),
            (deque(("test_keeper",)), 2, {"a1"}),
            (deque(("test_keeper",)), 2, {"test_keeper"}),
            (deque(("test_keeper",)), 2, {"a_1", "a_2", "test_keeper"}),
            (deque(("test_keeper",)), 1, set()),
            (deque(("test_keeper",)), 3, set()),
        ),
    )
def test_select_keeper(keeper_retries_mock: mock.PropertyMock, keepers_mock: mock.PropertyMock, keepers: Deque[str], keeper_retries: int, blacklisted_keepers: Set[str]) -> None
```

Test select keeper agent.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_behaviours.TestSignatureBehaviour"></a>

## TestSignatureBehaviour Objects

```python
class TestSignatureBehaviour(TransactionSettlementFSMBehaviourBaseCase)
```

Test SignatureBehaviour.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_behaviours.TestSignatureBehaviour.test_signature_behaviour"></a>

#### test`_`signature`_`behaviour

```python
def test_signature_behaviour() -> None
```

Test signature behaviour.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_behaviours.TestFinalizeBehaviour"></a>

## TestFinalizeBehaviour Objects

```python
class TestFinalizeBehaviour(TransactionSettlementFSMBehaviourBaseCase)
```

Test FinalizeBehaviour.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_behaviours.TestFinalizeBehaviour.test_non_sender_act"></a>

#### test`_`non`_`sender`_`act

```python
def test_non_sender_act() -> None
```

Test finalize behaviour.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_behaviours.TestFinalizeBehaviour.test_sender_act"></a>

#### test`_`sender`_`act

```python
@pytest.mark.parametrize(
        "resubmitting, response_kwargs",
        (
            (
                (
                    True,
                    dict(
                        performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                        callable="get_deploy_transaction",
                        raw_transaction=RawTransaction(
                            ledger_id="ethereum",
                            body={
                                "tx_hash": "0x3b",
                                "nonce": 0,
                                "maxFeePerGas": int(10e10),
                                "maxPriorityFeePerGas": int(10e10),
                            },
                        ),
                    ),
                )
            ),
            (
                False,
                dict(
                    performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                    callable="get_deploy_transaction",
                    raw_transaction=RawTransaction(
                        ledger_id="ethereum",
                        body={
                            "tx_hash": "0x3b",
                            "nonce": 0,
                            "maxFeePerGas": int(10e10),
                            "maxPriorityFeePerGas": int(10e10),
                        },
                    ),
                ),
            ),
            (
                False,
                dict(
                    performative=ContractApiMessage.Performative.ERROR,
                    callable="get_deploy_transaction",
                    code=500,
                    message="GS026",
                    data=b"",
                ),
            ),
            (
                False,
                dict(
                    performative=ContractApiMessage.Performative.ERROR,
                    callable="get_deploy_transaction",
                    code=500,
                    message="other error",
                    data=b"",
                ),
            ),
        ),
    )
@mock.patch.object(SkillContext, "agent_address", new_callable=mock.PropertyMock)
def test_sender_act(agent_address_mock: mock.PropertyMock, resubmitting: bool, response_kwargs: Dict[
            str,
            Union[
                int,
                str,
                bytes,
                Dict[str, Union[int, str]],
                ContractApiMessage.Performative,
                RawTransaction,
            ],
        ]) -> None
```

Test finalize behaviour.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_behaviours.TestFinalizeBehaviour.test_handle_late_messages"></a>

#### test`_`handle`_`late`_`messages

```python
def test_handle_late_messages() -> None
```

Test `handle_late_messages.`

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_behaviours.TestValidateTransactionBehaviour"></a>

## TestValidateTransactionBehaviour Objects

```python
class TestValidateTransactionBehaviour(TransactionSettlementFSMBehaviourBaseCase)
```

Test ValidateTransactionBehaviour.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_behaviours.TestValidateTransactionBehaviour.test_validate_transaction_safe_behaviour"></a>

#### test`_`validate`_`transaction`_`safe`_`behaviour

```python
def test_validate_transaction_safe_behaviour() -> None
```

Test ValidateTransactionBehaviour.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_behaviours.TestValidateTransactionBehaviour.test_validate_transaction_safe_behaviour_no_tx_sent"></a>

#### test`_`validate`_`transaction`_`safe`_`behaviour`_`no`_`tx`_`sent

```python
def test_validate_transaction_safe_behaviour_no_tx_sent() -> None
```

Test ValidateTransactionBehaviour when tx cannot be sent.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_behaviours.TestCheckTransactionHistoryBehaviour"></a>

## TestCheckTransactionHistoryBehaviour Objects

```python
class TestCheckTransactionHistoryBehaviour(TransactionSettlementFSMBehaviourBaseCase)
```

Test CheckTransactionHistoryBehaviour.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_behaviours.TestCheckTransactionHistoryBehaviour.test_check_tx_history_behaviour"></a>

#### test`_`check`_`tx`_`history`_`behaviour

```python
@pytest.mark.parametrize(
        "verified, status, hashes_history, revert_reason",
        (
            (False, -1, "0x" + "t" * 64, "test"),
            (False, 0, "", "test"),
            (False, 0, "0x" + "t" * 64, "test"),
            (False, 0, "0x" + "t" * 64, "GS026"),
            (True, 1, "0x" + "t" * 64, "test"),
        ),
    )
def test_check_tx_history_behaviour(verified: bool, status: int, hashes_history: str, revert_reason: str) -> None
```

Test CheckTransactionHistoryBehaviour.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_behaviours.TestSynchronizeLateMessagesBehaviour"></a>

## TestSynchronizeLateMessagesBehaviour Objects

```python
class TestSynchronizeLateMessagesBehaviour(TransactionSettlementFSMBehaviourBaseCase)
```

Test `SynchronizeLateMessagesBehaviour`

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_behaviours.TestSynchronizeLateMessagesBehaviour.test_async_act"></a>

#### test`_`async`_`act

```python
@pytest.mark.parametrize("late_messages", ([], [MagicMock, MagicMock]))
def test_async_act(late_messages: List[MagicMock]) -> None
```

Test `async_act`

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_behaviours.TestResetBehaviour"></a>

## TestResetBehaviour Objects

```python
class TestResetBehaviour(TransactionSettlementFSMBehaviourBaseCase)
```

Test the reset behaviour.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_behaviours.TestResetBehaviour.test_reset_behaviour"></a>

#### test`_`reset`_`behaviour

```python
def test_reset_behaviour() -> None
```

Test reset behaviour.

