<a id="autonomy.analyse.service"></a>

# autonomy.analyse.service

Tools for analysing the service for deployment readiness

<a id="autonomy.analyse.service.CustomSchemaValidationError"></a>

## CustomSchemaValidationError Objects

```python
class CustomSchemaValidationError(SchemaValidationError)
```

Custom schema validation error to report all errors at once.

<a id="autonomy.analyse.service.CustomSchemaValidationError.__init__"></a>

#### `__`init`__`

```python
def __init__(extra_properties: Optional[List[str]] = None,
             missing_properties: Optional[List[str]] = None,
             not_having_enough_properties: Optional[List[str]] = None,
             **kwargs: Any) -> None
```

Initialize object.

<a id="autonomy.analyse.service.CustomSchemaValidator"></a>

## CustomSchemaValidator Objects

```python
class CustomSchemaValidator(Draft4Validator)
```

Custom schema validator to report all missing fields at once.

<a id="autonomy.analyse.service.CustomSchemaValidator.validate"></a>

#### validate

```python
def validate(*args: Any, **kwargs: Any) -> None
```

Validate and raise all errors at once.

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
def __init__(service_config: Service,
             abci_skill_id: PublicId,
             is_on_chain_check: bool = False,
             logger: Optional[logging.Logger] = None,
             skip_warnings: bool = False) -> None
```

Initialise object.

<a id="autonomy.analyse.service.ServiceAnalyser.check_on_chain_state"></a>

#### check`_`on`_`chain`_`state

```python
def check_on_chain_state(ledger_api: LedgerApi, chain_type: ChainType,
                         token_id: int) -> None
```

Check on-chain state of a service.

<a id="autonomy.analyse.service.ServiceAnalyser.check_agent_dependencies_published"></a>

#### check`_`agent`_`dependencies`_`published

```python
def check_agent_dependencies_published(agent_config: AgentConfig,
                                       ipfs_pins: Set[str]) -> None
```

Check if the agent package is published or not

<a id="autonomy.analyse.service.ServiceAnalyser.cross_verify_overrides"></a>

#### cross`_`verify`_`overrides

```python
def cross_verify_overrides(agent_config: AgentConfig,
                           skill_config: SkillConfig) -> None
```

Cross verify overrides between service config and agent config

<a id="autonomy.analyse.service.ServiceAnalyser.validate_override_env_vars"></a>

#### validate`_`override`_`env`_`vars

```python
@classmethod
def validate_override_env_vars(
        cls,
        overrides: Union[OrderedDict, dict],
        validate_env_var_name: bool = False,
        json_path: Optional[List[str]] = None) -> List[str]
```

Validate environment variables.

<a id="autonomy.analyse.service.ServiceAnalyser.validate_agent_override_env_vars"></a>

#### validate`_`agent`_`override`_`env`_`vars

```python
def validate_agent_override_env_vars(agent_config: AgentConfig) -> None
```

Check if all of the overrides are defined as a env vars in the agent config

<a id="autonomy.analyse.service.ServiceAnalyser.validate_service_override_env_vars"></a>

#### validate`_`service`_`override`_`env`_`vars

```python
def validate_service_override_env_vars() -> None
```

Check if all of the overrides are defined as a env vars in the agent config

<a id="autonomy.analyse.service.ServiceAnalyser.validate_override"></a>

#### validate`_`override

```python
def validate_override(component_id: ComponentId, override: Dict,
                      has_multiple_overrides: bool) -> None
```

Validate override

<a id="autonomy.analyse.service.ServiceAnalyser.validate_skill_config"></a>

#### validate`_`skill`_`config

```python
def validate_skill_config(skill_config: SkillConfig) -> None
```

Check required overrides.

<a id="autonomy.analyse.service.ServiceAnalyser.validate_agent_overrides"></a>

#### validate`_`agent`_`overrides

```python
def validate_agent_overrides(agent_config: AgentConfig) -> None
```

Check required overrides.

<a id="autonomy.analyse.service.ServiceAnalyser.validate_service_overrides"></a>

#### validate`_`service`_`overrides

```python
def validate_service_overrides() -> None
```

Check required overrides.

