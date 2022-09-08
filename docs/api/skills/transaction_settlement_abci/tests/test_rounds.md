<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds"></a>

# packages.valory.skills.transaction`_`settlement`_`abci.tests.test`_`rounds

Tests for valory/registration_abci skill's rounds.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.get_participants"></a>

#### get`_`participants

```python
def get_participants() -> FrozenSet[str]
```

Participants

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.get_participant_to_randomness"></a>

#### get`_`participant`_`to`_`randomness

```python
def get_participant_to_randomness(participants: FrozenSet[str], round_id: int) -> Dict[str, RandomnessPayload]
```

participant_to_randomness

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.get_most_voted_randomness"></a>

#### get`_`most`_`voted`_`randomness

```python
def get_most_voted_randomness() -> str
```

most_voted_randomness

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.get_participant_to_selection"></a>

#### get`_`participant`_`to`_`selection

```python
def get_participant_to_selection(participants: FrozenSet[str], keepers: str) -> Dict[str, SelectKeeperPayload]
```

participant_to_selection

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.get_participant_to_period_count"></a>

#### get`_`participant`_`to`_`period`_`count

```python
def get_participant_to_period_count(participants: FrozenSet[str], period_count: int) -> Dict[str, ResetPayload]
```

participant_to_selection

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.get_safe_contract_address"></a>

#### get`_`safe`_`contract`_`address

```python
def get_safe_contract_address() -> str
```

safe_contract_address

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.get_participant_to_votes"></a>

#### get`_`participant`_`to`_`votes

```python
def get_participant_to_votes(participants: FrozenSet[str], vote: Optional[bool] = True) -> Dict[str, ValidatePayload]
```

participant_to_votes

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.get_most_voted_tx_hash"></a>

#### get`_`most`_`voted`_`tx`_`hash

```python
def get_most_voted_tx_hash() -> str
```

most_voted_tx_hash

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.get_participant_to_signature"></a>

#### get`_`participant`_`to`_`signature

```python
def get_participant_to_signature(participants: FrozenSet[str]) -> Dict[str, SignaturePayload]
```

participant_to_signature

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.get_final_tx_hash"></a>

#### get`_`final`_`tx`_`hash

```python
def get_final_tx_hash() -> str
```

final_tx_hash

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.get_participant_to_check"></a>

#### get`_`participant`_`to`_`check

```python
def get_participant_to_check(participants: FrozenSet[str], status: str, tx_hash: str) -> Dict[str, CheckTransactionHistoryPayload]
```

Get participants to check

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.get_participant_to_late_arriving_tx_hashes"></a>

#### get`_`participant`_`to`_`late`_`arriving`_`tx`_`hashes

```python
def get_participant_to_late_arriving_tx_hashes(participants: FrozenSet[str]) -> Dict[str, SynchronizeLateMessagesPayload]
```

participant_to_selection

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.get_late_arriving_tx_hashes"></a>

#### get`_`late`_`arriving`_`tx`_`hashes

```python
def get_late_arriving_tx_hashes() -> List[str]
```

Get dummy late-arriving tx hashes.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.get_keepers"></a>

#### get`_`keepers

```python
def get_keepers(keepers: Deque[str], retries: int = 1) -> str
```

Get dummy keepers.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.BaseValidateRoundTest"></a>

## BaseValidateRoundTest Objects

```python
class BaseValidateRoundTest(BaseVotingRoundTest)
```

Test BaseValidateRound.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.BaseValidateRoundTest.test_positive_votes"></a>

#### test`_`positive`_`votes

```python
def test_positive_votes() -> None
```

Test ValidateRound.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.BaseValidateRoundTest.test_negative_votes"></a>

#### test`_`negative`_`votes

```python
def test_negative_votes() -> None
```

Test ValidateRound.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.BaseValidateRoundTest.test_none_votes"></a>

#### test`_`none`_`votes

```python
def test_none_votes() -> None
```

Test ValidateRound.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.BaseSelectKeeperRoundTest"></a>

## BaseSelectKeeperRoundTest Objects

```python
class BaseSelectKeeperRoundTest(BaseCollectSameUntilThresholdRoundTest)
```

Test SelectKeeperTransactionSubmissionRoundA

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.BaseSelectKeeperRoundTest.test_run"></a>

#### test`_`run

```python
def test_run(most_voted_payload: str = "keeper", keepers: str = "", exit_event: Optional[Any] = None) -> None
```

Run tests.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.TestSelectKeeperTransactionSubmissionRoundA"></a>

## TestSelectKeeperTransactionSubmissionRoundA Objects

