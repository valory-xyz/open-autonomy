<a id="packages.valory.skills.abstract_round_abci.tests.test_base"></a>

# packages.valory.skills.abstract`_`round`_`abci.tests.test`_`base

Test the base.py module of the skill.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.hypothesis_cleanup"></a>

#### hypothesis`_`cleanup

```python
@pytest.fixture(scope="session", autouse=True)
def hypothesis_cleanup() -> Generator
```

Fixture to remove hypothesis directory after tests.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.PayloadEnum"></a>

## PayloadEnum Objects

```python
class PayloadEnum(Enum)
```

Payload enumeration type.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.PayloadEnum.__str__"></a>

#### `__`str`__`

```python
def __str__() -> str
```

Get the string representation.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.PayloadEnumB"></a>

## PayloadEnumB Objects

```python
class PayloadEnumB(Enum)
```

Payload enumeration type.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.PayloadEnumB.__str__"></a>

#### `__`str`__`

```python
def __str__() -> str
```

Get the string representation.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.BasePayload"></a>

## BasePayload Objects

```python
class BasePayload(BaseTxPayload,  ABC)
```

Base payload class for testing.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.PayloadA"></a>

## PayloadA Objects

```python
class PayloadA(BasePayload)
```

Payload class for payload type 'A'.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.PayloadB"></a>

## PayloadB Objects

```python
class PayloadB(BasePayload)
```

Payload class for payload type 'B'.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.PayloadC"></a>

## PayloadC Objects

```python
class PayloadC(BasePayload)
```

Payload class for payload type 'C'.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.PayloadD"></a>

## PayloadD Objects

```python
class PayloadD(BasePayload)
```

Payload class for payload type 'D'.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.DummyPayload"></a>

## DummyPayload Objects

```python
class DummyPayload(BasePayload)
```

Dummy payload class.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.DummyPayload.__init__"></a>

#### `__`init`__`

```python
def __init__(sender: str, dummy_attribute: int, **kwargs: Any) -> None
```

Initialize a dummy payload.

**Arguments**:

- `sender`: the sender address
- `dummy_attribute`: a dummy attribute
- `kwargs`: the keyword arguments

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.DummyPayload.dummy_attribute"></a>

#### dummy`_`attribute

```python
@property
def dummy_attribute() -> int
```

Get the dummy_attribute.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.DummyPayload.data"></a>

#### data

```python
@property
def data() -> Dict
```

Get the data.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TooBigPayload"></a>

## TooBigPayload Objects

```python
class TooBigPayload(BaseTxPayload,  ABC)
```

Base payload class for testing.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TooBigPayload.data"></a>

#### data

```python
@property
def data() -> Dict
```

Get the data

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.ObjectImitator"></a>

## ObjectImitator Objects

```python
class ObjectImitator()
```

For custom __eq__ implementation testing

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.ObjectImitator.__init__"></a>

#### `__`init`__`

```python
def __init__(other: Any)
```

Copying references to class attr, and instance attr

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.test_base_tx_payload"></a>

#### test`_`base`_`tx`_`payload

```python
def test_base_tx_payload() -> None
```

Test BaseTxPayload.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestTransactions"></a>

## TestTransactions Objects

```python
class TestTransactions()
```

Test Transactions class.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestTransactions.setup"></a>

#### setup

```python
def setup() -> None
```

Set up the test.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestTransactions.test_encode_decode"></a>

#### test`_`encode`_`decode

```python
def test_encode_decode() -> None
```

Test encoding and decoding of payloads.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestTransactions.test_encode_decode_transaction"></a>

#### test`_`encode`_`decode`_`transaction

```python
def test_encode_decode_transaction() -> None
```

Test encode/decode of a transaction.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestTransactions.test_encode_too_big_transaction"></a>

#### test`_`encode`_`too`_`big`_`transaction

```python
def test_encode_too_big_transaction() -> None
```

Test encode of a too big transaction.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestTransactions.test_sign_verify_transaction"></a>

#### test`_`sign`_`verify`_`transaction

```python
def test_sign_verify_transaction() -> None
```

Test sign/verify transaction.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestTransactions.test_payload_not_equal_lookalike"></a>

#### test`_`payload`_`not`_`equal`_`lookalike

```python
def test_payload_not_equal_lookalike() -> None
```

Test payload __eq__ reflection via NotImplemented

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestTransactions.test_transaction_not_equal_lookalike"></a>

#### test`_`transaction`_`not`_`equal`_`lookalike

```python
def test_transaction_not_equal_lookalike() -> None
```

Test transaction __eq__ reflection via NotImplemented

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestTransactions.teardown"></a>

#### teardown

```python
def teardown() -> None
```

Tear down the test.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.test_verify_transaction_negative_case"></a>

