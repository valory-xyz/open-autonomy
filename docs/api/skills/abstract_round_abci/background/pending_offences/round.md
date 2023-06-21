<a id="packages.valory.skills.abstract_round_abci.background.pending_offences.round"></a>

# packages.valory.skills.abstract`_`round`_`abci.background.pending`_`offences.round

This module contains the pending offences round.

<a id="packages.valory.skills.abstract_round_abci.background.pending_offences.round.PendingOffencesRound"></a>

## PendingOffencesRound Objects

```python
class PendingOffencesRound(CollectSameUntilThresholdRound)
```

Defines the pending offences background round, which runs concurrently with other rounds to sync the offences.

<a id="packages.valory.skills.abstract_round_abci.background.pending_offences.round.PendingOffencesRound.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any) -> None
```

Initialize the `PendingOffencesRound`.

<a id="packages.valory.skills.abstract_round_abci.background.pending_offences.round.PendingOffencesRound.offence_status"></a>

#### offence`_`status

```python
@property
def offence_status() -> Dict[str, OffenceStatus]
```

Get the offence status from the round sequence.

<a id="packages.valory.skills.abstract_round_abci.background.pending_offences.round.PendingOffencesRound.end_block"></a>

#### end`_`block

```python
def end_block() -> None
```

Process the end of the block for the pending offences background round.

It is important to note that this is a non-standard type of round, meaning it does not emit any events.
Instead, it continuously runs in the background.
The objective of this round is to consistently monitor the received pending offences
and achieve a consensus among the agents.

