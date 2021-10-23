<a id="packages.valory.skills.price_estimation_abci.rounds"></a>

# packages.valory.skills.price`_`estimation`_`abci.rounds

This module contains the data classes for the price estimation ABCI application.

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
def __init__(participants: Optional[AbstractSet[str]] = None, participant_to_randomness: Optional[Mapping[str, RandomnessPayload]] = None, most_voted_randomness: Optional[str] = None, participant_to_selection: Optional[Mapping[str, SelectKeeperPayload]] = None, most_voted_keeper_address: Optional[str] = None, safe_contract_address: Optional[str] = None, participant_to_votes: Optional[Mapping[str, ValidatePayload]] = None, participant_to_observations: Optional[Mapping[str, ObservationPayload]] = None, participant_to_estimate: Optional[Mapping[str, EstimatePayload]] = None, estimate: Optional[float] = None, most_voted_estimate: Optional[float] = None, participant_to_tx_hash: Optional[Mapping[str, TransactionHashPayload]] = None, most_voted_tx_hash: Optional[str] = None, participant_to_signature: Optional[Mapping[str, str]] = None, final_tx_hash: Optional[str] = None) -> None
```

Initialize a period state.

<a id="packages.valory.skills.price_estimation_abci.rounds.PeriodState.keeper_randomness"></a>

#### keeper`_`randomness

```python
@property
def keeper_randomness() -> float
```

Get the keeper's random number [0-1].

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
def participant_to_signature() -> Mapping[str, str]
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

<a id="packages.valory.skills.price_estimation_abci.rounds.PriceEstimationAbstractRound"></a>

## PriceEstimationAbstractRound Objects

```python
class PriceEstimationAbstractRound(AbstractRound,  ABC)
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
class RegistrationRound(PriceEstimationAbstractRound)
```

This class represents the registration round.

Input: None
Output: a period state with the set of participants.

It schedules the SelectKeeperARound.

<a id="packages.valory.skills.price_estimation_abci.rounds.RegistrationRound.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any) -> None
```

Initialize the registration round.

<a id="packages.valory.skills.price_estimation_abci.rounds.RegistrationRound.registration"></a>

#### registration

```python
def registration(payload: RegistrationPayload) -> None
```

Handle a registration payload.

<a id="packages.valory.skills.price_estimation_abci.rounds.RegistrationRound.check_registration"></a>

#### check`_`registration

```python
def check_registration(_payload: RegistrationPayload) -> None
```

Check a registration payload can be applied to the current state.

A registration can happen only when we are in the registration state.

:param: _payload: the payload.

<a id="packages.valory.skills.price_estimation_abci.rounds.RegistrationRound.registration_threshold_reached"></a>

#### registration`_`threshold`_`reached

```python
@property
def registration_threshold_reached() -> bool
```

Check that the registration threshold has been reached.

<a id="packages.valory.skills.price_estimation_abci.rounds.RegistrationRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BasePeriodState, AbstractRound]]
```

Process the end of the block.

<a id="packages.valory.skills.price_estimation_abci.rounds.RandomnessRound"></a>

## RandomnessRound Objects

```python
class RandomnessRound(PriceEstimationAbstractRound,  ABC)
```

This class represents the randomness round.

Input: a set of participants (addresses)
Output: a set of participants (addresses) and randomness

It schedules the SelectKeeperARound.

<a id="packages.valory.skills.price_estimation_abci.rounds.RandomnessRound.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any)
```

Initialize the 'select-keeper' round.

<a id="packages.valory.skills.price_estimation_abci.rounds.RandomnessRound.randomness"></a>

#### randomness

```python
def randomness(payload: RandomnessPayload) -> None
```

Handle a 'randomness' payload.

<a id="packages.valory.skills.price_estimation_abci.rounds.RandomnessRound.check_randomness"></a>

#### check`_`randomness

```python
def check_randomness(payload: SelectKeeperPayload) -> bool
```

Check an randomness payload can be applied to the current state.

An randomness transaction can be applied only if:
- the round is in the 'randomness' state;
- the sender belongs to the set of participants
- the sender has not sent its selection yet

:param: payload: the payload.

**Returns**:

True if the selection is allowed, False otherwise.

<a id="packages.valory.skills.price_estimation_abci.rounds.RandomnessRound.threshold_reached"></a>

#### threshold`_`reached

```python
@property
def threshold_reached() -> bool
```

Check that the threshold has been reached.

<a id="packages.valory.skills.price_estimation_abci.rounds.RandomnessRound.most_voted_randomness"></a>