#### test`_`verify`_`transaction`_`negative`_`case

```python
@mock.patch(
    "aea.crypto.ledger_apis.LedgerApis.recover_message", return_value={"wrong_sender"}
)
def test_verify_transaction_negative_case(*_mocks: Any) -> None
```

Test verify() of transaction, negative case.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.test_dict_serializer_is_deterministic"></a>

#### test`_`dict`_`serializer`_`is`_`deterministic

```python
@hypothesis.settings(deadline=2000)
@given(
    dictionaries(
        keys=text(),
        values=one_of(floats(allow_nan=False, allow_infinity=False), booleans()),
    )
)
def test_dict_serializer_is_deterministic(obj: Any) -> None
```

Test that 'DictProtobufStructSerializer' is deterministic.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestMetaPayloadUtilityMethods"></a>

## TestMetaPayloadUtilityMethods Objects

```python
class TestMetaPayloadUtilityMethods()
```

Test _MetaPayload private utility methods.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestMetaPayloadUtilityMethods.setup"></a>

#### setup

```python
def setup() -> None
```

Set up the test.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestMetaPayloadUtilityMethods.test_meta_payload_validate_tx_type"></a>

#### test`_`meta`_`payload`_`validate`_`tx`_`type

```python
def test_meta_payload_validate_tx_type() -> None
```

Test _MetaPayload._validate_transaction_type utility method.

First, it registers a class object with a transaction type name into the
_MetaPayload map from transaction type name to classes.
Then, it tries to validate a new insertion with the same transaction type name
but different class object. This will raise an error.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestMetaPayloadUtilityMethods.test_get_field_positive"></a>

#### test`_`get`_`field`_`positive

```python
def test_get_field_positive() -> None
```

Test the utility class method "_get_field", positive case

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestMetaPayloadUtilityMethods.test_get_field_negative"></a>

#### test`_`get`_`field`_`negative

```python
def test_get_field_negative() -> None
```

Test the utility class method "_get_field", negative case

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestMetaPayloadUtilityMethods.teardown"></a>

#### teardown

```python
def teardown() -> None
```

Tear down the test.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.test_initialize_block"></a>

#### test`_`initialize`_`block

```python
def test_initialize_block() -> None
```

Test instantiation of a Block instance.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestBlockchain"></a>

## TestBlockchain Objects

```python
class TestBlockchain()
```

Test a blockchain object.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestBlockchain.setup"></a>

#### setup

```python
def setup() -> None
```

Set up the test.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestBlockchain.test_height"></a>

#### test`_`height

```python
def test_height() -> None
```

Test the 'height' property getter.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestBlockchain.test_len"></a>

#### test`_`len

```python
def test_len() -> None
```

Test the 'length' property getter.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestBlockchain.test_add_block_positive"></a>

#### test`_`add`_`block`_`positive

```python
def test_add_block_positive() -> None
```

Test 'add_block', success.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestBlockchain.test_add_block_negative_wrong_height"></a>

#### test`_`add`_`block`_`negative`_`wrong`_`height

```python
def test_add_block_negative_wrong_height() -> None
```

Test 'add_block', wrong height.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestBlockchain.test_blocks"></a>

#### test`_`blocks

```python
def test_blocks() -> None
```

Test 'blocks' property getter.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestBlockBuilder"></a>

## TestBlockBuilder Objects

```python
class TestBlockBuilder()
```

Test block builder.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestBlockBuilder.setup"></a>

#### setup

```python
def setup() -> None
```

Set up the method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestBlockBuilder.test_get_header_positive"></a>

#### test`_`get`_`header`_`positive

```python
def test_get_header_positive() -> None
```

Test header property getter, positive.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestBlockBuilder.test_get_header_negative"></a>

#### test`_`get`_`header`_`negative

```python
def test_get_header_negative() -> None
```

Test header property getter, negative.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestBlockBuilder.test_set_header_positive"></a>

#### test`_`set`_`header`_`positive

```python
def test_set_header_positive() -> None
```

Test header property setter, positive.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestBlockBuilder.test_set_header_negative"></a>

#### test`_`set`_`header`_`negative

```python
def test_set_header_negative() -> None
```

Test header property getter, negative.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestBlockBuilder.test_transitions_getter"></a>

#### test`_`transitions`_`getter

```python
def test_transitions_getter() -> None
```

Test 'transitions' property getter.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestBlockBuilder.test_add_transitions"></a>

#### test`_`add`_`transitions

```python
def test_add_transitions() -> None
```

Test 'add_transition'.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestBlockBuilder.test_get_block_negative_header_not_set_yet"></a>

#### test`_`get`_`block`_`negative`_`header`_`not`_`set`_`yet

