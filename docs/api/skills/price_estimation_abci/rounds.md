<a id="packages.valory.skills.price_estimation_abci.rounds"></a>

# packages.valory.skills.price`_`estimation`_`abci.rounds

This module contains the data classes for the price estimation ABCI application.

<a id="packages.valory.skills.price_estimation_abci.rounds.Event"></a>

## Event Objects

```python
class Event(Enum)
```

Event enumeration for the price estimation demo.

<a id="packages.valory.skills.price_estimation_abci.rounds.encode_float"></a>

#### encode`_`float

```python
def encode_float(value: float) -> bytes
```

Encode a float value.

<a id="packages.valory.skills.price_estimation_abci.rounds.rotate_list"></a>

#### rotate`_`list

```python
def rotate_list(my_list: list, positions: int) -> List[str]
```

Rotate a list n positions.

<a id="packages.valory.skills.price_estimation_abci.rounds.PeriodState"></a>

## PeriodState Objects

```python
class PeriodState(BasePeriodState)
```

Class to represent a period state.

This state is replicated by the tendermint application.

<a id="packages.valory.skills.price_estimation_abci.rounds.PeriodState.__init__"></a>

#### `__`init`__`

```python
def __init__(participants: Optional[AbstractSet[str]] = None, participant_to_randomness: Optional[Mapping[str, RandomnessPayload]] = None, most_voted_randomness: Optional[str] = None, participant_to_selection: Optional[Mapping[str, SelectKeeperPayload]] = None, most_voted_keeper_address: Optional[str] = None, safe_contract_address: Optional[str] = None, participant_to_votes: Optional[Mapping[str, ValidatePayload]] = None, participant_to_observations: Optional[Mapping[str, ObservationPayload]] = None, participant_to_estimate: Optional[Mapping[str, EstimatePayload]] = None, estimate: Optional[float] = None, most_voted_estimate: Optional[float] = None, participant_to_tx_hash: Optional[Mapping[str, TransactionHashPayload]] = None, most_voted_tx_hash: Optional[str] = None, participant_to_signature: Optional[Mapping[str, SignaturePayload]] = None, final_tx_hash: Optional[str] = None) -> None
```

Initialize a period state.

<a id="packages.valory.skills.price_estimation_abci.rounds.PeriodState.keeper_randomness"></a>

#### keeper`_`randomness

```python
@property
def keeper_randomness() -> float
```

Get the keeper's random number [0-1].

<a id="packages.valory.skills.price_estimation_abci.rounds.PeriodState.sorted_participants"></a>

#### sorted`_`participants

```python
@property
def sorted_participants() -> Sequence[str]
```

Get the sorted participants' addresses.

The addresses are sorted according to their hexadecimal value;
this is the reason we use key=str.lower as comparator.

This property is useful when interacting with the Safe contract.

**Returns**:

the sorted participants' addresses

<a id="packages.valory.skills.price_estimation_abci.rounds.PeriodState.participant_to_randomness"></a>

#### participant`_`to`_`randomness

```python
@property
def participant_to_randomness() -> Mapping[str, RandomnessPayload]
```

Get the participant_to_randomness.

<a id="packages.valory.skills.price_estimation_abci.rounds.PeriodState.most_voted_randomness"></a>

#### most`_`voted`_`randomness

```python
@property
def most_voted_randomness() -> str
```

Get the most_voted_randomness.

<a id="packages.valory.skills.price_estimation_abci.rounds.PeriodState.most_voted_keeper_address"></a>

#### most`_`voted`_`keeper`_`address

```python
@property
def most_voted_keeper_address() -> str
```

Get the most_voted_keeper_address.

<a id="packages.valory.skills.price_estimation_abci.rounds.PeriodState.safe_contract_address"></a>

#### safe`_`contract`_`address

```python
@property
def safe_contract_address() -> str
```

Get the safe contract address.

<a id="packages.valory.skills.price_estimation_abci.rounds.PeriodState.participant_to_selection"></a>

#### participant`_`to`_`selection

```python
@property
def participant_to_selection() -> Mapping[str, SelectKeeperPayload]
```

Get the participant_to_selection.

<a id="packages.valory.skills.price_estimation_abci.rounds.PeriodState.participant_to_votes"></a>

#### participant`_`to`_`votes

```python
@property
def participant_to_votes() -> Mapping[str, ValidatePayload]
```

Get the participant_to_votes.

<a id="packages.valory.skills.price_estimation_abci.rounds.PeriodState.participant_to_observations"></a>

#### participant`_`to`_`observations

```python
@property
def participant_to_observations() -> Mapping[str, ObservationPayload]
```

Get the participant_to_observations.

<a id="packages.valory.skills.price_estimation_abci.rounds.PeriodState.participant_to_estimate"></a>

#### participant`_`to`_`estimate

```python
@property
def participant_to_estimate() -> Mapping[str, EstimatePayload]
```

Get the participant_to_estimate.

<a id="packages.valory.skills.price_estimation_abci.rounds.PeriodState.participant_to_signature"></a>

