<a id="autonomy.cli.scaffold_fsm"></a>

# autonomy.cli.scaffold`_`fsm

Implement a scaffold sub-command to scaffold ABCI skills.

This module patches the 'aea scaffold' command so to add a new subcommand for scaffolding a skill
 starting from FSM specification.

<a id="autonomy.cli.scaffold_fsm.AbstractFileGenerator"></a>

## AbstractFileGenerator Objects

```python
class AbstractFileGenerator(ABC)
```

An abstract class for file generators.

<a id="autonomy.cli.scaffold_fsm.AbstractFileGenerator.__init__"></a>

#### `__`init`__`

```python
def __init__(ctx: Context, skill_name: str, dfa: DFA) -> None
```

Initialize the abstract file generator.

<a id="autonomy.cli.scaffold_fsm.AbstractFileGenerator.get_file_content"></a>

#### get`_`file`_`content

```python
@abstractmethod
def get_file_content() -> str
```

Get file content.

<a id="autonomy.cli.scaffold_fsm.AbstractFileGenerator.write_file"></a>

#### write`_`file

```python
def write_file(output_dir: Path) -> None
```

Write the file to output_dir/FILENAME.

<a id="autonomy.cli.scaffold_fsm.AbstractFileGenerator.abci_app_name"></a>

#### abci`_`app`_`name

```python
@property
def abci_app_name() -> str
```

ABCI app class name

<a id="autonomy.cli.scaffold_fsm.AbstractFileGenerator.fsm_name"></a>

#### fsm`_`name

```python
@property
def fsm_name() -> str
```

FSM base name

<a id="autonomy.cli.scaffold_fsm.AbstractFileGenerator.author"></a>

#### author

```python
@property
def author() -> str
```

Author

<a id="autonomy.cli.scaffold_fsm.AbstractFileGenerator.all_rounds"></a>

#### all`_`rounds

```python
@property
def all_rounds() -> List[str]
```

Rounds

<a id="autonomy.cli.scaffold_fsm.AbstractFileGenerator.degenerate_rounds"></a>

#### degenerate`_`rounds

```python
@property
def degenerate_rounds() -> List[str]
```

Degenerate rounds

<a id="autonomy.cli.scaffold_fsm.AbstractFileGenerator.rounds"></a>

#### rounds

```python
@property
def rounds() -> List[str]
```

Non-degenerate rounds

<a id="autonomy.cli.scaffold_fsm.AbstractFileGenerator.base_names"></a>

#### base`_`names

```python
@property
def base_names() -> List[str]
```

Base names

<a id="autonomy.cli.scaffold_fsm.AbstractFileGenerator.behaviours"></a>

#### behaviours

```python
@property
def behaviours() -> List[str]
```

Behaviours

<a id="autonomy.cli.scaffold_fsm.AbstractFileGenerator.payloads"></a>

#### payloads

```python
@property
def payloads() -> List[str]
```

Payloads

<a id="autonomy.cli.scaffold_fsm.RoundFileGenerator"></a>

## RoundFileGenerator Objects

```python
class RoundFileGenerator(AbstractFileGenerator)
```

File generator for 'rounds.py' modules.

<a id="autonomy.cli.scaffold_fsm.RoundFileGenerator.get_file_content"></a>

#### get`_`file`_`content

```python
def get_file_content() -> str
```

Scaffold the 'rounds.py' file.

<a id="autonomy.cli.scaffold_fsm.BehaviourFileGenerator"></a>

## BehaviourFileGenerator Objects

```python
class BehaviourFileGenerator(AbstractFileGenerator)
```

File generator for 'behaviours.py' modules.

<a id="autonomy.cli.scaffold_fsm.BehaviourFileGenerator.get_file_content"></a>

#### get`_`file`_`content

```python
def get_file_content() -> str
```

Scaffold the 'behaviours.py' file.

<a id="autonomy.cli.scaffold_fsm.PayloadsFileGenerator"></a>

## PayloadsFileGenerator Objects

```python
class PayloadsFileGenerator(AbstractFileGenerator)
```

File generator for 'payloads.py' modules.

<a id="autonomy.cli.scaffold_fsm.PayloadsFileGenerator.get_file_content"></a>

#### get`_`file`_`content

```python
def get_file_content() -> str
```

Get the file content.

<a id="autonomy.cli.scaffold_fsm.ModelsFileGenerator"></a>

## ModelsFileGenerator Objects

```python
class ModelsFileGenerator(AbstractFileGenerator)
```

File generator for 'models.py' modules.

<a id="autonomy.cli.scaffold_fsm.ModelsFileGenerator.get_file_content"></a>

#### get`_`file`_`content

```python
def get_file_content() -> str
```

Get the file content.

<a id="autonomy.cli.scaffold_fsm.HandlersFileGenerator"></a>

## HandlersFileGenerator Objects

```python
class HandlersFileGenerator(AbstractFileGenerator)
```

File generator for 'handlers.py' modules.

<a id="autonomy.cli.scaffold_fsm.HandlersFileGenerator.get_file_content"></a>

#### get`_`file`_`content

```python
def get_file_content() -> str
```

Get the file content.

<a id="autonomy.cli.scaffold_fsm.DialoguesFileGenerator"></a>

## DialoguesFileGenerator Objects

```python
class DialoguesFileGenerator(AbstractFileGenerator)
```

File generator for 'dialogues.py' modules.