```python
def test_get_block_negative_header_not_set_yet() -> None
```

Test 'get_block', negative case (header not set yet).

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestBlockBuilder.test_get_block_positive"></a>

#### test`_`get`_`block`_`positive

```python
def test_get_block_positive() -> None
```

Test 'get_block', positive case.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestConsensusParams"></a>

## TestConsensusParams Objects

```python
class TestConsensusParams()
```

Test the 'ConsensusParams' class.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestConsensusParams.setup"></a>

#### setup

```python
def setup() -> None
```

Set up the tests.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestConsensusParams.test_max_participants_getter"></a>

#### test`_`max`_`participants`_`getter

```python
def test_max_participants_getter() -> None
```

Test 'max_participants' property getter.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestConsensusParams.test_threshold_getter"></a>

#### test`_`threshold`_`getter

```python
@pytest.mark.parametrize(
        "nb_participants,expected",
        [
            (1, 1),
            (2, 2),
            (3, 3),
            (4, 3),
            (5, 4),
            (6, 5),
            (7, 5),
            (8, 6),
            (9, 7),
            (10, 7),
        ],
    )
def test_threshold_getter(nb_participants: int, expected: int) -> None
```

Test threshold property getter.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestConsensusParams.test_consensus_params_not_equal_lookalike"></a>

#### test`_`consensus`_`params`_`not`_`equal`_`lookalike

```python
def test_consensus_params_not_equal_lookalike() -> None
```

Test consensus param __eq__ reflection via NotImplemented

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestConsensusParams.test_from_json"></a>

#### test`_`from`_`json

```python
def test_from_json() -> None
```

Test 'from_json' method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciAppDB"></a>

## TestAbciAppDB Objects

```python
class TestAbciAppDB()
```

Test 'AbciAppDB' class.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciAppDB.setup"></a>

#### setup

```python
def setup() -> None
```

Set up the tests.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciAppDB.test_init"></a>

#### test`_`init

```python
@pytest.mark.parametrize(
        "data, setup_data",
        (
            ({"participants": ["a", "b"]}, {"participants": ["a", "b"]}),
            ({"participants": []}, {}),
            ({"participants": None}, None),
            ("participants", None),
            (1, None),
            (object(), None),
            (["participants"], None),
            ({"participants": [], "other": [1, 2]}, {"other": [1, 2]}),
        ),
    )
def test_init(data: Dict, setup_data: Optional[Dict]) -> None
```

Test constructor.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciAppDB.test_try_alter_init_data"></a>

#### test`_`try`_`alter`_`init`_`data

```python
def test_try_alter_init_data() -> None
```

Test trying to alter the init data.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciAppDB.test_get"></a>

#### test`_`get

```python
def test_get() -> None
```

Test getters.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciAppDB.test_increment_round_count"></a>

#### test`_`increment`_`round`_`count

```python
def test_increment_round_count() -> None
```

Test increment_round_count.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciAppDB.test_update"></a>

#### test`_`update

```python
@pytest.mark.parametrize(
        "setup_data, update_data, expected_data",
        (
            (dict(), {"dummy_key": "dummy_value"}, {0: {"dummy_key": ["dummy_value"]}}),
            (
                dict(),
                {"dummy_key": ["dummy_value1", "dummy_value2"]},
                {0: {"dummy_key": [["dummy_value1", "dummy_value2"]]}},
            ),
            (
                {"test": ["test"]},
                {"dummy_key": "dummy_value"},
                {0: {"dummy_key": ["dummy_value"], "test": ["test"]}},
            ),
            (
                {"test": ["test"]},
                {"test": "dummy_value"},
                {0: {"test": ["test", "dummy_value"]}},
            ),
            (
                {"test": [["test"]]},
                {"test": ["dummy_value1", "dummy_value2"]},
                {0: {"test": [["test"], ["dummy_value1", "dummy_value2"]]}},
            ),
            (
                {"test": ["test"]},
                {"test": ["dummy_value1", "dummy_value2"]},
                {0: {"test": ["test", ["dummy_value1", "dummy_value2"]]}},
            ),
        ),
    )
def test_update(setup_data: Dict, update_data: Dict, expected_data: Dict[int, Dict]) -> None
```

Test update db.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciAppDB.test_cleanup"></a>

#### test`_`cleanup

