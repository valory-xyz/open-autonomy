<a id="autonomy.fsm.scaffold.scaffold_skill"></a>

# autonomy.fsm.scaffold.scaffold`_`skill

Scaffold skill from an FSM

<a id="autonomy.fsm.scaffold.scaffold_skill.SkillConfigUpdater"></a>

## SkillConfigUpdater Objects

```python
class SkillConfigUpdater()
```

Update the skill configuration according to the Abci classes.

<a id="autonomy.fsm.scaffold.scaffold_skill.SkillConfigUpdater.__init__"></a>

#### `__`init`__`

```python
def __init__(ctx: Context, skill_dir: Path, dfa: DFA) -> None
```

Initialize the skill config updater.

**Arguments**:

- `ctx`: the AEA CLI context object.
- `skill_dir`: the directory of the AEA skill package.
- `dfa`: the DFA object.

<a id="autonomy.fsm.scaffold.scaffold_skill.SkillConfigUpdater.update"></a>

#### update

```python
def update() -> None
```

Update the skill configuration file.

<a id="autonomy.fsm.scaffold.scaffold_skill.SkillConfigUpdater.get_actual_abstract_round_abci_package_public_id"></a>

#### get`_`actual`_`abstract`_`round`_`abci`_`package`_`public`_`id

```python
@classmethod
def get_actual_abstract_round_abci_package_public_id(
        cls, ctx: Context) -> Optional[PublicId]
```

Get abstract round abci pacakge id from the registry.

<a id="autonomy.fsm.scaffold.scaffold_skill.ScaffoldABCISkill"></a>

## ScaffoldABCISkill Objects

```python
class ScaffoldABCISkill()
```

Utility class that implements the scaffolding of the ABCI skill.

<a id="autonomy.fsm.scaffold.scaffold_skill.ScaffoldABCISkill.__init__"></a>

#### `__`init`__`

```python
def __init__(ctx: Context, skill_name: str, spec_path: Path) -> None
```

Initialize the utility class.

<a id="autonomy.fsm.scaffold.scaffold_skill.ScaffoldABCISkill.skill_dir"></a>

#### skill`_`dir

```python
@property
def skill_dir() -> Path
```

Get the directory to the skill.

<a id="autonomy.fsm.scaffold.scaffold_skill.ScaffoldABCISkill.skill_test_dir"></a>

#### skill`_`test`_`dir

```python
@property
def skill_test_dir() -> Path
```

Get the directory to the skill tests.

<a id="autonomy.fsm.scaffold.scaffold_skill.ScaffoldABCISkill.do_scaffolding"></a>

#### do`_`scaffolding

```python
def do_scaffolding() -> None
```

Do the scaffolding.

<a id="autonomy.fsm.scaffold.scaffold_skill.ScaffoldABCISkill.add_skill_to_packages"></a>

#### add`_`skill`_`to`_`packages

```python
def add_skill_to_packages() -> None
```

Add skill to packages.json if scaffolded to local packages repository