#### participant`_`to`_`signature

```python
@property
def participant_to_signature() -> Mapping[str, SignaturePayload]
```

Get the participant_to_signature.

<a id="packages.valory.skills.price_estimation_abci.rounds.PeriodState.final_tx_hash"></a>

#### final`_`tx`_`hash

```python
@property
def final_tx_hash() -> str
```

Get the final_tx_hash.

<a id="packages.valory.skills.price_estimation_abci.rounds.PeriodState.estimate"></a>

#### estimate

```python
@property
def estimate() -> float
```

Get the estimate.

<a id="packages.valory.skills.price_estimation_abci.rounds.PeriodState.most_voted_estimate"></a>

#### most`_`voted`_`estimate

```python
@property
def most_voted_estimate() -> float
```

Get the most_voted_estimate.

<a id="packages.valory.skills.price_estimation_abci.rounds.PeriodState.encoded_most_voted_estimate"></a>

#### encoded`_`most`_`voted`_`estimate

```python
@property
def encoded_most_voted_estimate() -> bytes
```

Get the encoded (most voted) estimate.

<a id="packages.valory.skills.price_estimation_abci.rounds.PeriodState.most_voted_tx_hash"></a>

#### most`_`voted`_`tx`_`hash

```python
@property
def most_voted_tx_hash() -> str
```

Get the most_voted_tx_hash.

<a id="packages.valory.skills.price_estimation_abci.rounds.PeriodState.reset"></a>

#### reset

```python
def reset() -> "PeriodState"
```

Return the initial period state.

<a id="packages.valory.skills.price_estimation_abci.rounds.PriceEstimationAbstractRound"></a>

## PriceEstimationAbstractRound Objects

```python
class PriceEstimationAbstractRound(AbstractRound[Event, TransactionType],  ABC)
```

Abstract round for the price estimation skill.

<a id="packages.valory.skills.price_estimation_abci.rounds.PriceEstimationAbstractRound.period_state"></a>

#### period`_`state

```python
@property
def period_state() -> PeriodState
```

Return the period state.

<a id="packages.valory.skills.price_estimation_abci.rounds.RegistrationRound"></a>

## RegistrationRound Objects

```python
class RegistrationRound(CollectDifferentUntilAllRound,  PriceEstimationAbstractRound)
```

This class represents the registration round.

Input: None
Output: a period state with the set of participants.

It schedules the SelectKeeperARound.

<a id="packages.valory.skills.price_estimation_abci.rounds.RegistrationRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BasePeriodState, Event]]
```

Process the end of the block.

<a id="packages.valory.skills.price_estimation_abci.rounds.RandomnessRound"></a>

## RandomnessRound Objects

```python
class RandomnessRound(CollectSameUntilThresholdRound,  PriceEstimationAbstractRound)
```

This class represents the randomness round.

Input: a set of participants (addresses)
Output: a set of participants (addresses) and randomness

It schedules the SelectKeeperARound.

<a id="packages.valory.skills.price_estimation_abci.rounds.RandomnessRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BasePeriodState, Event]]
```

Process the end of the block.

<a id="packages.valory.skills.price_estimation_abci.rounds.SelectKeeperRound"></a>

## SelectKeeperRound Objects

```python
class SelectKeeperRound(CollectSameUntilThresholdRound,  PriceEstimationAbstractRound)
```

This class represents the select keeper round.

Input: a set of participants (addresses)
Output: the selected keeper.

<a id="packages.valory.skills.price_estimation_abci.rounds.SelectKeeperRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BasePeriodState, Event]]
```

Process the end of the block.

<a id="packages.valory.skills.price_estimation_abci.rounds.DeploySafeRound"></a>

## DeploySafeRound Objects

```python
class DeploySafeRound(OnlyKeeperSendsRound,  PriceEstimationAbstractRound)
```

This class represents the deploy Safe round.

Input: a set of participants (addresses) and a keeper
Output: a period state with the set of participants, the keeper and the Safe contract address.

It schedules the ValidateSafeRound.

<a id="packages.valory.skills.price_estimation_abci.rounds.DeploySafeRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BasePeriodState, Event]]
```

Process the end of the block.

<a id="packages.valory.skills.price_estimation_abci.rounds.ValidateRound"></a>

## ValidateRound Objects

```python
class ValidateRound(VotingRound,  PriceEstimationAbstractRound)
```

This class represents the validate round.

Input: a period state with the set of participants, the keeper and the Safe contract address.
Output: a period state with the set of participants, the keeper, the Safe contract address and a validation of the Safe contract address.

<a id="packages.valory.skills.price_estimation_abci.rounds.ValidateRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BasePeriodState, Event]]
```

Process the end of the block.

<a id="packages.valory.skills.price_estimation_abci.rounds.CollectObservationRound"></a>

## CollectObservationRound Objects

```python
class CollectObservationRound(
    CollectDifferentUntilThresholdRound,  PriceEstimationAbstractRound)