```python
@pytest.mark.parametrize(
        "existing_data, cleanup_history_depth, cleanup_history_depth_current, expected",
        (
            (
                {1: {"test": ["test", ["dummy_value1", "dummy_value2"]]}},
                0,
                None,
                {1: {"test": ["test", ["dummy_value1", "dummy_value2"]]}},
            ),
            (
                {
                    1: {"test": ["test", ["dummy_value1", "dummy_value2"]]},
                    2: {"test": [0]},
                },
                0,
                None,
                {2: {"test": [0]}},
            ),
            (
                {
                    1: {"test": ["test", ["dummy_value1", "dummy_value2"]]},
                    2: {"test": [0, 1, 2]},
                },
                0,
                0,
                {2: {"test": [0, 1, 2]}},
            ),
            (
                {
                    1: {"test": ["test", ["dummy_value1", "dummy_value2"]]},
                    2: {"test": [0, 1, 2]},
                },
                0,
                1,
                {2: {"test": [2]}},
            ),
            (
                {
                    1: {"test": ["test", ["dummy_value1", "dummy_value2"]]},
                    2: {"test": [i for i in range(5)]},
                    3: {"test": [i for i in range(5, 10)]},
                    4: {"test": [i for i in range(10, 15)]},
                    5: {"test": [i for i in range(15, 20)]},
                },
                3,
                0,
                {
                    3: {"test": [i for i in range(5, 10)]},
                    4: {"test": [i for i in range(10, 15)]},
                    5: {"test": [i for i in range(15, 20)]},
                },
            ),
            (
                {
                    1: {"test": ["test", ["dummy_value1", "dummy_value2"]]},
                    2: {"test": [i for i in range(5)]},
                    3: {"test": [i for i in range(5, 10)]},
                    4: {"test": [i for i in range(10, 15)]},
                    5: {"test": [i for i in range(15, 20)]},
                },
                5,
                3,
                {
                    1: {"test": ["test", ["dummy_value1", "dummy_value2"]]},
                    2: {"test": [i for i in range(5)]},
                    3: {"test": [i for i in range(5, 10)]},
                    4: {"test": [i for i in range(10, 15)]},
                    5: {"test": [i for i in range(15 + 2, 20)]},
                },
            ),
            (
                {
                    1: {"test": ["test", ["dummy_value1", "dummy_value2"]]},
                    2: {"test": [i for i in range(5)]},
                    3: {"test": [i for i in range(5, 10)]},
                    4: {"test": [i for i in range(10, 15)]},
                    5: {"test": [i for i in range(15, 20)]},
                },
                2,
                3,
                {
                    4: {"test": [i for i in range(10, 15)]},
                    5: {"test": [i for i in range(15 + 2, 20)]},
                },
            ),
            (
                {
                    1: {"test": ["test", ["dummy_value1", "dummy_value2"]]},
                    2: {"test": [i for i in range(5)]},
                    3: {"test": [i for i in range(5, 10)]},
                    4: {"test": [i for i in range(10, 15)]},
                    5: {"test": [i for i in range(15, 20)]},
                },
                0,
                1,
                {
                    5: {"test": [19]},
                },
            ),
        ),
    )
def test_cleanup(existing_data: Dict[int, Dict[str, List[Any]]], cleanup_history_depth: int, cleanup_history_depth_current: Optional[int], expected: Dict[int, Dict[str, List[Any]]]) -> None
```

Test cleanup db.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestBaseSynchronizedData"></a>

## TestBaseSynchronizedData Objects

```python
class TestBaseSynchronizedData()
```

Test 'BaseSynchronizedData' class.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestBaseSynchronizedData.setup"></a>

#### setup

```python
def setup() -> None
```

Set up the tests.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestBaseSynchronizedData.test_participants_getter_positive"></a>

#### test`_`participants`_`getter`_`positive

```python
def test_participants_getter_positive() -> None
```

Test 'participants' property getter.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestBaseSynchronizedData.test_nb_participants_getter"></a>

#### test`_`nb`_`participants`_`getter

```python
def test_nb_participants_getter() -> None
```

Test 'participants' property getter.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestBaseSynchronizedData.test_participants_getter_negative"></a>

#### test`_`participants`_`getter`_`negative

```python
def test_participants_getter_negative() -> None
```

Test 'participants' property getter, negative case.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestBaseSynchronizedData.test_update"></a>

#### test`_`update

```python
def test_update() -> None
```

Test the 'update' method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestBaseSynchronizedData.test_create"></a>

#### test`_`create

```python
def test_create() -> None
```

Test the 'create' method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestBaseSynchronizedData.test_repr"></a>

#### test`_`repr

```python
def test_repr() -> None
```

Test the '__repr__' magic method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestBaseSynchronizedData.test_participants_list_is_empty"></a>

#### test`_`participants`_`list`_`is`_`empty

```python
def test_participants_list_is_empty() -> None
```

Tets when participants list is set to zero.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestBaseSynchronizedData.test_all_participants_list_is_empty"></a>

#### test`_`all`_`participants`_`list`_`is`_`empty

```python
def test_all_participants_list_is_empty() -> None
```

