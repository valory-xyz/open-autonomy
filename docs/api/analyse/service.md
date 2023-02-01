<a id="autonomy.analyse.service"></a>

# autonomy.analyse.service

Tools for analysing the service for deployment readiness

<a id="autonomy.analyse.service.ServiceValidationFailed"></a>

## ServiceValidationFailed Objects

```python
class ServiceValidationFailed(Exception)
```

Raise when service validation fails.

<a id="autonomy.analyse.service.ServiceAnalyser"></a>

## ServiceAnalyser Objects

```python
class ServiceAnalyser()
```

Tools to analyse a service

<a id="autonomy.analyse.service.ServiceAnalyser.__init__"></a>

#### `__`init`__`

```python
def __init__(service_path: Path) -> None
```

Initialise object.

<a id="autonomy.analyse.service.ServiceAnalyser.check_on_chain_state"></a>

#### check`_`on`_`chain`_`state

```python
@staticmethod
def check_on_chain_state(ledger_api: LedgerApi, chain_type: ChainType, token_id: int) -> None
```

Check on-chain state of a service.

<a id="autonomy.analyse.service.ServiceAnalyser.check_agent_package_published"></a>

#### check`_`agent`_`package`_`published

```python
def check_agent_package_published(ipfs_pins: Set[str]) -> None
```

Check if the agent package is published or not

<a id="autonomy.analyse.service.ServiceAnalyser.check_agent_dependencies_published"></a>

#### check`_`agent`_`dependencies`_`published

```python
def check_agent_dependencies_published(agent_config: AgentConfig, ipfs_pins: Set[str]) -> None
```

Check if the agent package is published or not

<a id="autonomy.analyse.service.ServiceAnalyser.verify_overrides"></a>

#### verify`_`overrides

```python
def verify_overrides(agent_config: AgentConfig) -> None
```

Cross verify overrides between service config and agent config

<a id="autonomy.analyse.service.ServiceAnalyser.check_skill_override"></a>

#### check`_`skill`_`override

```python
@staticmethod
def check_skill_override(override: Dict) -> None
```

Check skill override.

<a id="autonomy.analyse.service.ServiceAnalyser.check_required_overrides"></a>

#### check`_`required`_`overrides

```python
def check_required_overrides() -> None
```

Check required overrides.

