<a id="autonomy.fsm.scaffold.generators.components"></a>

# autonomy.fsm.scaffold.generators.components

Component generators.

<a id="autonomy.fsm.scaffold.generators.components.SimpleFileGenerator"></a>

## SimpleFileGenerator Objects

```python
class SimpleFileGenerator(AbstractFileGenerator)
```

For files that require minimal formatting

<a id="autonomy.fsm.scaffold.generators.components.SimpleFileGenerator.get_file_content"></a>

#### get`_`file`_`content

```python
def get_file_content() -> str
```

Get the file content.

<a id="autonomy.fsm.scaffold.generators.components.RoundFileGenerator"></a>

## RoundFileGenerator Objects

```python
class RoundFileGenerator(AbstractFileGenerator, ROUNDS)
```

File generator for 'rounds.py' modules.

<a id="autonomy.fsm.scaffold.generators.components.RoundFileGenerator.get_file_content"></a>

#### get`_`file`_`content

```python
def get_file_content() -> str
```

Scaffold the 'rounds.py' file.

<a id="autonomy.fsm.scaffold.generators.components.BehaviourFileGenerator"></a>

## BehaviourFileGenerator Objects

```python
class BehaviourFileGenerator(AbstractFileGenerator, BEHAVIOURS)
```

File generator for 'behaviours.py' modules.

<a id="autonomy.fsm.scaffold.generators.components.BehaviourFileGenerator.get_file_content"></a>

#### get`_`file`_`content

```python
def get_file_content() -> str
```

Scaffold the 'behaviours.py' file.

<a id="autonomy.fsm.scaffold.generators.components.PayloadsFileGenerator"></a>

## PayloadsFileGenerator Objects

```python
class PayloadsFileGenerator(AbstractFileGenerator, PAYLOADS)
```

File generator for 'payloads.py' modules.

<a id="autonomy.fsm.scaffold.generators.components.PayloadsFileGenerator.get_file_content"></a>

#### get`_`file`_`content

```python
def get_file_content() -> str
```

Get the file content.

<a id="autonomy.fsm.scaffold.generators.components.ModelsFileGenerator"></a>

## ModelsFileGenerator Objects

```python
class ModelsFileGenerator(SimpleFileGenerator, MODELS)
```

File generator for 'models.py' modules.

<a id="autonomy.fsm.scaffold.generators.components.HandlersFileGenerator"></a>

## HandlersFileGenerator Objects

```python
class HandlersFileGenerator(SimpleFileGenerator, HANDLERS)
```

File generator for 'handlers.py' modules.

<a id="autonomy.fsm.scaffold.generators.components.DialoguesFileGenerator"></a>

## DialoguesFileGenerator Objects

```python
class DialoguesFileGenerator(SimpleFileGenerator, DIALOGUES)
```

File generator for 'dialogues.py' modules.