Tets when participants list is set to zero.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestBaseSynchronizedData.test_properties"></a>

#### test`_`properties

```python
def test_properties() -> None
```

Test several properties

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbstractRound"></a>

## TestAbstractRound Objects

```python
class TestAbstractRound()
```

Test the 'AbstractRound' class.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbstractRound.setup"></a>

#### setup

```python
def setup() -> None
```

Set up the tests.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbstractRound.test_must_set_round_id"></a>

#### test`_`must`_`set`_`round`_`id

```python
def test_must_set_round_id() -> None
```

Test that the 'round_id' must be set in concrete classes.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbstractRound.test_must_set_allowed_tx_type"></a>

#### test`_`must`_`set`_`allowed`_`tx`_`type

```python
def test_must_set_allowed_tx_type() -> None
```

Test that the 'allowed_tx_type' must be set in concrete classes.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbstractRound.test_check_allowed_tx_type_with_previous_round_transaction"></a>

#### test`_`check`_`allowed`_`tx`_`type`_`with`_`previous`_`round`_`transaction

```python
def test_check_allowed_tx_type_with_previous_round_transaction() -> None
```

Test check 'allowed_tx_type'.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbstractRound.test_check_allowed_tx_type"></a>

#### test`_`check`_`allowed`_`tx`_`type

```python
def test_check_allowed_tx_type() -> None
```

Test check 'allowed_tx_type'.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbstractRound.test_synchronized_data_getter"></a>

#### test`_`synchronized`_`data`_`getter

```python
def test_synchronized_data_getter() -> None
```

Test 'synchronized_data' property getter.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbstractRound.test_check_transaction_unknown_payload"></a>

#### test`_`check`_`transaction`_`unknown`_`payload

```python
def test_check_transaction_unknown_payload() -> None
```

Test 'check_transaction' method, with unknown payload type.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbstractRound.test_check_transaction_known_payload"></a>

#### test`_`check`_`transaction`_`known`_`payload

```python
def test_check_transaction_known_payload() -> None
```

Test 'check_transaction' method, with known payload type.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbstractRound.test_process_transaction_negative_unknown_payload"></a>

#### test`_`process`_`transaction`_`negative`_`unknown`_`payload

```python
def test_process_transaction_negative_unknown_payload() -> None
```

Test 'process_transaction' method, with unknown payload type.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbstractRound.test_process_transaction_negative_check_transaction_fails"></a>

#### test`_`process`_`transaction`_`negative`_`check`_`transaction`_`fails

```python
def test_process_transaction_negative_check_transaction_fails() -> None
```

Test 'process_transaction' method, with 'check_transaction' failing.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbstractRound.test_process_transaction_positive"></a>

#### test`_`process`_`transaction`_`positive

```python
def test_process_transaction_positive() -> None
```

Test 'process_transaction' method, positive case.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbstractRound.test_check_majority_possible_raises_error_when_nb_participants_is_0"></a>

#### test`_`check`_`majority`_`possible`_`raises`_`error`_`when`_`nb`_`participants`_`is`_`0

```python
def test_check_majority_possible_raises_error_when_nb_participants_is_0() -> None
```

Check that 'check_majority_possible' raises error when nb_participants=0.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbstractRound.test_check_majority_possible_passes_when_vote_set_is_empty"></a>

#### test`_`check`_`majority`_`possible`_`passes`_`when`_`vote`_`set`_`is`_`empty

```python
def test_check_majority_possible_passes_when_vote_set_is_empty() -> None
```

Check that 'check_majority_possible' passes when the set of votes is empty.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbstractRound.test_check_majority_possible_passes_when_vote_set_nonempty_and_check_passes"></a>

#### test`_`check`_`majority`_`possible`_`passes`_`when`_`vote`_`set`_`nonempty`_`and`_`check`_`passes

```python
def test_check_majority_possible_passes_when_vote_set_nonempty_and_check_passes() -> None
```

Check that 'check_majority_possible' passes when set of votes is non-empty.

The check passes because:
- the threshold is 2
- the other voter can vote for the same item of the first voter

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbstractRound.test_check_majority_possible_passes_when_payload_attributes_majority_match"></a>

#### test`_`check`_`majority`_`possible`_`passes`_`when`_`payload`_`attributes`_`majority`_`match

```python
def test_check_majority_possible_passes_when_payload_attributes_majority_match() -> None
```

Test 'check_majority_possible' when set of votes is non-empty and the majority of the attribute values match.

The check passes because:
- the threshold is 3 (participants are 4)
- 3 voters have the same attribute value in their payload

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbstractRound.test_check_majority_possible_passes_when_vote_set_nonempty_and_check_doesnt_pass"></a>

