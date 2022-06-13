<a id="autonomy.configurations.validation"></a>

# autonomy.configurations.validation

Config validators.

<a id="autonomy.configurations.validation.ConfigValidator"></a>

## ConfigValidator Objects

```python
class ConfigValidator(validation.ConfigValidator)
```

Configuration validator implementation.

<a id="autonomy.configurations.validation.ConfigValidator.__init__"></a>

#### `__`init`__`

```python
def __init__(schema_filename: str, env_vars_friendly: bool = False) -> None
```

Initialize the parser for configuration files.

**Arguments**:

- `schema_filename`: the path to the JSON-schema file in 'aea/configurations/schemas'.
- `env_vars_friendly`: whether or not it is env var friendly.