#### most`_`voted`_`randomness

```python
@property
def most_voted_randomness() -> float
```

Get the most voted randomness.

<a id="packages.valory.skills.price_estimation_abci.rounds.RandomnessRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BasePeriodState, AbstractRound]]
```

Process the end of the block.

<a id="packages.valory.skills.price_estimation_abci.rounds.SelectKeeperRound"></a>

## SelectKeeperRound Objects

```python
class SelectKeeperRound(PriceEstimationAbstractRound,  ABC)
```

This class represents the select keeper round.

Input: a set of participants (addresses)
Output: the selected keeper.

It schedules the next_round_class.

<a id="packages.valory.skills.price_estimation_abci.rounds.SelectKeeperRound.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any)
```

Initialize the 'select-keeper' round.

<a id="packages.valory.skills.price_estimation_abci.rounds.SelectKeeperRound.select_keeper"></a>

#### select`_`keeper

```python
def select_keeper(payload: SelectKeeperPayload) -> None
```

Handle a 'select_keeper' payload.

<a id="packages.valory.skills.price_estimation_abci.rounds.SelectKeeperRound.check_select_keeper"></a>

#### check`_`select`_`keeper

```python
def check_select_keeper(payload: SelectKeeperPayload) -> None
```

Check an select_keeper payload can be applied to the current state.

An select_keeper transaction can be applied only if:
- the round is in the 'select_keeper' state;
- the sender belongs to the set of participants
- the sender has not sent its selection yet

:param: payload: the payload.

<a id="packages.valory.skills.price_estimation_abci.rounds.SelectKeeperRound.selection_threshold_reached"></a>

#### selection`_`threshold`_`reached

```python
@property
def selection_threshold_reached() -> bool
```

Check that the selection threshold has been reached.

<a id="packages.valory.skills.price_estimation_abci.rounds.SelectKeeperRound.most_voted_keeper_address"></a>

#### most`_`voted`_`keeper`_`address

```python
@property
def most_voted_keeper_address() -> float
```

Get the most voted keeper.

<a id="packages.valory.skills.price_estimation_abci.rounds.SelectKeeperRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BasePeriodState, AbstractRound]]
```

Process the end of the block.

<a id="packages.valory.skills.price_estimation_abci.rounds.DeploySafeRound"></a>

## DeploySafeRound Objects

```python
class DeploySafeRound(PriceEstimationAbstractRound)
```

This class represents the deploy Safe round.

Input: a set of participants (addresses) and a keeper
Output: a period state with the set of participants, the keeper and the Safe contract address.

It schedules the ValidateSafeRound.

<a id="packages.valory.skills.price_estimation_abci.rounds.DeploySafeRound.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any)
```

Initialize the 'collect-observation' round.

<a id="packages.valory.skills.price_estimation_abci.rounds.DeploySafeRound.deploy_safe"></a>

#### deploy`_`safe

```python
def deploy_safe(payload: DeploySafePayload) -> None
```

Handle a deploy safe payload.

<a id="packages.valory.skills.price_estimation_abci.rounds.DeploySafeRound.check_deploy_safe"></a>

#### check`_`deploy`_`safe

```python
def check_deploy_safe(payload: DeploySafePayload) -> None
```

Check a deploy safe payload can be applied to the current state.

A deploy safe transaction can be applied only if:
- the sender belongs to the set of participants
- the sender is the elected sender
- the sender has not already sent the contract address

:param: payload: the payload.

<a id="packages.valory.skills.price_estimation_abci.rounds.DeploySafeRound.is_contract_set"></a>

#### is`_`contract`_`set

```python
@property
def is_contract_set() -> bool
```

Check that the contract has been set.

<a id="packages.valory.skills.price_estimation_abci.rounds.DeploySafeRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BasePeriodState, AbstractRound]]
```

Process the end of the block.

<a id="packages.valory.skills.price_estimation_abci.rounds.ValidateRound"></a>

## ValidateRound Objects

```python
class ValidateRound(PriceEstimationAbstractRound)
```

This class represents the validate round.

Input: a period state with the set of participants, the keeper and the Safe contract address.
Output: a period state with the set of participants, the keeper, the Safe contract address and a validation of the Safe contract address.

It schedules the positive_next_round_class or negative_next_round_class.

<a id="packages.valory.skills.price_estimation_abci.rounds.ValidateRound.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any)
```

Initialize the 'collect-observation' round.