#### test`_`check`_`majority`_`possible`_`passes`_`when`_`vote`_`set`_`nonempty`_`and`_`check`_`doesnt`_`pass

```python
def test_check_majority_possible_passes_when_vote_set_nonempty_and_check_doesnt_pass() -> None
```

Check that 'check_majority_possible' doesn't pass when set of votes is non-empty.

the check does not pass because:
- the threshold is 2
- both voters have already voted for different items

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbstractRound.test_is_majority_possible_positive_case"></a>

#### test`_`is`_`majority`_`possible`_`positive`_`case

```python
def test_is_majority_possible_positive_case() -> None
```

Test 'is_majority_possible', positive case.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbstractRound.test_is_majority_possible_negative_case"></a>

#### test`_`is`_`majority`_`possible`_`negative`_`case

```python
def test_is_majority_possible_negative_case() -> None
```

Test 'is_majority_possible', negative case.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbstractRound.test_check_majority_possible_raises_error_when_new_voter_already_voted"></a>

#### test`_`check`_`majority`_`possible`_`raises`_`error`_`when`_`new`_`voter`_`already`_`voted

```python
def test_check_majority_possible_raises_error_when_new_voter_already_voted() -> None
```

Test 'check_majority_possible_with_new_vote' raises when new voter already voted.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbstractRound.test_check_majority_possible_raises_error_when_nb_participants_inconsistent"></a>

#### test`_`check`_`majority`_`possible`_`raises`_`error`_`when`_`nb`_`participants`_`inconsistent

```python
def test_check_majority_possible_raises_error_when_nb_participants_inconsistent() -> None
```

Test 'check_majority_possible_with_new_vote' raises when 'nb_participants' inconsistent with other args.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbstractRound.test_check_majority_possible_when_check_passes"></a>

#### test`_`check`_`majority`_`possible`_`when`_`check`_`passes

```python
def test_check_majority_possible_when_check_passes() -> None
```

Test 'check_majority_possible_with_new_vote' when the check passes.

The test passes because:
- the number of participants is 2, and so the threshold is 2
- the new voter votes for the same item already voted by voter 1.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestTimeouts"></a>

## TestTimeouts Objects

```python
class TestTimeouts()
```

Test the 'Timeouts' class.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestTimeouts.setup"></a>

#### setup

```python
def setup() -> None
```

Set up the test.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestTimeouts.test_size"></a>

#### test`_`size

```python
def test_size() -> None
```

Test the 'size' property.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestTimeouts.test_add_timeout"></a>

#### test`_`add`_`timeout

```python
def test_add_timeout() -> None
```

Test the 'add_timeout' method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestTimeouts.test_cancel_timeout"></a>

#### test`_`cancel`_`timeout

```python
def test_cancel_timeout() -> None
```

Test the 'cancel_timeout' method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestTimeouts.test_pop_earliest_cancelled_timeouts"></a>

#### test`_`pop`_`earliest`_`cancelled`_`timeouts

```python
def test_pop_earliest_cancelled_timeouts() -> None
```

Test the 'pop_earliest_cancelled_timeouts' method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestTimeouts.test_get_earliest_timeout_a"></a>

#### test`_`get`_`earliest`_`timeout`_`a

```python
def test_get_earliest_timeout_a() -> None
```

Test the 'get_earliest_timeout' method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestTimeouts.test_get_earliest_timeout_b"></a>

#### test`_`get`_`earliest`_`timeout`_`b

```python
def test_get_earliest_timeout_b() -> None
```

Test the 'get_earliest_timeout' method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestTimeouts.test_pop_timeout"></a>

#### test`_`pop`_`timeout

```python
def test_pop_timeout() -> None
```

Test the 'pop_timeout' method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciApp"></a>

## TestAbciApp Objects

```python
class TestAbciApp()
```

Test the 'AbciApp' class.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciApp.setup"></a>

#### setup

```python
def setup() -> None
```

Set up the test.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciApp.test_is_abstract"></a>

#### test`_`is`_`abstract

```python
@pytest.mark.parametrize("flag", (True, False))
def test_is_abstract(flag: bool) -> None
```

Test `is_abstract` property.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciApp.test_reset_index"></a>

#### test`_`reset`_`index

```python
@given(integers())
def test_reset_index(reset_index: int) -> None
```

Test `reset_index` getter and setter.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciApp.test_initial_round_cls_not_set"></a>

#### test`_`initial`_`round`_`cls`_`not`_`set

```python
def test_initial_round_cls_not_set() -> None
```

Test when 'initial_round_cls' is not set.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciApp.test_transition_function_not_set"></a>

#### test`_`transition`_`function`_`not`_`set

```python
def test_transition_function_not_set() -> None
```

