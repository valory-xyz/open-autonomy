<a id="packages.valory.skills.registration_abci.behaviours"></a>

# packages.valory.skills.registration`_`abci.behaviours

This module contains the behaviours for the 'abci' skill.

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

<a id="packages.valory.skills.registration_abci.behaviours.RegistrationStartupBehaviour.registered_addresses"></a>

#### registered`_`addresses

```python
@property
def registered_addresses() -> Set[str]
```

Agent addresses registered on-chain for the service

<a id="packages.valory.skills.registration_abci.behaviours.RegistrationStartupBehaviour.is_correct_contract"></a>

#### is`_`correct`_`contract

```python
def is_correct_contract() -> Generator[None, None, bool]
```

Contract deployment verification.

<a id="packages.valory.skills.registration_abci.behaviours.RegistrationStartupBehaviour.get_service_info"></a>

#### get`_`service`_`info

```python
def get_service_info() -> Generator[None, None, dict]
```

Get service info available on-chain

<a id="packages.valory.skills.registration_abci.behaviours.RegistrationStartupBehaviour.get_addresses"></a>

#### get`_`addresses

```python
def get_addresses() -> Generator[None, None, bool]
```

Get addresses of agents registered for the service

<a id="packages.valory.skills.registration_abci.behaviours.RegistrationStartupBehaviour.make_tendermint_request"></a>

#### make`_`tendermint`_`request

```python
def make_tendermint_request(address: str) -> None
```

Make Tendermint callback request

<a id="packages.valory.skills.registration_abci.behaviours.RegistrationStartupBehaviour.process_response"></a>

#### process`_`response

```python
def process_response(message: TendermintMessage) -> None
```

Process tendermint response messages

<a id="packages.valory.skills.registration_abci.behaviours.RegistrationStartupBehaviour.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Act asynchronously

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