<a id="packages.valory.skills.price_estimation_abci.rounds.ValidateRound.validate"></a>

#### validate

```python
def validate(payload: ValidatePayload) -> None
```

Handle a validate safe payload.

<a id="packages.valory.skills.price_estimation_abci.rounds.ValidateRound.check_validate"></a>

#### check`_`validate

```python
def check_validate(payload: ValidatePayload) -> None
```

Check a validate payload can be applied to the current state.

A validate transaction can be applied only if:
- the sender belongs to the set of participants
- the sender has not already submitted the transaction

:param: payload: the payload.

<a id="packages.valory.skills.price_estimation_abci.rounds.ValidateRound.positive_vote_threshold_reached"></a>

#### positive`_`vote`_`threshold`_`reached

```python
@property
def positive_vote_threshold_reached() -> bool
```

Check that the vote threshold has been reached.

<a id="packages.valory.skills.price_estimation_abci.rounds.ValidateRound.negative_vote_threshold_reached"></a>

#### negative`_`vote`_`threshold`_`reached

```python
@property
def negative_vote_threshold_reached() -> bool
```

Check that the vote threshold has been reached.

<a id="packages.valory.skills.price_estimation_abci.rounds.ValidateRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BasePeriodState, AbstractRound]]
```

Process the end of the block.

<a id="packages.valory.skills.price_estimation_abci.rounds.CollectObservationRound"></a>

## CollectObservationRound Objects

```python
class CollectObservationRound(PriceEstimationAbstractRound)
```

This class represents the 'collect-observation' round.

Input: a period state with the prior round data
Ouptut: a new period state with the prior round data and the observations

It schedules the EstimateConsensusRound.

<a id="packages.valory.skills.price_estimation_abci.rounds.CollectObservationRound.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any)
```

Initialize the 'collect-observation' round.

<a id="packages.valory.skills.price_estimation_abci.rounds.CollectObservationRound.observation"></a>

#### observation

```python
def observation(payload: ObservationPayload) -> None
```

Handle an 'observation' payload.

<a id="packages.valory.skills.price_estimation_abci.rounds.CollectObservationRound.check_observation"></a>

#### check`_`observation

```python
def check_observation(payload: ObservationPayload) -> None
```

Check an observation payload can be applied to the current state.

An observation transaction can be applied only if:
- the sender belongs to the set of participants
- the sender has not already sent its observation

:param: payload: the payload.

<a id="packages.valory.skills.price_estimation_abci.rounds.CollectObservationRound.observation_threshold_reached"></a>

#### observation`_`threshold`_`reached

```python
@property
def observation_threshold_reached() -> bool
```

Check that the observation threshold has been reached.

<a id="packages.valory.skills.price_estimation_abci.rounds.CollectObservationRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BasePeriodState, AbstractRound]]
```

Process the end of the block.

<a id="packages.valory.skills.price_estimation_abci.rounds.EstimateConsensusRound"></a>

## EstimateConsensusRound Objects

```python
class EstimateConsensusRound(PriceEstimationAbstractRound)
```

This class represents the 'estimate_consensus' round.

Input: a period state with the prior round data
Ouptut: a new period state with the prior round data and the votes for each estimate

It schedules the TxHashRound.

<a id="packages.valory.skills.price_estimation_abci.rounds.EstimateConsensusRound.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any)
```

Initialize the 'estimate consensus' round.

<a id="packages.valory.skills.price_estimation_abci.rounds.EstimateConsensusRound.estimate"></a>

#### estimate

```python
def estimate(payload: EstimatePayload) -> None
```

Handle an 'estimate' payload.

<a id="packages.valory.skills.price_estimation_abci.rounds.EstimateConsensusRound.check_estimate"></a>

#### check`_`estimate

```python
def check_estimate(payload: EstimatePayload) -> None
```

Check an estimate payload can be applied to the current state.

An estimate transaction can be applied only if:
- the round is in the 'estimate_consensus' state;
- the sender belongs to the set of participants
- the sender has not sent its estimate yet
:param: payload: the payload.

<a id="packages.valory.skills.price_estimation_abci.rounds.EstimateConsensusRound.estimate_threshold_reached"></a>

#### estimate`_`threshold`_`reached

```python
@property
def estimate_threshold_reached() -> bool
```

Check that the estimate threshold has been reached.

<a id="packages.valory.skills.price_estimation_abci.rounds.EstimateConsensusRound.most_voted_estimate"></a>

#### most`_`voted`_`estimate

```python
@property
def most_voted_estimate() -> float
```

