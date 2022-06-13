<a id="autonomy.cli.utils.click_utils"></a>

# autonomy.cli.utils.click`_`utils

Usefule click utils.

<a id="autonomy.cli.utils.click_utils.image_profile_flag"></a>

#### image`_`profile`_`flag

```python
def image_profile_flag(default: str = ImageProfiles.PRODUCTION, mark_default: bool = True) -> Callable
```

Choice of one flag between: '--local/--remote'.

<a id="autonomy.cli.utils.click_utils.abci_spec_format_flag"></a>

#### abci`_`spec`_`format`_`flag

```python
def abci_spec_format_flag(default: str = DFA.OutputFormats.YAML, mark_default: bool = True) -> Callable
```

Flags for abci spec outputs formats.

