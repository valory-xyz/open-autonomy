<a id="autonomy.fsm.scaffold.generators.tests"></a>

# autonomy.fsm.scaffold.generators.tests

Test generators.

<a id="autonomy.fsm.scaffold.generators.tests.RoundTestsFileGenerator"></a>

## RoundTestsFileGenerator Objects

```python
class RoundTestsFileGenerator(AbstractFileGenerator, TEST_ROUNDS)
```

RoundTestsFileGenerator

<a id="autonomy.fsm.scaffold.generators.tests.RoundTestsFileGenerator.get_file_content"></a>

#### get`_`file`_`content

```python
def get_file_content() -> str
```

Scaffold the 'test_rounds.py' file.

<a id="autonomy.fsm.scaffold.generators.tests.BehaviourTestsFileGenerator"></a>

## BehaviourTestsFileGenerator Objects

```python
class BehaviourTestsFileGenerator(AbstractFileGenerator, TEST_BEHAVIOURS)
```

File generator for 'test_behaviours.py' modules.

<a id="autonomy.fsm.scaffold.generators.tests.BehaviourTestsFileGenerator.get_file_content"></a>

#### get`_`file`_`content

```python
def get_file_content() -> str
```

Scaffold the 'test_behaviours.py' file.

<a id="autonomy.fsm.scaffold.generators.tests.PayloadTestsFileGenerator"></a>

## PayloadTestsFileGenerator Objects

```python
class PayloadTestsFileGenerator(AbstractFileGenerator, TEST_PAYLOADS)
```

File generator for 'test_payloads.py' modules.

<a id="autonomy.fsm.scaffold.generators.tests.PayloadTestsFileGenerator.get_file_content"></a>

#### get`_`file`_`content

```python
def get_file_content() -> str
```

Scaffold the 'test_payloads.py' file.

<a id="autonomy.fsm.scaffold.generators.tests.ModelTestFileGenerator"></a>

## ModelTestFileGenerator Objects

```python
class ModelTestFileGenerator(SimpleFileGenerator, TEST_MODELS)
```

File generator for 'test_models.py'.

<a id="autonomy.fsm.scaffold.generators.tests.HandlersTestFileGenerator"></a>

## HandlersTestFileGenerator Objects

```python
class HandlersTestFileGenerator(SimpleFileGenerator, TEST_HANDLERS)
```

File generator for 'test_dialogues.py'.

<a id="autonomy.fsm.scaffold.generators.tests.DialoguesTestFileGenerator"></a>

## DialoguesTestFileGenerator Objects

```python
class DialoguesTestFileGenerator(SimpleFileGenerator, TEST_DIALOGUES)
```

File generator for 'test_dialogues.py'.