Get the most voted estimate.

<a id="packages.valory.skills.price_estimation_abci.rounds.EstimateConsensusRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BasePeriodState, AbstractRound]]
```

Process the end of the block.

<a id="packages.valory.skills.price_estimation_abci.rounds.TxHashRound"></a>

## TxHashRound Objects

```python
class TxHashRound(PriceEstimationAbstractRound)
```

This class represents the 'tx-hash' round.

Input: a period state with the prior round data
Ouptut: a new period state with the prior round data and the votes for each tx hash

It schedules the CollectSignatureRound.

<a id="packages.valory.skills.price_estimation_abci.rounds.TxHashRound.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any)
```

Initialize the 'collect-signature' round.

<a id="packages.valory.skills.price_estimation_abci.rounds.TxHashRound.tx_hash"></a>

#### tx`_`hash

```python
def tx_hash(payload: TransactionHashPayload) -> None
```

Handle a 'tx_hash' payload.

<a id="packages.valory.skills.price_estimation_abci.rounds.TxHashRound.check_tx_hash"></a>

#### check`_`tx`_`hash

```python
def check_tx_hash(payload: TransactionHashPayload) -> None
```

Check a signature payload can be applied to the current state.

This can happen only if:
- the round is in the 'tx_hash' state;
- the sender belongs to the set of participants
- the sender has not sent the tx_hash yet

**Arguments**:

- `payload`: the payload to check

<a id="packages.valory.skills.price_estimation_abci.rounds.TxHashRound.tx_threshold_reached"></a>

#### tx`_`threshold`_`reached

```python
@property
def tx_threshold_reached() -> bool
```

Check that the tx threshold has been reached.

<a id="packages.valory.skills.price_estimation_abci.rounds.TxHashRound.most_voted_tx_hash"></a>

#### most`_`voted`_`tx`_`hash

```python
@property
def most_voted_tx_hash() -> str
```

Get the most voted tx hash.

<a id="packages.valory.skills.price_estimation_abci.rounds.TxHashRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BasePeriodState, AbstractRound]]
```

Process the end of the block.

<a id="packages.valory.skills.price_estimation_abci.rounds.CollectSignatureRound"></a>

## CollectSignatureRound Objects

```python
class CollectSignatureRound(PriceEstimationAbstractRound)
```

This class represents the 'collect-signature' round.

Input: a period state with the prior round data
Ouptut: a new period state with the prior round data and the signatures

It schedules the FinalizationRound.

<a id="packages.valory.skills.price_estimation_abci.rounds.CollectSignatureRound.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any)
```

Initialize the 'collect-signature' round.

<a id="packages.valory.skills.price_estimation_abci.rounds.CollectSignatureRound.signature"></a>

#### signature

```python
def signature(payload: SignaturePayload) -> None
```

Handle a 'signature' payload.

<a id="packages.valory.skills.price_estimation_abci.rounds.CollectSignatureRound.check_signature"></a>

#### check`_`signature

```python
def check_signature(payload: SignaturePayload) -> None
```

Check a signature payload can be applied to the current state.

A signature transaction can be applied only if:
- the round is in the 'collect-signature' state;
- the sender belongs to the set of participants
- the sender has not sent its signature yet

:param: payload: the payload.

<a id="packages.valory.skills.price_estimation_abci.rounds.CollectSignatureRound.signature_threshold_reached"></a>

#### signature`_`threshold`_`reached

```python
@property
def signature_threshold_reached() -> bool
```

Check that the signature threshold has been reached.

<a id="packages.valory.skills.price_estimation_abci.rounds.CollectSignatureRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BasePeriodState, AbstractRound]]
```

Process the end of the block.

<a id="packages.valory.skills.price_estimation_abci.rounds.FinalizationRound"></a>

## FinalizationRound Objects

```python
class FinalizationRound(PriceEstimationAbstractRound)
```

This class represents the finalization Safe round.

Input: a period state with the prior round data
Output: a new period state with the prior round data and the hash of the Safe transaction

It schedules the ValidateTransactionRound.

<a id="packages.valory.skills.price_estimation_abci.rounds.FinalizationRound.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any)
```

Initialize the 'finalization' round.

<a id="packages.valory.skills.price_estimation_abci.rounds.FinalizationRound.finalization"></a>

#### finalization

```python
def finalization(payload: FinalizationTxPayload) -> None
```

Handle a finalization payload.

<a id="packages.valory.skills.price_estimation_abci.rounds.FinalizationRound.check_finalization"></a>