```

This class represents the 'collect-observation' round.

Input: a period state with the prior round data
Ouptut: a new period state with the prior round data and the observations

It schedules the EstimateConsensusRound.

<a id="packages.valory.skills.price_estimation_abci.rounds.CollectObservationRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BasePeriodState, Event]]
```

Process the end of the block.

<a id="packages.valory.skills.price_estimation_abci.rounds.EstimateConsensusRound"></a>

## EstimateConsensusRound Objects

```python
class EstimateConsensusRound(
    CollectSameUntilThresholdRound,  PriceEstimationAbstractRound)
```

This class represents the 'estimate_consensus' round.

Input: a period state with the prior round data
Ouptut: a new period state with the prior round data and the votes for each estimate

It schedules the TxHashRound.

<a id="packages.valory.skills.price_estimation_abci.rounds.EstimateConsensusRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BasePeriodState, Event]]
```

Process the end of the block.

<a id="packages.valory.skills.price_estimation_abci.rounds.TxHashRound"></a>

## TxHashRound Objects

```python
class TxHashRound(CollectSameUntilThresholdRound,  PriceEstimationAbstractRound)
```

This class represents the 'tx-hash' round.

Input: a period state with the prior round data
Ouptut: a new period state with the prior round data and the votes for each tx hash

It schedules the CollectSignatureRound.

<a id="packages.valory.skills.price_estimation_abci.rounds.TxHashRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BasePeriodState, Event]]
```

Process the end of the block.

<a id="packages.valory.skills.price_estimation_abci.rounds.CollectSignatureRound"></a>

## CollectSignatureRound Objects

```python
class CollectSignatureRound(
    CollectDifferentUntilThresholdRound,  PriceEstimationAbstractRound)
```

This class represents the 'collect-signature' round.

Input: a period state with the prior round data
Ouptut: a new period state with the prior round data and the signatures

It schedules the FinalizationRound.

<a id="packages.valory.skills.price_estimation_abci.rounds.CollectSignatureRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BasePeriodState, Event]]
```

Process the end of the block.

<a id="packages.valory.skills.price_estimation_abci.rounds.FinalizationRound"></a>

## FinalizationRound Objects

```python
class FinalizationRound(OnlyKeeperSendsRound,  PriceEstimationAbstractRound)
```

This class represents the finalization Safe round.

Input: a period state with the prior round data
Output: a new period state with the prior round data and the hash of the Safe transaction

It schedules the ValidateTransactionRound.

<a id="packages.valory.skills.price_estimation_abci.rounds.FinalizationRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BasePeriodState, Event]]
```

Process the end of the block.

<a id="packages.valory.skills.price_estimation_abci.rounds.SelectKeeperARound"></a>

## SelectKeeperARound Objects

```python
class SelectKeeperARound(SelectKeeperRound)
```

This class represents the select keeper A round.

<a id="packages.valory.skills.price_estimation_abci.rounds.SelectKeeperBRound"></a>

## SelectKeeperBRound Objects

```python
class SelectKeeperBRound(SelectKeeperRound)
```

This class represents the select keeper B round.

<a id="packages.valory.skills.price_estimation_abci.rounds.ConsensusReachedRound"></a>

## ConsensusReachedRound Objects

```python
class ConsensusReachedRound(PriceEstimationAbstractRound)
```

This class represents the 'consensus-reached' round (the final round).

<a id="packages.valory.skills.price_estimation_abci.rounds.ConsensusReachedRound.process_payload"></a>

#### process`_`payload

```python
def process_payload(payload: BaseTxPayload) -> None
```

Process the payload.

<a id="packages.valory.skills.price_estimation_abci.rounds.ConsensusReachedRound.check_payload"></a>

#### check`_`payload

```python
def check_payload(payload: BaseTxPayload) -> None
```

Check the payload

<a id="packages.valory.skills.price_estimation_abci.rounds.ConsensusReachedRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BasePeriodState, Event]]
```

Process the end of the block.

<a id="packages.valory.skills.price_estimation_abci.rounds.ValidateSafeRound"></a>

## ValidateSafeRound Objects

```python
class ValidateSafeRound(ValidateRound)
```

This class represents the validate Safe round.

Input: a period state with the prior round data
Output: a new period state with the prior round data and the validation of the contract address

It schedules the CollectObservationRound or SelectKeeperARound.

<a id="packages.valory.skills.price_estimation_abci.rounds.ValidateTransactionRound"></a>

## ValidateTransactionRound Objects

```python
class ValidateTransactionRound(ValidateRound)
```

This class represents the validate transaction round.

Input: a period state with the prior round data
Output: a new period state with the prior round data and the validation of the transaction

It schedules the ConsensusReachedRound or SelectKeeperARound.

<a id="packages.valory.skills.price_estimation_abci.rounds.PriceEstimationAbciApp"></a>

## PriceEstimationAbciApp Objects

```python
class PriceEstimationAbciApp(AbciApp[Event])
```

Price estimation ABCI application.

