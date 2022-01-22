<a id="packages.valory.skills.registration_abci.behaviours"></a>

# packages.valory.skills.registration`_`abci.behaviours

This module contains the behaviours for the 'abci' skill.

<a id="packages.valory.skills.registration_abci.behaviours.TendermintHealthcheckBehaviour"></a>

## TendermintHealthcheckBehaviour Objects

```python
class TendermintHealthcheckBehaviour(BaseState)
```

Check whether Tendermint nodes are running.

<a id="packages.valory.skills.registration_abci.behaviours.TendermintHealthcheckBehaviour.start"></a>

#### start

```python
def start() -> None
```

Set up the behaviour.

<a id="packages.valory.skills.registration_abci.behaviours.TendermintHealthcheckBehaviour.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Do the action.

<a id="packages.valory.skills.registration_abci.behaviours.RegistrationBaseBehaviour"></a>

## RegistrationBaseBehaviour Objects

```python
class RegistrationBaseBehaviour(BaseState)
```

Register to the next periods.

<a id="packages.valory.skills.registration_abci.behaviours.RegistrationBaseBehaviour.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Do the action.

Steps:
- Build a registration transaction.
- Send the transaction and wait for it to be mined.
- Wait until ABCI application transitions to the next round.
- Go to the next behaviour state (set done event).

<a id="packages.valory.skills.registration_abci.behaviours.RegistrationStartupBehaviour"></a>

## RegistrationStartupBehaviour Objects

```python
class RegistrationStartupBehaviour(RegistrationBaseBehaviour)
```

Register to the next periods.

<a id="packages.valory.skills.registration_abci.behaviours.RegistrationBehaviour"></a>

## RegistrationBehaviour Objects

```python
class RegistrationBehaviour(RegistrationBaseBehaviour)
```

Register to the next periods.

<a id="packages.valory.skills.registration_abci.behaviours.AgentRegistrationRoundBehaviour"></a>

## AgentRegistrationRoundBehaviour Objects

```python
class AgentRegistrationRoundBehaviour(AbstractRoundBehaviour)
```

This behaviour manages the consensus stages for the registration.