#### check`_`finalization

```python
def check_finalization(payload: FinalizationTxPayload) -> None
```

Check a finalization payload can be applied to the current state.

A finalization transaction can be applied only if:
- the sender belongs to the set of participants
- the sender is the elected sender
- the sender has not already sent the transaction hash

:param: payload: the payload.

<a id="packages.valory.skills.price_estimation_abci.rounds.FinalizationRound.tx_hash_set"></a>

#### tx`_`hash`_`set

```python
@property
def tx_hash_set() -> bool
```

Check that the tx hash has been set.

<a id="packages.valory.skills.price_estimation_abci.rounds.FinalizationRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BasePeriodState, AbstractRound]]
```

Process the end of the block.

<a id="packages.valory.skills.price_estimation_abci.rounds.SelectKeeperARound"></a>

## SelectKeeperARound Objects

```python
class SelectKeeperARound(SelectKeeperRound)
```

This class represents the select keeper A round.

<a id="packages.valory.skills.price_estimation_abci.rounds.SelectKeeperARound.select_keeper_a"></a>

#### select`_`keeper`_`a

```python
def select_keeper_a(payload: SelectKeeperPayload) -> None
```

Handle a 'select_keeper' payload.

<a id="packages.valory.skills.price_estimation_abci.rounds.SelectKeeperARound.check_select_keeper_a"></a>

#### check`_`select`_`keeper`_`a

```python
def check_select_keeper_a(payload: SelectKeeperPayload) -> None
```

Check an select_keeper payload can be applied to the current state.

<a id="packages.valory.skills.price_estimation_abci.rounds.SelectKeeperBRound"></a>

## SelectKeeperBRound Objects

```python
class SelectKeeperBRound(SelectKeeperRound)
```

This class represents the select keeper B round.

<a id="packages.valory.skills.price_estimation_abci.rounds.SelectKeeperBRound.select_keeper_b"></a>

#### select`_`keeper`_`b

```python
def select_keeper_b(payload: SelectKeeperPayload) -> None
```

Handle a 'select_keeper' payload.

<a id="packages.valory.skills.price_estimation_abci.rounds.SelectKeeperBRound.check_select_keeper_b"></a>

#### check`_`select`_`keeper`_`b

```python
def check_select_keeper_b(payload: SelectKeeperPayload) -> None
```

Check an select_keeper payload can be applied to the current state.

<a id="packages.valory.skills.price_estimation_abci.rounds.ConsensusReachedRound"></a>

## ConsensusReachedRound Objects

```python
class ConsensusReachedRound(PriceEstimationAbstractRound)
```

This class represents the 'consensus-reached' round (the final round).

<a id="packages.valory.skills.price_estimation_abci.rounds.ConsensusReachedRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BasePeriodState, AbstractRound]]
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

<a id="packages.valory.skills.price_estimation_abci.rounds.ValidateSafeRound.validate_safe"></a>

#### validate`_`safe

```python
def validate_safe(payload: ValidatePayload) -> None
```

Handle a validate payload.

:param: payload: the payload.

<a id="packages.valory.skills.price_estimation_abci.rounds.ValidateSafeRound.check_validate_safe"></a>

#### check`_`validate`_`safe

```python
def check_validate_safe(payload: ValidatePayload) -> None
```

Check a validate safe payload can be applied to the current state.

A deploy safe transaction can be applied only if:
- the sender belongs to the set of participants

:param: payload: the payload.

<a id="packages.valory.skills.price_estimation_abci.rounds.ValidateTransactionRound"></a>

## ValidateTransactionRound Objects

```python
class ValidateTransactionRound(ValidateRound)
```

This class represents the validate transaction round.

Input: a period state with the prior round data
Output: a new period state with the prior round data and the validation of the transaction

It schedules the ConsensusReachedRound or SelectKeeperARound.

<a id="packages.valory.skills.price_estimation_abci.rounds.ValidateTransactionRound.validate_transaction"></a>

#### validate`_`transaction

```python
def validate_transaction(payload: ValidatePayload) -> None
```

Handle a validate payload.

:param: payload: the payload.

<a id="packages.valory.skills.price_estimation_abci.rounds.ValidateTransactionRound.check_validate_transaction"></a>

#### check`_`validate`_`transaction

```python
def check_validate_transaction(payload: ValidatePayload) -> None
```

Check a validate transaction payload can be applied to the current state.

A deploy safe transaction can be applied only if:
- the sender belongs to the set of participants

:param: payload: the payload.

