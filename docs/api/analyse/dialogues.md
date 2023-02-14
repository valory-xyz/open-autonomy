<a id="autonomy.analyse.dialogues"></a>

# autonomy.analyse.dialogues

Analyse dialogue definitions.

<a id="autonomy.analyse.dialogues.load_dialogues_module_from_skill_path"></a>

#### load`_`dialogues`_`module`_`from`_`skill`_`path

```python
def load_dialogues_module_from_skill_path(
        skill_path: Path) -> types.ModuleType
```

Load `dialogues.py` module for the given skill.

<a id="autonomy.analyse.dialogues.validate_and_get_dialogues"></a>

#### validate`_`and`_`get`_`dialogues

```python
def validate_and_get_dialogues(
        models_configuration: Dict[str, Dict[str, str]]) -> Dict[str, str]
```

Returns dialogue names to class name mappings

<a id="autonomy.analyse.dialogues.check_dialogues_in_a_skill_package"></a>

#### check`_`dialogues`_`in`_`a`_`skill`_`package

```python
def check_dialogues_in_a_skill_package(config_file: Path,
                                       dialogues: List[str]) -> None
```

Check dialogue definitions.

