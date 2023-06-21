<a id="packages.valory.skills.abstract_round_abci.background.pending_offences.behaviour"></a>

# packages.valory.skills.abstract`_`round`_`abci.background.pending`_`offences.behaviour

This module contains the pending offences ever-running background behaviour.

<a id="packages.valory.skills.abstract_round_abci.background.pending_offences.behaviour.PendingOffencesBehaviour"></a>

## PendingOffencesBehaviour Objects

```python
class PendingOffencesBehaviour(BaseBehaviour)
```

A behaviour responsible for checking whether there are any pending offences.

<a id="packages.valory.skills.abstract_round_abci.background.pending_offences.behaviour.PendingOffencesBehaviour.round_sequence"></a>

#### round`_`sequence

```python
@property
def round_sequence() -> RoundSequence
```

Get the round sequence from the shared state.

<a id="packages.valory.skills.abstract_round_abci.background.pending_offences.behaviour.PendingOffencesBehaviour.pending_offences"></a>

#### pending`_`offences

```python
@property
def pending_offences() -> Set[PendingOffense]
```

Get the pending offences from the round sequence.

<a id="packages.valory.skills.abstract_round_abci.background.pending_offences.behaviour.PendingOffencesBehaviour.has_pending_offences"></a>

#### has`_`pending`_`offences

```python
def has_pending_offences() -> bool
```

Check if there are any pending offences.

<a id="packages.valory.skills.abstract_round_abci.background.pending_offences.behaviour.PendingOffencesBehaviour.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Checks the pending offences.

This behaviour simply checks if the set of pending offences is not empty.
When it’s not empty, it pops the offence from the set, and sends it to the rest of the agents via a payload

**Returns**:

None

