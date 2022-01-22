<a id="packages.valory.skills.abstract_round_abci.abci_app_chain"></a>

# packages.valory.skills.abstract`_`round`_`abci.abci`_`app`_`chain

This module contains utilities for AbciApps.

<a id="packages.valory.skills.abstract_round_abci.abci_app_chain.chain"></a>

#### chain

```python
def chain(abci_apps: Tuple[Type[AbciApp], ...], abci_app_transition_mapping: AbciAppTransitionMapping) -> Type[AbciApp]
```

Concatenate multiple AbciApp types.