Test when 'transition_function' is not set.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciApp.test_last_timestamp_negative"></a>

#### test`_`last`_`timestamp`_`negative

```python
def test_last_timestamp_negative() -> None
```

Test the 'last_timestamp' property, negative case.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciApp.test_last_timestamp_positive"></a>

#### test`_`last`_`timestamp`_`positive

```python
def test_last_timestamp_positive() -> None
```

Test the 'last_timestamp' property, positive case.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciApp.test_process_event"></a>

#### test`_`process`_`event

```python
def test_process_event() -> None
```

Test the 'process_event' method, positive case, with timeout events.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciApp.test_process_event_negative_case"></a>

#### test`_`process`_`event`_`negative`_`case

```python
def test_process_event_negative_case() -> None
```

Test the 'process_event' method, negative case.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciApp.test_update_time"></a>

#### test`_`update`_`time

```python
def test_update_time() -> None
```

Test the 'update_time' method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciApp.test_get_all_events"></a>

#### test`_`get`_`all`_`events

```python
def test_get_all_events() -> None
```

Test the all events getter.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciApp.test_cleanup"></a>

#### test`_`cleanup

```python
def test_cleanup() -> None
```

Test the cleanup method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence"></a>

## TestRoundSequence Objects

```python
class TestRoundSequence()
```

Test the RoundSequence class.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.setup"></a>

#### setup

```python
def setup() -> None
```

Set up the test.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_height"></a>

#### test`_`height

```python
@pytest.mark.parametrize("offset", tuple(range(5)))
@pytest.mark.parametrize("n_blocks", (0, 1, 10))
def test_height(n_blocks: int, offset: int) -> None
```

Test 'height' property.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_is_finished"></a>

#### test`_`is`_`finished

```python
def test_is_finished() -> None
```

Test 'is_finished' property.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_last_round"></a>

#### test`_`last`_`round

```python
def test_last_round() -> None
```

Test 'last_round' property.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_last_timestamp_none"></a>

#### test`_`last`_`timestamp`_`none

```python
def test_last_timestamp_none() -> None
```

Test 'last_timestamp' property.

The property is None because there are no blocks.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_last_timestamp"></a>

#### test`_`last`_`timestamp

```python
def test_last_timestamp() -> None
```

Test 'last_timestamp' property, positive case.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_abci_app_negative"></a>

#### test`_`abci`_`app`_`negative

```python
def test_abci_app_negative() -> None
```

Test 'abci_app' property, negative case.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_check_is_finished_negative"></a>

#### test`_`check`_`is`_`finished`_`negative

```python
def test_check_is_finished_negative() -> None
```

Test 'check_is_finished', negative case.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_current_round_positive"></a>

#### test`_`current`_`round`_`positive

```python
def test_current_round_positive() -> None
```

Test 'current_round' property getter, positive case.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_current_round_negative_current_round_not_set"></a>

#### test`_`current`_`round`_`negative`_`current`_`round`_`not`_`set

```python
def test_current_round_negative_current_round_not_set() -> None
```

Test 'current_round' property getter, negative case (current round not set).

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_current_round_id"></a>

#### test`_`current`_`round`_`id

```python
def test_current_round_id() -> None
```

Test 'current_round_id' property getter

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_latest_result"></a>

#### test`_`latest`_`result

```python
def test_latest_result() -> None
```

Test 'latest_result' property getter.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_last_round_transition_timestamp"></a>

#### test`_`last`_`round`_`transition`_`timestamp

```python
@pytest.mark.parametrize("committed", (True, False))
def test_last_round_transition_timestamp(committed: bool) -> None
```

Test 'last_round_transition_timestamp' method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_last_round_transition_height"></a>

#### test`_`last`_`round`_`transition`_`height

```python
@pytest.mark.parametrize("committed", (True, False))
def test_last_round_transition_height(committed: bool) -> None
```

Test 'last_round_transition_height' method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_last_round_transition_root_hash"></a>

#### test`_`last`_`round`_`transition`_`root`_`hash

```python
@pytest.mark.parametrize("last_round_transition_root_hash", (b"", b"test"))
@pytest.mark.parametrize("round_count, reset_index", ((0, 0), (4, 2), (8, 1)))
def test_last_round_transition_root_hash(last_round_transition_root_hash: bytes, round_count: int, reset_index: int) -> None
```

Test 'last_round_transition_root_hash' method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_last_round_transition_tm_height"></a>

#### test`_`last`_`round`_`transition`_`tm`_`height

```python
@pytest.mark.parametrize("tm_height", (None, 1, 5))
def test_last_round_transition_tm_height(tm_height: Optional[int]) -> None
```

Test 'last_round_transition_tm_height' method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_tm_height"></a>