<a id="autonomy.cli.scaffold_fsm.DialoguesFileGenerator.get_file_content"></a>

#### get`_`file`_`content

```python
def get_file_content() -> str
```

Get the file content.

<a id="autonomy.cli.scaffold_fsm.SkillConfigUpdater"></a>

## SkillConfigUpdater Objects

```python
class SkillConfigUpdater()
```

Update the skill configuration according to the Abci classes.

<a id="autonomy.cli.scaffold_fsm.SkillConfigUpdater.__init__"></a>

#### `__`init`__`

```python
def __init__(ctx: Context, skill_dir: Path, dfa: DFA) -> None
```

Initialize the skill config updater.

**Arguments**:

- `ctx`: the AEA CLI context object.
- `skill_dir`: the directory of the AEA skill package.
- `dfa`: the DFA object.

<a id="autonomy.cli.scaffold_fsm.SkillConfigUpdater.update"></a>

#### update

```python
def update() -> None
```

Update the skill configuration file.

<a id="autonomy.cli.scaffold_fsm.RoundTestsFileGenerator"></a>

## RoundTestsFileGenerator Objects

```python
class RoundTestsFileGenerator(AbstractFileGenerator)
```

RoundTestsFileGenerator

<a id="autonomy.cli.scaffold_fsm.RoundTestsFileGenerator.get_file_content"></a>

#### get`_`file`_`content

```python
def get_file_content() -> str
```

Scaffold the 'test_rounds.py' file.

<a id="autonomy.cli.scaffold_fsm.BehaviourTestsFileGenerator"></a>

## BehaviourTestsFileGenerator Objects

```python
class BehaviourTestsFileGenerator(AbstractFileGenerator)
```

File generator for 'test_behaviours.py' modules.

<a id="autonomy.cli.scaffold_fsm.BehaviourTestsFileGenerator.get_file_content"></a>

#### get`_`file`_`content

```python
def get_file_content() -> str
```

Scaffold the 'test_behaviours.py' file.

<a id="autonomy.cli.scaffold_fsm.PayloadTestsFileGenerator"></a>

## PayloadTestsFileGenerator Objects

```python
class PayloadTestsFileGenerator(AbstractFileGenerator)
```

File generator for 'test_payloads.py' modules.

<a id="autonomy.cli.scaffold_fsm.PayloadTestsFileGenerator.get_file_content"></a>

#### get`_`file`_`content

```python
def get_file_content() -> str
```

Scaffold the 'test_payloads.py' file.

<a id="autonomy.cli.scaffold_fsm.ModelTestFileGenerator"></a>

## ModelTestFileGenerator Objects

```python
class ModelTestFileGenerator(AbstractFileGenerator)
```

File generator for 'test_models.py'.

<a id="autonomy.cli.scaffold_fsm.ModelTestFileGenerator.get_file_content"></a>

#### get`_`file`_`content

```python
def get_file_content() -> str
```

Get the file content.

<a id="autonomy.cli.scaffold_fsm.HandlersTestFileGenerator"></a>

## HandlersTestFileGenerator Objects

```python
class HandlersTestFileGenerator(AbstractFileGenerator)
```

File generator for 'test_dialogues.py'.

<a id="autonomy.cli.scaffold_fsm.HandlersTestFileGenerator.get_file_content"></a>

#### get`_`file`_`content

```python
def get_file_content() -> str
```

Get the file content.

<a id="autonomy.cli.scaffold_fsm.DialoguesTestFileGenerator"></a>

## DialoguesTestFileGenerator Objects

```python
class DialoguesTestFileGenerator(AbstractFileGenerator)
```

File generator for 'test_dialogues.py'.

<a id="autonomy.cli.scaffold_fsm.DialoguesTestFileGenerator.get_file_content"></a>

#### get`_`file`_`content

```python
def get_file_content() -> str
```

Get the file content.

<a id="autonomy.cli.scaffold_fsm.ScaffoldABCISkill"></a>

## ScaffoldABCISkill Objects

```python
class ScaffoldABCISkill()
```

Utility class that implements the scaffolding of the ABCI skill.

<a id="autonomy.cli.scaffold_fsm.ScaffoldABCISkill.__init__"></a>

#### `__`init`__`

```python
def __init__(ctx: Context, skill_name: str, dfa: DFA) -> None
```

Initialize the utility class.

<a id="autonomy.cli.scaffold_fsm.ScaffoldABCISkill.skill_dir"></a>

#### skill`_`dir

```python
@property
def skill_dir() -> Path
```

Get the directory to the skill.

<a id="autonomy.cli.scaffold_fsm.ScaffoldABCISkill.skill_test_dir"></a>

#### skill`_`test`_`dir

```python
@property
def skill_test_dir() -> Path
```

Get the directory to the skill tests.

<a id="autonomy.cli.scaffold_fsm.ScaffoldABCISkill.do_scaffolding"></a>

#### do`_`scaffolding

```python
def do_scaffolding() -> None
```

Do the scaffolding.

<a id="autonomy.cli.scaffold_fsm.fsm"></a>

#### fsm

```python
@scaffold.command()  # noqa
@registry_flag()
@click.argument("skill_name", type=str, required=True)
@click.option("--spec", type=click.Path(exists=True, dir_okay=False), required=True)
@pass_ctx
def fsm(ctx: Context, registry: str, skill_name: str, spec: str) -> None
```

Add an ABCI skill scaffolding from an FSM specification.

