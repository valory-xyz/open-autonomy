<a id="packages.valory.skills.abstract_round_abci.abci_app_chain"></a>

# packages.valory.skills.abstract`_`round`_`abci.abci`_`app`_`chain

This module contains utilities for AbciApps.

<a id="packages.valory.skills.abstract_round_abci.abci_app_chain.check_set_uniqueness"></a>

#### check`_`set`_`uniqueness

```python
def check_set_uniqueness(sets: Tuple) -> Optional[Any]
```

Checks that all elements in the set list are unique and not repeated among different sets

<a id="packages.valory.skills.abstract_round_abci.abci_app_chain.chain"></a>

#### chain

```python
def chain(
        abci_apps: Tuple[Type[AbciApp], ...],
        abci_app_transition_mapping: AbciAppTransitionMapping
) -> Type[AbciApp]
```

Concatenate multiple AbciApp types.

The consistency checks assume that the first element in
abci_apps is the entry-point abci_app (i.e. the associated round of
the  initial_behaviour_cls of the AbstractRoundBehaviour in which
the chained AbciApp is used is one of the initial_states of the first element.)