```python
class TestSelectKeeperTransactionSubmissionRoundA(BaseSelectKeeperRoundTest)
```

Test SelectKeeperTransactionSubmissionRoundA

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.TestSelectKeeperTransactionSubmissionRoundA.test_run"></a>

#### test`_`run

```python
@pytest.mark.parametrize(
        "most_voted_payload, keepers, exit_event",
        (
            (
                "incorrectly_serialized",
                "",
                TransactionSettlementEvent.INCORRECT_SERIALIZATION,
            ),
            (
                int(1).to_bytes(32, "big").hex() + "new_keeper" + "-" * 32,
                "",
                TransactionSettlementEvent.DONE,
            ),
        ),
    )
def test_run(most_voted_payload: str, keepers: str, exit_event: TransactionSettlementEvent) -> None
```

Run tests.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.TestSelectKeeperTransactionSubmissionRoundB"></a>

## TestSelectKeeperTransactionSubmissionRoundB Objects

```python
class TestSelectKeeperTransactionSubmissionRoundB(
    TestSelectKeeperTransactionSubmissionRoundA)
```

Test SelectKeeperTransactionSubmissionRoundB.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.TestSelectKeeperTransactionSubmissionRoundB.test_run"></a>

#### test`_`run

```python
@pytest.mark.parametrize(
        "most_voted_payload, keepers, exit_event",
        (
            (
                int(1).to_bytes(32, "big").hex() + "new_keeper" + "-" * 32,
                "",
                TransactionSettlementEvent.DONE,
            ),
            (
                int(1).to_bytes(32, "big").hex() + "new_keeper" + "-" * 32,
                int(1).to_bytes(32, "big").hex()
                + "".join(
                    [keeper + "-" * 30 for keeper in ("test_keeper1", "test_keeper2")]
                ),
                TransactionSettlementEvent.DONE,
            ),
        ),
    )
def test_run(most_voted_payload: str, keepers: str, exit_event: TransactionSettlementEvent) -> None
```

Run tests.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.TestSelectKeeperTransactionSubmissionRoundBAfterTimeout"></a>

## TestSelectKeeperTransactionSubmissionRoundBAfterTimeout Objects

```python
class TestSelectKeeperTransactionSubmissionRoundBAfterTimeout(
    TestSelectKeeperTransactionSubmissionRoundB)
```

Test SelectKeeperTransactionSubmissionRoundBAfterTimeout.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.TestSelectKeeperTransactionSubmissionRoundBAfterTimeout.test_run"></a>

#### test`_`run

```python
@mock.patch.object(
        TransactionSettlementSynchronizedSata,
        "keepers_threshold_exceeded",
        new_callable=mock.PropertyMock,
    )
@pytest.mark.parametrize(
        "attrs, threshold_exceeded, exit_event",
        (
            (
                {
                    "tx_hashes_history": "t" * 66,
                    "missed_messages": 10,
                },
                True,
                # Since the threshold has been exceeded, we should return a `CHECK_HISTORY` event.
                TransactionSettlementEvent.CHECK_HISTORY,
            ),
            (
                {
                    "missed_messages": 10,
                },
                True,
                TransactionSettlementEvent.CHECK_LATE_ARRIVING_MESSAGE,
            ),
            (
                {
                    "missed_messages": 10,
                },
                False,
                TransactionSettlementEvent.DONE,
            ),
        ),
    )
def test_run(threshold_exceeded_mock: mock.PropertyMock, attrs: Dict[str, Union[str, int]], threshold_exceeded: bool, exit_event: TransactionSettlementEvent) -> None
```

Test `SelectKeeperTransactionSubmissionRoundBAfterTimeout`.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.TestFinalizationRound"></a>

## TestFinalizationRound Objects

```python
class TestFinalizationRound(BaseOnlyKeeperSendsRoundTest)
```

Test FinalizationRound.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.TestFinalizationRound.test_finalization_round"></a>

#### test`_`finalization`_`round

