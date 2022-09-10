<a id="packages.valory.protocols.abci.tests.test_abci_fuzz"></a>

# packages.valory.protocols.abci.tests.test`_`abci`_`fuzz

Test random initializations of ABCI Message content

<a id="packages.valory.protocols.abci.tests.test_abci_fuzz.create_tender_type_tree"></a>

#### create`_`tender`_`type`_`tree

```python
def create_tender_type_tree(aea_type_tree: Node, tender_type_tree: Node) -> Node
```

Create type tree with Tendermint primitives (as string)

<a id="packages.valory.protocols.abci.tests.test_abci_fuzz.init_type_tree_hypotheses"></a>

#### init`_`type`_`tree`_`hypotheses

```python
def init_type_tree_hypotheses(type_tree: Node) -> Node
```

Initialize the hypothesis strategies

**Arguments**:

- `type_tree`: mapping from message / field name to type.

**Returns**:

mapping from message / field name to initialized primitive.

<a id="packages.valory.protocols.abci.tests.test_abci_fuzz.create_aea_hypotheses"></a>

#### create`_`aea`_`hypotheses

```python
def create_aea_hypotheses() -> Any
```

Create hypotheses for ABCI Messages

<a id="packages.valory.protocols.abci.tests.test_abci_fuzz.init_abci_messages"></a>

#### init`_`abci`_`messages

```python
def init_abci_messages(type_tree: Node, init_tree: Node) -> Node
```

Create ABCI messages for AEA-native ABCI spec

<a id="packages.valory.protocols.abci.tests.test_abci_fuzz.list_to_tuple"></a>

#### list`_`to`_`tuple

```python
def list_to_tuple(node: Node) -> Node
```

Expecting tuples instead of lists

<a id="packages.valory.protocols.abci.tests.test_abci_fuzz.make_aea_test_method"></a>

#### make`_`aea`_`test`_`method

```python
def make_aea_test_method(message_key: str, strategy: Node) -> Callable
```

Dynamically create AEA test

<a id="packages.valory.protocols.abci.tests.test_abci_fuzz.TestAeaHypotheses"></a>

## TestAeaHypotheses Objects

```python
class TestAeaHypotheses()
```

Test AEA hypotheses

<a id="packages.valory.protocols.abci.tests.test_abci_fuzz.create_tendermint_hypotheses"></a>

#### create`_`tendermint`_`hypotheses

```python
def create_tendermint_hypotheses() -> Node
```

Create Tendermint hypotheses

<a id="packages.valory.protocols.abci.tests.test_abci_fuzz.make_tendermint_test_method"></a>

#### make`_`tendermint`_`test`_`method

```python
def make_tendermint_test_method(message_key: str, strategy: Node) -> Callable
```

Dynamically create Tendermint test

<a id="packages.valory.protocols.abci.tests.test_abci_fuzz.TestTendermintHypotheses"></a>

## TestTendermintHypotheses Objects

```python
class TestTendermintHypotheses()
```

Test Tendermint hypotheses

