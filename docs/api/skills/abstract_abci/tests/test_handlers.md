<a id="packages.valory.skills.abstract_abci.tests.test_handlers"></a>

# packages.valory.skills.abstract`_`abci.tests.test`_`handlers

Test the handlers.py module of the skill.

<a id="packages.valory.skills.abstract_abci.tests.test_handlers.AbciDialoguesServer"></a>

## AbciDialoguesServer Objects

```python
class AbciDialoguesServer(BaseAbciDialogues)
```

The dialogues class keeps track of all ABCI dialogues.

<a id="packages.valory.skills.abstract_abci.tests.test_handlers.AbciDialoguesServer.__init__"></a>

#### `__`init`__`

```python
def __init__(address: str) -> None
```

Initialize dialogues.

<a id="packages.valory.skills.abstract_abci.tests.test_handlers.TestABCIHandlerOld"></a>

## TestABCIHandlerOld Objects

```python
class TestABCIHandlerOld(BaseSkillTestCase)
```

Test ABCIHandler methods.

<a id="packages.valory.skills.abstract_abci.tests.test_handlers.TestABCIHandlerOld.setup"></a>

#### setup

```python
@classmethod
def setup(cls, **kwargs: Any) -> None
```

Setup the test class.

<a id="packages.valory.skills.abstract_abci.tests.test_handlers.TestABCIHandlerOld.test_setup"></a>

#### test`_`setup

```python
def test_setup() -> None
```

Test the setup method of the echo handler.

<a id="packages.valory.skills.abstract_abci.tests.test_handlers.TestABCIHandlerOld.test_teardown"></a>

#### test`_`teardown

```python
def test_teardown() -> None
```

Test the teardown method of the echo handler.

<a id="packages.valory.skills.abstract_abci.tests.test_handlers.TestABCIHandler"></a>

## TestABCIHandler Objects

```python
class TestABCIHandler()
```

Test 'ABCIHandler'.

<a id="packages.valory.skills.abstract_abci.tests.test_handlers.TestABCIHandler.setup"></a>

#### setup

```python
def setup() -> None
```

Set up the tests.

<a id="packages.valory.skills.abstract_abci.tests.test_handlers.TestABCIHandler.test_setup"></a>

#### test`_`setup

```python
def test_setup() -> None
```

Test the setup method.

<a id="packages.valory.skills.abstract_abci.tests.test_handlers.TestABCIHandler.test_teardown"></a>

#### test`_`teardown

```python
def test_teardown() -> None
```

Test the teardown method.

<a id="packages.valory.skills.abstract_abci.tests.test_handlers.TestABCIHandler.test_handle"></a>

#### test`_`handle

```python
def test_handle() -> None
```

Test the message gets handled.

<a id="packages.valory.skills.abstract_abci.tests.test_handlers.TestABCIHandler.test_handle_log_exception"></a>

#### test`_`handle`_`log`_`exception

```python
def test_handle_log_exception() -> None
```

Test the message gets handled.

<a id="packages.valory.skills.abstract_abci.tests.test_handlers.TestABCIHandler.test_info"></a>

#### test`_`info

```python
def test_info() -> None
```

Test the 'info' handler method.

<a id="packages.valory.skills.abstract_abci.tests.test_handlers.TestABCIHandler.test_echo"></a>

#### test`_`echo

```python
def test_echo() -> None
```

Test the 'echo' handler method.

<a id="packages.valory.skills.abstract_abci.tests.test_handlers.TestABCIHandler.test_set_option"></a>

#### test`_`set`_`option

```python
def test_set_option() -> None
```

Test the 'set_option' handler method.

<a id="packages.valory.skills.abstract_abci.tests.test_handlers.TestABCIHandler.test_begin_block"></a>

#### test`_`begin`_`block

```python
def test_begin_block() -> None
```

Test the 'begin_block' handler method.

<a id="packages.valory.skills.abstract_abci.tests.test_handlers.TestABCIHandler.test_check_tx"></a>

#### test`_`check`_`tx

```python
def test_check_tx(*_: Any) -> None
```

Test the 'check_tx' handler method.

<a id="packages.valory.skills.abstract_abci.tests.test_handlers.TestABCIHandler.test_deliver_tx"></a>

#### test`_`deliver`_`tx

```python
def test_deliver_tx(*_: Any) -> None
```

Test the 'deliver_tx' handler method.

<a id="packages.valory.skills.abstract_abci.tests.test_handlers.TestABCIHandler.test_end_block"></a>

#### test`_`end`_`block

```python
def test_end_block() -> None
```

Test the 'end_block' handler method.

<a id="packages.valory.skills.abstract_abci.tests.test_handlers.TestABCIHandler.test_commit"></a>

#### test`_`commit

```python
def test_commit() -> None
```

Test the 'commit' handler method.

<a id="packages.valory.skills.abstract_abci.tests.test_handlers.TestABCIHandler.test_flush"></a>

#### test`_`flush

```python
def test_flush() -> None
```

Test the 'flush' handler method.

<a id="packages.valory.skills.abstract_abci.tests.test_handlers.TestABCIHandler.test_init_chain"></a>

#### test`_`init`_`chain

```python
def test_init_chain() -> None
```

Test the 'init_chain' handler method.

<a id="packages.valory.skills.abstract_abci.tests.test_handlers.TestABCIHandler.test_query"></a>

#### test`_`query

```python
def test_query() -> None
```

Test the 'init_chain' handler method.

<a id="packages.valory.skills.abstract_abci.tests.test_handlers.TestABCIHandler.test_list_snapshots"></a>

#### test`_`list`_`snapshots

```python
def test_list_snapshots() -> None
```

Test the 'list_snapshots' handler method.

<a id="packages.valory.skills.abstract_abci.tests.test_handlers.TestABCIHandler.test_offer_snapshot"></a>

#### test`_`offer`_`snapshot

```python
def test_offer_snapshot() -> None
```

Test the 'offer_snapshot' handler method.

<a id="packages.valory.skills.abstract_abci.tests.test_handlers.TestABCIHandler.test_load_snapshot_chunk"></a>

#### test`_`load`_`snapshot`_`chunk

```python
def test_load_snapshot_chunk() -> None
```

Test the 'load_snapshot_chunk' handler method.

<a id="packages.valory.skills.abstract_abci.tests.test_handlers.TestABCIHandler.test_apply_snapshot_chunk"></a>

#### test`_`apply`_`snapshot`_`chunk

```python
def test_apply_snapshot_chunk() -> None
```

Test the 'apply_snapshot_chunk' handler method.