```python
@pytest.mark.parametrize(
        "tx_hashes_history, tx_digest, missed_messages, status, exit_event",
        (
            (
                "",
                "",
                1,
                VerificationStatus.ERROR.value,
                TransactionSettlementEvent.CHECK_LATE_ARRIVING_MESSAGE,
            ),
            (
                "",
                "",
                0,
                VerificationStatus.ERROR.value,
                TransactionSettlementEvent.FINALIZATION_FAILED,
            ),
            (
                "t" * 66,
                "",
                0,
                VerificationStatus.VERIFIED.value,
                TransactionSettlementEvent.CHECK_HISTORY,
            ),
            (
                "t" * 66,
                "",
                0,
                VerificationStatus.ERROR.value,
                TransactionSettlementEvent.CHECK_HISTORY,
            ),
            (
                "",
                "",
                0,
                VerificationStatus.PENDING.value,
                TransactionSettlementEvent.FINALIZATION_FAILED,
            ),
            (
                "",
                "tx_digest" + "t" * 57,
                0,
                VerificationStatus.PENDING.value,
                TransactionSettlementEvent.DONE,
            ),
            (
                "t" * 66,
                "tx_digest" + "t" * 57,
                0,
                VerificationStatus.PENDING.value,
                TransactionSettlementEvent.DONE,
            ),
            (
                "t" * 66,
                "",
                0,
                VerificationStatus.INSUFFICIENT_FUNDS.value,
                TransactionSettlementEvent.INSUFFICIENT_FUNDS,
            ),
        ),
    )
def test_finalization_round(tx_hashes_history: str, tx_digest: str, missed_messages: int, status: int, exit_event: TransactionSettlementEvent) -> None
```

Runs tests.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.TestCollectSignatureRound"></a>

## TestCollectSignatureRound Objects

```python
class TestCollectSignatureRound(BaseCollectDifferentUntilThresholdRoundTest)
```

Test CollectSignatureRound.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.TestCollectSignatureRound.test_run"></a>

#### test`_`run

```python
def test_run() -> None
```

Runs tests.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.TestCollectSignatureRound.test_no_majority_event"></a>

#### test`_`no`_`majority`_`event

```python
def test_no_majority_event() -> None
```

Test the no-majority event.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.TestValidateTransactionRound"></a>

## TestValidateTransactionRound Objects

```python
class TestValidateTransactionRound(BaseValidateRoundTest)
```

Test ValidateRound.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.TestCheckTransactionHistoryRound"></a>

## TestCheckTransactionHistoryRound Objects

```python
class TestCheckTransactionHistoryRound(BaseCollectSameUntilThresholdRoundTest)
```

Test CheckTransactionHistoryRound

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.TestCheckTransactionHistoryRound.test_run"></a>

#### test`_`run

```python
@pytest.mark.parametrize(
        "expected_status, expected_tx_hash, missed_messages, expected_event",
        (
            (
                "0000000000000000000000000000000000000000000000000000000000000001",
                "b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9",
                0,
                TransactionSettlementEvent.DONE,
            ),
            (
                "0000000000000000000000000000000000000000000000000000000000000002",
                "b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9",
                0,
                TransactionSettlementEvent.NEGATIVE,
            ),
            (
                "0000000000000000000000000000000000000000000000000000000000000003",
                "b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9",
                0,
                TransactionSettlementEvent.NONE,
            ),
            (
                "0000000000000000000000000000000000000000000000000000000000000002",
                "b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9",
                1,
                TransactionSettlementEvent.CHECK_LATE_ARRIVING_MESSAGE,
            ),
        ),
    )
def test_run(expected_status: str, expected_tx_hash: str, missed_messages: int, expected_event: TransactionSettlementEvent) -> None
```

Run tests.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.TestSynchronizeLateMessagesRound"></a>

## TestSynchronizeLateMessagesRound Objects

```python
class TestSynchronizeLateMessagesRound(BaseCollectNonEmptyUntilThresholdRound)
```

Test `SynchronizeLateMessagesRound`.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.TestSynchronizeLateMessagesRound.test_runs"></a>

#### test`_`runs

```python
@pytest.mark.parametrize(
        "missed_messages, expected_event",
        (
            (0, TransactionSettlementEvent.MISSED_AND_LATE_MESSAGES_MISMATCH),
            (8, TransactionSettlementEvent.DONE),
        ),
    )
def test_runs(missed_messages: int, expected_event: TransactionSettlementEvent) -> None
```

Runs tests.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.TestSynchronizeLateMessagesRound.test_incorrect_serialization_not_accepted"></a>

#### test`_`incorrect`_`serialization`_`not`_`accepted

```python
def test_incorrect_serialization_not_accepted() -> None
```

Test wrong serialization not collected

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.test_synchronized_datas"></a>

#### test`_`synchronized`_`datas

```python
def test_synchronized_datas() -> None
```

Test SynchronizedData.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.TestResetRound"></a>

## TestResetRound Objects

```python
class TestResetRound(BaseCollectSameUntilThresholdRoundTest)
```

Test ResetRound.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_rounds.TestResetRound.test_runs"></a>

#### test`_`runs

```python
def test_runs() -> None
```

Runs tests.