#### test`_`tm`_`height

```python
@given(one_of(none(), integers()))
def test_tm_height(tm_height: int) -> None
```

Test `tm_height` getter and setter.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_block_stall_deadline_expired"></a>

#### test`_`block`_`stall`_`deadline`_`expired

```python
@given(one_of(none(), datetimes()))
def test_block_stall_deadline_expired(block_stall_deadline: datetime.datetime) -> None
```

Test 'block_stall_deadline_expired' method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_init_chain"></a>

#### test`_`init`_`chain

```python
@pytest.mark.parametrize("begin_height", tuple(range(0, 50, 10)))
@pytest.mark.parametrize("initial_height", tuple(range(0, 11, 5)))
def test_init_chain(begin_height: int, initial_height: int) -> None
```

Test 'init_chain' method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_begin_block_negative_is_finished"></a>

#### test`_`begin`_`block`_`negative`_`is`_`finished

```python
def test_begin_block_negative_is_finished() -> None
```

Test 'begin_block' method, negative case (round sequence is finished).

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_begin_block_negative_wrong_phase"></a>

#### test`_`begin`_`block`_`negative`_`wrong`_`phase

```python
def test_begin_block_negative_wrong_phase() -> None
```

Test 'begin_block' method, negative case (wrong phase).

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_begin_block_positive"></a>

#### test`_`begin`_`block`_`positive

```python
def test_begin_block_positive() -> None
```

Test 'begin_block' method, positive case.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_deliver_tx_negative_wrong_phase"></a>

#### test`_`deliver`_`tx`_`negative`_`wrong`_`phase

```python
def test_deliver_tx_negative_wrong_phase() -> None
```

Test 'begin_block' method, negative (wrong phase).

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_deliver_tx_positive_not_valid"></a>

#### test`_`deliver`_`tx`_`positive`_`not`_`valid

```python
def test_deliver_tx_positive_not_valid() -> None
```

Test 'begin_block' method, positive (not valid).

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_end_block_negative_wrong_phase"></a>

#### test`_`end`_`block`_`negative`_`wrong`_`phase

```python
def test_end_block_negative_wrong_phase() -> None
```

Test 'end_block' method, negative case (wrong phase).

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_end_block_positive"></a>

#### test`_`end`_`block`_`positive

```python
def test_end_block_positive() -> None
```

Test 'end_block' method, positive case.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_commit_negative_wrong_phase"></a>

#### test`_`commit`_`negative`_`wrong`_`phase

```python
def test_commit_negative_wrong_phase() -> None
```

Test 'end_block' method, negative case (wrong phase).

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_commit_negative_exception"></a>

#### test`_`commit`_`negative`_`exception

```python
def test_commit_negative_exception() -> None
```

Test 'end_block' method, negative case (raise exception).

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_commit_positive_no_change_round"></a>

#### test`_`commit`_`positive`_`no`_`change`_`round

```python
def test_commit_positive_no_change_round() -> None
```

Test 'end_block' method, positive (no change round).

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_commit_positive_with_change_round"></a>

#### test`_`commit`_`positive`_`with`_`change`_`round

```python
def test_commit_positive_with_change_round() -> None
```

Test 'end_block' method, positive (with change round).

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_reset_blockchain"></a>

#### test`_`reset`_`blockchain

```python
@pytest.mark.parametrize("is_replay", (True, False))
def test_reset_blockchain(is_replay: bool) -> None
```

Test `reset_blockchain` method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_update_round"></a>

#### test`_`update`_`round

```python
@mock.patch.object(AbciApp, "process_event")
@pytest.mark.parametrize("end_block_res", (None, (MagicMock(), MagicMock())))
def test_update_round(process_event_mock: mock.Mock, end_block_res: Optional[Tuple[BaseSynchronizedData, Any]]) -> None
```

Test '_update_round' method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.test_meta_abci_app_when_instance_not_subclass_of_abstract_round"></a>

#### test`_`meta`_`abci`_`app`_`when`_`instance`_`not`_`subclass`_`of`_`abstract`_`round

```python
def test_meta_abci_app_when_instance_not_subclass_of_abstract_round() -> None
```

Test instantiation of meta-class when instance not a subclass of AbciApp.

Since the class is not a subclass of AbciApp, the checks performed by
the meta-class should not apply.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.test_meta_abci_app_when_final_round_not_subclass_of_degenerate_round"></a>

#### test`_`meta`_`abci`_`app`_`when`_`final`_`round`_`not`_`subclass`_`of`_`degenerate`_`round

```python
def test_meta_abci_app_when_final_round_not_subclass_of_degenerate_round() -> None
```

Test instantiation of meta-class when a final round is not a subclass of DegenerateRound.

