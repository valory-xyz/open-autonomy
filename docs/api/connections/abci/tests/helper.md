<a id="packages.valory.connections.abci.tests.helper"></a>

# packages.valory.connections.abci.tests.helper

Helper functions for checking compliance to ABCI spec

<a id="packages.valory.connections.abci.tests.helper.is_enum"></a>

#### is`_`enum

```python
def is_enum(d_type: Any) -> bool
```

Check if a type is an Enum (not instance!).

<a id="packages.valory.connections.abci.tests.helper.my_repr"></a>

#### my`_`repr

```python
def my_repr(self: Any) -> str
```

Custom __repr__ for Tendermint protobuf objects, which lack it.

<a id="packages.valory.connections.abci.tests.helper.is_typing_list"></a>

#### is`_`typing`_`list

```python
def is_typing_list(d_type: Any) -> bool
```

Check if field is repeated.

<a id="packages.valory.connections.abci.tests.helper.replace_keys"></a>

#### replace`_`keys

```python
def replace_keys(node: Node, trans: Node) -> None
```

Replace keys in-place

<a id="packages.valory.connections.abci.tests.helper.set_repr"></a>

#### set`_`repr

```python
def set_repr(cls: Type) -> Type
```

Set custom __repr__

<a id="packages.valory.connections.abci.tests.helper.get_aea_classes"></a>

#### get`_`aea`_`classes

```python
def get_aea_classes(module: ModuleType) -> Dict[str, Type]
```

Get AEA custom classes.

<a id="packages.valory.connections.abci.tests.helper.get_protocol_readme_spec"></a>

#### get`_`protocol`_`readme`_`spec

```python
@functools.lru_cache()
def get_protocol_readme_spec() -> Tuple[Any, Any, Any]
```

Test specification used to generate protocol matches ABCI spec

<a id="packages.valory.connections.abci.tests.helper.create_aea_abci_type_tree"></a>

#### create`_`aea`_`abci`_`type`_`tree

```python
def create_aea_abci_type_tree(
        speech_acts: Dict[str, Dict[str, str]]) -> Dict[str, Node]
```

Create AEA-native ABCI type tree from the defined speech acts

<a id="packages.valory.connections.abci.tests.helper.init_type_tree_primitives"></a>

#### init`_`type`_`tree`_`primitives

```python
def init_type_tree_primitives(type_tree: Node) -> Node
```

Initialize the primitive types and size of repeated fields.

These are the only initialization parameters that can vary;
after this the initialization of custom types is what remains

This structure allows:
- Comparison of structure and these values with Tendermint translation
- Visual inspection of fields to be sets, also on custom objects
- Randomized testing strategies using e.g. hypothesis

**Arguments**:

- `type_tree`: mapping from message / field name to type.

**Returns**:

mapping from message / field name to initialized primitive.

<a id="packages.valory.connections.abci.tests.helper.init_aea_abci_messages"></a>

#### init`_`aea`_`abci`_`messages

```python
def init_aea_abci_messages(type_tree: Node, init_tree: Node) -> Node
```

Create ABCI messages for AEA-native ABCI spec

We iterate the type_tree and init_tree to finalize the
initialization of custom objects contained in it, and
create an instance of all ABCI messages.

**Arguments**:

- `type_tree`: mapping from message / field name to type.
- `init_tree`: mapping from message / field name to initialized primitive.

**Returns**:

mapping from message name to ABCI Message instance

<a id="packages.valory.connections.abci.tests.helper.EncodingError"></a>

## EncodingError Objects

```python
class EncodingError(Exception)
```

EncodingError AEA- to Tendermint-native ABCI message

<a id="packages.valory.connections.abci.tests.helper.DecodingError"></a>

## DecodingError Objects

```python
class DecodingError(Exception)
```

DecodingError Tendermint- to AEA-native ABCI message

<a id="packages.valory.connections.abci.tests.helper.encode"></a>

#### encode

```python
def encode(message: AbciMessage) -> Response
```

Encode AEA-native ABCI protocol messages to Tendermint-native

<a id="packages.valory.connections.abci.tests.helper.decode"></a>

#### decode

```python
def decode(request: Request) -> AbciMessage
```

Decode Tendermint-native ABCI protocol messages to AEA-native

<a id="packages.valory.connections.abci.tests.helper.get_tendermint_content"></a>

#### get`_`tendermint`_`content

```python
def get_tendermint_content(envelope: Union[Request, Response]) -> Node
```

Get Tendermint-native ABCI message content.

For all Request / Response instances obtained after encoding,
we retrieve the information present in the message they contain.

**Arguments**:

- `envelope`: a Tendermint Request / Response object.

**Returns**:

mapping structure from message / field name to leaf values

<a id="packages.valory.connections.abci.tests.helper.compare_trees"></a>

#### compare`_`trees

```python
def compare_trees(init_node: Node, tender_node: Node) -> None
```

Compare Initialization and Tendermint tree nodes

<a id="packages.valory.connections.abci.tests.helper.get_tender_type_tree"></a>

#### get`_`tender`_`type`_`tree

```python
def get_tender_type_tree() -> Node
```

Tendermint type tree

<a id="packages.valory.connections.abci.tests.helper.init_tendermint_messages"></a>

#### init`_`tendermint`_`messages

```python
def init_tendermint_messages(
        tender_type_tree: Node) -> List[Union[Request, Response]]
```

Initialize tendermint ABCI messages

