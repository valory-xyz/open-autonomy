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

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.BasePayload"></a>

## BasePayload Objects

```python
class BasePayload(BaseTxPayload, ABC)
```

Base payload class for testing.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.PayloadA"></a>

## PayloadA Objects

```python
@dataclass(frozen=True)
class PayloadA(BasePayload)
```

Payload class for payload type 'A'.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.PayloadB"></a>

## PayloadB Objects

```python
@dataclass(frozen=True)
class PayloadB(BasePayload)
```

Payload class for payload type 'B'.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.PayloadC"></a>

## PayloadC Objects

```python
@dataclass(frozen=True)
class PayloadC(BasePayload)
```

Payload class for payload type 'C'.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.PayloadD"></a>

## PayloadD Objects

```python
@dataclass(frozen=True)
class PayloadD(BasePayload)
```

Payload class for payload type 'D'.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.DummyPayload"></a>

## DummyPayload Objects

```python
@dataclass(frozen=True)
class DummyPayload(BasePayload)
```

Dummy payload class.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TooBigPayload"></a>

## TooBigPayload Objects

```python
@dataclass(frozen=True)
class TooBigPayload(BaseTxPayload)
```

Base payload class for testing.

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

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.test_meta_round_abstract_round_when_instance_not_subclass_of_abstract_round"></a>

#### test`_`meta`_`round`_`abstract`_`round`_`when`_`instance`_`not`_`subclass`_`of`_`abstract`_`round

```python
def test_meta_round_abstract_round_when_instance_not_subclass_of_abstract_round(
) -> (None)
```

Test instantiation of meta class when instance not a subclass of abstract round.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.test_abstract_round_instantiation_without_attributes_raises_error"></a>

#### test`_`abstract`_`round`_`instantiation`_`without`_`attributes`_`raises`_`error

```python
def test_abstract_round_instantiation_without_attributes_raises_error(
) -> None
```

Test that definition of concrete subclass of AbstractRound without attributes raises error.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.test_specific_round_instantiation_without_extended_requirements_raises_error"></a>

#### test`_`specific`_`round`_`instantiation`_`without`_`extended`_`requirements`_`raises`_`error

```python
def test_specific_round_instantiation_without_extended_requirements_raises_error(
) -> (None)
```

Test that definition of concrete subclass of CollectSameUntilThresholdRound without extended raises error.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestTransactions"></a>

## TestTransactions Objects

```python
class TestTransactions()
```

Test Transactions class.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestTransactions.setup_method"></a>

#### setup`_`method

```python
def setup_method() -> None
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

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestTransactions.test_encode_too_big_payload"></a>

#### test`_`encode`_`too`_`big`_`payload

```python
def test_encode_too_big_payload() -> None
```

Test encode of a too big payload.

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

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestTransactions.teardown_method"></a>

#### teardown`_`method

```python
def teardown_method() -> None
```

Tear down the test.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.test_verify_transaction_negative_case"></a>

#### test`_`verify`_`transaction`_`negative`_`case

```python
@mock.patch("aea.crypto.ledger_apis.LedgerApis.recover_message",
            return_value={"wrong_sender"})
def test_verify_transaction_negative_case(*_mocks: Any) -> None
```

Test verify() of transaction, negative case.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.SomeClass"></a>

## SomeClass Objects

```python
@dataclass(frozen=True)
class SomeClass(BaseTxPayload)
```

Test class.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.test_payload_serializer_is_deterministic"></a>

#### test`_`payload`_`serializer`_`is`_`deterministic

```python
@given(
    dictionaries(
        keys=text(),
        values=one_of(floats(allow_nan=False, allow_infinity=False),
                      booleans()),
    ))
def test_payload_serializer_is_deterministic(obj: Any) -> None
```

Test that 'DictProtobufStructSerializer' is deterministic.

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

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestBlockchain.setup_method"></a>

#### setup`_`method

```python
def setup_method() -> None
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

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestBlockchain.test_add_block_before_initial_height"></a>

#### test`_`add`_`block`_`before`_`initial`_`height

```python
def test_add_block_before_initial_height() -> None
```

Test 'add_block', too old height.

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

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestBlockBuilder.setup_method"></a>

#### setup`_`method

```python
def setup_method() -> None
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

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciAppDB"></a>

## TestAbciAppDB Objects

```python
class TestAbciAppDB()
```

Test 'AbciAppDB' class.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciAppDB.setup_method"></a>

#### setup`_`method

```python
def setup_method() -> None
```

Set up the tests.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciAppDB.test_init"></a>

#### test`_`init

```python
@pytest.mark.parametrize(
    "data, setup_data",
    (
        ({
            "participants": ["a", "b"]
        }, {
            "participants": ["a", "b"]
        }),
        ({
            "participants": []
        }, {}),
        ({
            "participants": None
        }, None),
        ("participants", None),
        (1, None),
        (object(), None),
        (["participants"], None),
        ({
            "participants": [],
            "other": [1, 2]
        }, {
            "other": [1, 2]
        }),
    ),
)
@pytest.mark.parametrize(
    "cross_period_persisted_keys, expected_cross_period_persisted_keys",
    ((None, set()), (set(), set()), ({"test"}, {"test"})),
)
def test_init(data: Dict, setup_data: Optional[Dict],
              cross_period_persisted_keys: Optional[Set[str]],
              expected_cross_period_persisted_keys: Set[str]) -> None
```

Test constructor.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciAppDB.EnumTest"></a>

## EnumTest Objects

```python
class EnumTest(Enum)
```

A test Enum class

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciAppDB.test_normalize"></a>

#### test`_`normalize

```python
@pytest.mark.parametrize(
    "data_in, expected_output",
    (
        (0, 0),
        ([], []),
        ({
            "test": 2
        }, {
            "test": 2
        }),
        (EnumTest.test, 10),
        (b"test", b"test".hex()),
        ({3, 4}, "[3, 4]"),
        (object(), None),
    ),
)
def test_normalize(data_in: Any, expected_output: Any) -> None
```

Test `normalize`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciAppDB.test_reset_index"></a>

#### test`_`reset`_`index

```python
@pytest.mark.parametrize("data", {0: [{"test": 2}]})
def test_reset_index(data: Dict) -> None
```

Test `reset_index`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciAppDB.test_round_count_setter"></a>

#### test`_`round`_`count`_`setter

```python
def test_round_count_setter() -> None
```

Tests the round count setter.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciAppDB.test_try_alter_init_data"></a>

#### test`_`try`_`alter`_`init`_`data

```python
def test_try_alter_init_data() -> None
```

Test trying to alter the init data.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciAppDB.test_cross_period_persisted_keys"></a>

#### test`_`cross`_`period`_`persisted`_`keys

```python
def test_cross_period_persisted_keys() -> None
```

Test `cross_period_persisted_keys` property

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

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciAppDB.test_validate"></a>

#### test`_`validate

```python
@mock.patch.object(
    abci_base,
    "is_json_serializable",
    return_value=False,
)
def test_validate(_: mock._patch) -> None
```

Test `validate` method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciAppDB.test_update"></a>

#### test`_`update

```python
@pytest.mark.parametrize(
    "setup_data, update_data, expected_data",
    (
        (dict(), {
            "dummy_key": "dummy_value"
        }, {
            0: {
                "dummy_key": ["dummy_value"]
            }
        }),
        (
            dict(),
            {
                "dummy_key": ["dummy_value1", "dummy_value2"]
            },
            {
                0: {
                    "dummy_key": [["dummy_value1", "dummy_value2"]]
                }
            },
        ),
        (
            {
                "test": ["test"]
            },
            {
                "dummy_key": "dummy_value"
            },
            {
                0: {
                    "dummy_key": ["dummy_value"],
                    "test": ["test"]
                }
            },
        ),
        (
            {
                "test": ["test"]
            },
            {
                "test": "dummy_value"
            },
            {
                0: {
                    "test": ["test", "dummy_value"]
                }
            },
        ),
        (
            {
                "test": [["test"]]
            },
            {
                "test": ["dummy_value1", "dummy_value2"]
            },
            {
                0: {
                    "test": [["test"], ["dummy_value1", "dummy_value2"]]
                }
            },
        ),
        (
            {
                "test": ["test"]
            },
            {
                "test": ["dummy_value1", "dummy_value2"]
            },
            {
                0: {
                    "test": ["test", ["dummy_value1", "dummy_value2"]]
                }
            },
        ),
    ),
)
def test_update(setup_data: Dict, update_data: Dict,
                expected_data: Dict[int, Dict]) -> None
```

Test update db.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciAppDB.test_create"></a>

#### test`_`create

```python
@pytest.mark.parametrize(
    "replacement_value, expected_replacement",
    (
        (132, 132),
        ("test", "test"),
        (set("132"), ("1", "2", "3")),
        ({"132"}, ("132", )),
        (frozenset("231"), ("1", "2", "3")),
        (frozenset({"231"}), ("231", )),
        (("1", "3", "2"), ("1", "3", "2")),
        (["1", "5", "3"], ["1", "5", "3"]),
    ),
)
@pytest.mark.parametrize(
    "setup_data, cross_period_persisted_keys",
    (
        (dict(), frozenset()),
        ({
            "test": [["test"]]
        }, frozenset()),
        ({
            "test": [["test"]]
        }, frozenset({"test"})),
        ({
            "test": ["test"]
        }, frozenset({"test"})),
    ),
)
def test_create(replacement_value: Any, expected_replacement: Any,
                setup_data: Dict,
                cross_period_persisted_keys: FrozenSet[str]) -> None
```

Test `create` db.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciAppDB.test_create_key_not_in_db"></a>

#### test`_`create`_`key`_`not`_`in`_`db

```python
def test_create_key_not_in_db() -> None
```

Test the `create` method when a given or a cross-period key does not exist in the db.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciAppDB.test_cleanup"></a>

#### test`_`cleanup

```python
@pytest.mark.parametrize(
    "existing_data, cleanup_history_depth, cleanup_history_depth_current, expected",
    (
        (
            {
                1: {
                    "test": ["test", ["dummy_value1", "dummy_value2"]]
                }
            },
            0,
            None,
            {
                1: {
                    "test": ["test", ["dummy_value1", "dummy_value2"]]
                }
            },
        ),
        (
            {
                1: {
                    "test": ["test", ["dummy_value1", "dummy_value2"]]
                },
                2: {
                    "test": [0]
                },
            },
            0,
            None,
            {
                2: {
                    "test": [0]
                }
            },
        ),
        (
            {
                1: {
                    "test": ["test", ["dummy_value1", "dummy_value2"]]
                },
                2: {
                    "test": [0, 1, 2]
                },
            },
            0,
            0,
            {
                2: {
                    "test": [0, 1, 2]
                }
            },
        ),
        (
            {
                1: {
                    "test": ["test", ["dummy_value1", "dummy_value2"]]
                },
                2: {
                    "test": [0, 1, 2]
                },
            },
            0,
            1,
            {
                2: {
                    "test": [2]
                }
            },
        ),
        (
            {
                1: {
                    "test": ["test", ["dummy_value1", "dummy_value2"]]
                },
                2: {
                    "test": list(range(5))
                },
                3: {
                    "test": list(range(5, 10))
                },
                4: {
                    "test": list(range(10, 15))
                },
                5: {
                    "test": list(range(15, 20))
                },
            },
            3,
            0,
            {
                3: {
                    "test": list(range(5, 10))
                },
                4: {
                    "test": list(range(10, 15))
                },
                5: {
                    "test": list(range(15, 20))
                },
            },
        ),
        (
            {
                1: {
                    "test": ["test", ["dummy_value1", "dummy_value2"]]
                },
                2: {
                    "test": list(range(5))
                },
                3: {
                    "test": list(range(5, 10))
                },
                4: {
                    "test": list(range(10, 15))
                },
                5: {
                    "test": list(range(15, 20))
                },
            },
            5,
            3,
            {
                1: {
                    "test": ["test", ["dummy_value1", "dummy_value2"]]
                },
                2: {
                    "test": list(range(5))
                },
                3: {
                    "test": list(range(5, 10))
                },
                4: {
                    "test": list(range(10, 15))
                },
                5: {
                    "test": list(range(15 + 2, 20))
                },
            },
        ),
        (
            {
                1: {
                    "test": ["test", ["dummy_value1", "dummy_value2"]]
                },
                2: {
                    "test": list(range(5))
                },
                3: {
                    "test": list(range(5, 10))
                },
                4: {
                    "test": list(range(10, 15))
                },
                5: {
                    "test": list(range(15, 20))
                },
            },
            2,
            3,
            {
                4: {
                    "test": list(range(10, 15))
                },
                5: {
                    "test": list(range(15 + 2, 20))
                },
            },
        ),
        (
            {
                1: {
                    "test": ["test", ["dummy_value1", "dummy_value2"]]
                },
                2: {
                    "test": list(range(5))
                },
                3: {
                    "test": list(range(5, 10))
                },
                4: {
                    "test": list(range(10, 15))
                },
                5: {
                    "test": list(range(15, 20))
                },
            },
            0,
            1,
            {
                5: {
                    "test": [19]
                },
            },
        ),
    ),
)
def test_cleanup(existing_data: Dict[int, Dict[str, List[Any]]],
                 cleanup_history_depth: int,
                 cleanup_history_depth_current: Optional[int],
                 expected: Dict[int, Dict[str, List[Any]]]) -> None
```

Test cleanup db.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciAppDB.test_serialize"></a>

#### test`_`serialize

```python
def test_serialize() -> None
```

Test `serialize` method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciAppDB.test_sync"></a>

#### test`_`sync

```python
@pytest.mark.parametrize(
    "_data",
    ({
        "db_data": {
            0: {
                "test": [0]
            }
        },
        "slashing_config": "serialized_config"
    }, ),
)
def test_sync(_data: Dict[str, Dict[int, Dict[str, List[Any]]]]) -> None
```

Test `sync` method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciAppDB.test_sync_incorrect_data"></a>

#### test`_`sync`_`incorrect`_`data

```python
@pytest.mark.parametrize(
    "serialized_data, match",
    (
        (b"", "Could not decode data using "),
        (
            json.dumps({"both_mandatory_keys_missing": {}}),
            "internal error: Mandatory keys `db_data`, `slashing_config` are missing from the deserialized data: "
            "{'both_mandatory_keys_missing': {}}\nThe following serialized data were given: "
            '{"both_mandatory_keys_missing": {}}',
        ),
        (
            json.dumps({"db_data": {}}),
            "internal error: Mandatory keys `db_data`, `slashing_config` are missing from the deserialized data: "
            "{'db_data': {}}\nThe following serialized data were given: {\"db_data\": {}}",
        ),
        (
            json.dumps({"slashing_config": {}}),
            "internal error: Mandatory keys `db_data`, `slashing_config` are missing from the deserialized data: "
            "{'slashing_config': {}}\nThe following serialized data were given: {\"slashing_config\": {}}",
        ),
        (
            json.dumps({
                "db_data": {
                    "invalid_index": {}
                },
                "slashing_config": "anything"
            }),
            "An invalid index was found while trying to sync the db using data: ",
        ),
        (
            json.dumps({
                "db_data": "invalid",
                "slashing_config": "anything"
            }),
            "Could not decode db data with an invalid format: ",
        ),
    ),
)
def test_sync_incorrect_data(serialized_data: Any, match: str) -> None
```

Test `sync` method with incorrect data.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciAppDB.test_hash"></a>

#### test`_`hash

```python
def test_hash() -> None
```

Test `hash` method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestBaseSynchronizedData"></a>

## TestBaseSynchronizedData Objects

```python
class TestBaseSynchronizedData()
```

Test 'BaseSynchronizedData' class.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestBaseSynchronizedData.setup_method"></a>

#### setup`_`method

```python
def setup_method() -> None
```

Set up the tests.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestBaseSynchronizedData.test_slashing_config"></a>

#### test`_`slashing`_`config

```python
@given(text())
def test_slashing_config(slashing_config: str) -> None
```

Test the `slashing_config` property.

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

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestBaseSynchronizedData.test_consensus_threshold"></a>

#### test`_`consensus`_`threshold

```python
@pytest.mark.parametrize(
    "n_participants, given_threshold, expected_threshold",
    (
        (1, None, 1),
        (5, None, 4),
        (10, None, 7),
        (345, None, 231),
        (246236, None, 164158),
        (1, 1, 1),
        (5, 5, 5),
        (10, 7, 7),
        (10, 8, 8),
        (10, 9, 9),
        (10, 10, 10),
        (345, 300, 300),
        (246236, 194158, 194158),
    ),
)
def test_consensus_threshold(n_participants: int, given_threshold: int,
                             expected_threshold: int) -> None
```

Test the `consensus_threshold` property.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestBaseSynchronizedData.test_consensus_threshold_incorrect"></a>

#### test`_`consensus`_`threshold`_`incorrect

```python
@pytest.mark.parametrize(
    "n_participants, given_threshold",
    (
        (1, 2),
        (5, 2),
        (10, 4),
        (10, 11),
        (10, 18),
        (345, 200),
        (246236, 164157),
        (246236, 246237),
    ),
)
def test_consensus_threshold_incorrect(n_participants: int,
                                       given_threshold: int) -> None
```

Test the `consensus_threshold` property when an incorrect threshold value has been inserted to the db.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestBaseSynchronizedData.test_properties"></a>

#### test`_`properties

```python
def test_properties() -> None
```

Test several properties

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.DummyConcreteRound"></a>

## DummyConcreteRound Objects

```python
class DummyConcreteRound(AbstractRound)
```

A dummy concrete round's implementation.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.DummyConcreteRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BaseSynchronizedData, EventType]]
```

A dummy `end_block` implementation.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.DummyConcreteRound.check_payload"></a>

#### check`_`payload

```python
def check_payload(payload: BaseTxPayload) -> None
```

A dummy `check_payload` implementation.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.DummyConcreteRound.process_payload"></a>

#### process`_`payload

```python
def process_payload(payload: BaseTxPayload) -> None
```

A dummy `process_payload` implementation.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.DummyConcreteRound.check_majority_possible_with_new_vote"></a>

#### check`_`majority`_`possible`_`with`_`new`_`vote

```python
def check_majority_possible_with_new_vote(
        votes_by_participant: Dict[str, BaseTxPayload],
        new_voter: str,
        new_vote: BaseTxPayload,
        nb_participants: int,
        exception_cls: Type[ABCIAppException] = ABCIAppException) -> None
```

A dummy implementation for testing.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbstractRound"></a>

## TestAbstractRound Objects

```python
class TestAbstractRound()
```

Test the 'AbstractRound' class.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbstractRound.setup_method"></a>

#### setup`_`method

```python
def setup_method() -> None
```

Set up the tests.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbstractRound.test_auto_round_id"></a>

#### test`_`auto`_`round`_`id

```python
def test_auto_round_id() -> None
```

Test that the 'auto_round_id()' method works as expected.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbstractRound.test_must_not_set_round_id"></a>

#### test`_`must`_`not`_`set`_`round`_`id

```python
def test_must_not_set_round_id() -> None
```

Test that the 'round_id' must be set in concrete classes.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbstractRound.test_must_set_payload_class_type"></a>

#### test`_`must`_`set`_`payload`_`class`_`type

```python
def test_must_set_payload_class_type() -> None
```

Test that the 'payload_class' must be set in concrete classes.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbstractRound.test_check_payload_type_with_previous_round_transaction"></a>

#### test`_`check`_`payload`_`type`_`with`_`previous`_`round`_`transaction

```python
def test_check_payload_type_with_previous_round_transaction() -> None
```

Test check 'check_payload_type'.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbstractRound.test_check_payload_type"></a>

#### test`_`check`_`payload`_`type

```python
def test_check_payload_type() -> None
```

Test check 'check_payload_type'.

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
def test_check_majority_possible_raises_error_when_nb_participants_is_0(
) -> None
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
def test_check_majority_possible_passes_when_vote_set_nonempty_and_check_passes(
) -> None
```

Check that 'check_majority_possible' passes when set of votes is non-empty.

The check passes because:
- the threshold is 2
- the other voter can vote for the same item of the first voter

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbstractRound.test_check_majority_possible_passes_when_payload_attributes_majority_match"></a>

#### test`_`check`_`majority`_`possible`_`passes`_`when`_`payload`_`attributes`_`majority`_`match

```python
def test_check_majority_possible_passes_when_payload_attributes_majority_match(
) -> None
```

Test 'check_majority_possible' when set of votes is non-empty and the majority of the attribute values match.

The check passes because:
- the threshold is 3 (participants are 4)
- 3 voters have the same attribute value in their payload

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbstractRound.test_check_majority_possible_passes_when_vote_set_nonempty_and_check_doesnt_pass"></a>

#### test`_`check`_`majority`_`possible`_`passes`_`when`_`vote`_`set`_`nonempty`_`and`_`check`_`doesnt`_`pass

```python
def test_check_majority_possible_passes_when_vote_set_nonempty_and_check_doesnt_pass(
) -> None
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
def test_check_majority_possible_raises_error_when_new_voter_already_voted(
) -> None
```

Test 'check_majority_possible_with_new_vote' raises when new voter already voted.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbstractRound.test_check_majority_possible_raises_error_when_nb_participants_inconsistent"></a>

#### test`_`check`_`majority`_`possible`_`raises`_`error`_`when`_`nb`_`participants`_`inconsistent

```python
def test_check_majority_possible_raises_error_when_nb_participants_inconsistent(
) -> None
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

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestTimeouts.setup_method"></a>

#### setup`_`method

```python
def setup_method() -> None
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

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciApp.setup_method"></a>

#### setup`_`method

```python
def setup_method() -> None
```

Set up the test.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciApp.teardown_method"></a>

#### teardown`_`method

```python
def teardown_method() -> None
```

Teardown the test.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciApp.test_is_abstract"></a>

#### test`_`is`_`abstract

```python
@pytest.mark.parametrize("flag", (True, False))
def test_is_abstract(flag: bool) -> None
```

Test `is_abstract` property.

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

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciApp.test_get_synced_value"></a>

#### test`_`get`_`synced`_`value

```python
@pytest.mark.parametrize(
    "db_key, sync_classes, default, property_found",
    (
        ("", set(), "default", False),
        ("non_existing_key", {BaseSynchronizedData}, True, False),
        ("participants", {BaseSynchronizedData}, {}, False),
        ("is_keeper_set", {BaseSynchronizedData}, True, True),
    ),
)
def test_get_synced_value(db_key: str,
                          sync_classes: Set[Type[BaseSynchronizedData]],
                          default: Any, property_found: bool) -> None
```

Test the `_get_synced_value` method.

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

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciApp.test_get_all_rounds_classes"></a>

#### test`_`get`_`all`_`rounds`_`classes

```python
@pytest.mark.parametrize("include_background_rounds", (True, False))
def test_get_all_rounds_classes(include_background_rounds: bool) -> None
```

Test the get all rounds getter.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciApp.test_get_all_rounds_classes_bg_ever_running"></a>

#### test`_`get`_`all`_`rounds`_`classes`_`bg`_`ever`_`running

```python
def test_get_all_rounds_classes_bg_ever_running() -> None
```

Test the get all rounds when the background round is of an ever running type.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciApp.test_add_background_app"></a>

#### test`_`add`_`background`_`app

```python
def test_add_background_app() -> None
```

Tests the add method for the background apps.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciApp.test_bg_apps_prioritized_independent_groups"></a>

#### test`_`bg`_`apps`_`prioritized`_`independent`_`groups

```python
def test_bg_apps_prioritized_independent_groups() -> None
```

Test that bg_apps_prioritized returns independent lists per group.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciApp.test_cleanup"></a>

#### test`_`cleanup

```python
def test_cleanup() -> None
```

Test the cleanup method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciApp.test_check_transaction_for_termination_round"></a>

#### test`_`check`_`transaction`_`for`_`termination`_`round

```python
@mock.patch.object(ConcreteBackgroundRound, "check_transaction")
@pytest.mark.parametrize(
    "transaction",
    [mock.MagicMock(payload=DUMMY_CONCRETE_BACKGROUND_PAYLOAD)],
)
def test_check_transaction_for_termination_round(
        check_transaction_mock: mock.Mock, transaction: Transaction) -> None
```

Tests process_transaction when it's a transaction meant for the termination app.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAbciApp.test_process_transaction_for_termination_round"></a>

#### test`_`process`_`transaction`_`for`_`termination`_`round

```python
@mock.patch.object(ConcreteBackgroundRound, "process_transaction")
@pytest.mark.parametrize(
    "transaction",
    [mock.MagicMock(payload=DUMMY_CONCRETE_BACKGROUND_PAYLOAD)],
)
def test_process_transaction_for_termination_round(
        process_transaction_mock: mock.Mock, transaction: Transaction) -> None
```

Tests process_transaction when it's a transaction meant for the termination app.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestOffenceTypeFns"></a>

## TestOffenceTypeFns Objects

```python
class TestOffenceTypeFns()
```

Test `OffenceType`-related functions.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestOffenceTypeFns.test_light_offences"></a>

#### test`_`light`_`offences

```python
@staticmethod
def test_light_offences() -> None
```

Test `light_offences` function.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestOffenceTypeFns.test_serious_offences"></a>

#### test`_`serious`_`offences

```python
@staticmethod
def test_serious_offences() -> None
```

Test `serious_offences` function.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.availability_window_data"></a>

#### availability`_`window`_`data

```python
@composite
def availability_window_data(draw: DrawFn) -> Dict[str, int]
```

A strategy for building valid availability window data.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAvailabilityWindow"></a>

## TestAvailabilityWindow Objects

```python
class TestAvailabilityWindow()
```

Test `AvailabilityWindow`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAvailabilityWindow.test_not_equal"></a>

#### test`_`not`_`equal

```python
@staticmethod
@given(integers(min_value=1, max_value=100))
def test_not_equal(max_length: int) -> None
```

Test the `add` method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAvailabilityWindow.test_add"></a>

#### test`_`add

```python
@staticmethod
@given(integers(min_value=0, max_value=100), data())
def test_add(max_length: int, hypothesis_data: Any) -> None
```

Test the `add` method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAvailabilityWindow.test_to_dict"></a>

#### test`_`to`_`dict

```python
@staticmethod
@given(
    max_length=integers(min_value=1, max_value=30_000),
    num_positive=integers(min_value=0),
    num_negative=integers(min_value=0),
)
@pytest.mark.parametrize(
    "window, expected_serialization",
    (
        (deque(()), 0),
        (deque((False, False, False)), 0),
        (deque((True, False, True)), 5),
        (deque((True for _ in range(3))), 7),
        (
            deque((True for _ in range(1000))),
            int("10715086071862673209484250490600018105614048117055336074437503883703510511249361224931983788156958"
                "58127594672917553146825187145285692314043598457757469857480393456777482423098542107460506237114187"
                "79541821530464749835819412673987675591655439460770629145711964776865421676604298316526243868372056"
                "68069375"),
        ),
    ),
)
def test_to_dict(max_length: int, num_positive: int, num_negative: int,
                 window: Deque, expected_serialization: int) -> None
```

Test `to_dict` method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAvailabilityWindow.test_validate_key"></a>

#### test`_`validate`_`key

```python
@staticmethod
@pytest.mark.parametrize(
    "data_, key, validator, expected_error",
    (
        ({
            "a": 1,
            "b": 2,
            "c": 3
        }, "a", lambda x: x > 0, None),
        (
            {
                "a": 1,
                "b": 2,
                "c": 3
            },
            "d",
            lambda x: x > 0,
            r"Missing required key: d\.",
        ),
        (
            {
                "a": "1",
                "b": 2,
                "c": 3
            },
            "a",
            lambda x: x > 0,
            r"a must be of type int\.",
        ),
        (
            {
                "a": -1,
                "b": 2,
                "c": 3
            },
            "a",
            lambda x: x > 0,
            r"a has invalid value -1\.",
        ),
    ),
)
def test_validate_key(data_: dict, key: str, validator: Callable,
                      expected_error: Optional[str]) -> None
```

Test the `_validate_key` method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAvailabilityWindow.test_validate_negative"></a>

#### test`_`validate`_`negative

```python
@staticmethod
@pytest.mark.parametrize(
    "data_, error_regex",
    (
        ("not a dict", r"Expected dict, got"),
        (
            {
                "max_length": -1,
                "array": 42,
                "num_positive": 10,
                "num_negative": 0
            },
            r"max_length",
        ),
        (
            {
                "max_length": 2,
                "array": 4,
                "num_positive": 10,
                "num_negative": 0
            },
            r"array",
        ),
        (
            {
                "max_length": 8,
                "array": 42,
                "num_positive": -1,
                "num_negative": 0
            },
            r"num_positive",
        ),
        (
            {
                "max_length": 8,
                "array": 42,
                "num_positive": 10,
                "num_negative": -1
            },
            r"num_negative",
        ),
    ),
)
def test_validate_negative(data_: dict, error_regex: str) -> None
```

Negative tests for the `_validate` method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAvailabilityWindow.test_validate_positive"></a>

#### test`_`validate`_`positive

```python
@staticmethod
@given(availability_window_data())
def test_validate_positive(data_: Dict[str, int]) -> None
```

Positive tests for the `_validate` method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAvailabilityWindow.test_from_dict"></a>

#### test`_`from`_`dict

```python
@staticmethod
@given(availability_window_data())
def test_from_dict(data_: Dict[str, int]) -> None
```

Test `from_dict` method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestAvailabilityWindow.test_to_dict_and_back"></a>

#### test`_`to`_`dict`_`and`_`back

```python
@staticmethod
@given(availability_window_data())
def test_to_dict_and_back(data_: Dict[str, int]) -> None
```

Test that the `from_dict` produces an object that generates the input data again when calling `to_dict`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestOffenceStatus"></a>

## TestOffenceStatus Objects

```python
class TestOffenceStatus()
```

Test the `OffenceStatus` dataclass.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestOffenceStatus.test_slash_amount"></a>

#### test`_`slash`_`amount

```python
@staticmethod
@pytest.mark.parametrize("custom_amount", (0, 5))
@pytest.mark.parametrize("light_unit_amount, serious_unit_amount", ((1, 2), ))
@pytest.mark.parametrize(
    "validator_downtime, invalid_payload, blacklisted, suspected, "
    "num_unknown_offenses, num_double_signed, num_light_client_attack, expected",
    (
        (False, False, False, False, 0, 0, 0, 0),
        (True, False, False, False, 0, 0, 0, 1),
        (False, True, False, False, 0, 0, 0, 1),
        (False, False, True, False, 0, 0, 0, 1),
        (False, False, False, True, 0, 0, 0, 1),
        (False, False, False, False, 1, 0, 0, 2),
        (False, False, False, False, 0, 1, 0, 2),
        (False, False, False, False, 0, 0, 1, 2),
        (False, False, False, False, 0, 2, 1, 6),
        (False, True, False, True, 5, 2, 1, 18),
        (True, True, True, True, 5, 2, 1, 20),
    ),
)
def test_slash_amount(custom_amount: int, light_unit_amount: int,
                      serious_unit_amount: int, validator_downtime: bool,
                      invalid_payload: bool, blacklisted: bool,
                      suspected: bool, num_unknown_offenses: int,
                      num_double_signed: int, num_light_client_attack: int,
                      expected: int) -> None
```

Test the `slash_amount` method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.offence_tracking"></a>

#### offence`_`tracking

```python
@composite
def offence_tracking(draw: DrawFn) -> Tuple[Evidences, LastCommitInfo]
```

A strategy for building offences reported by Tendermint.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.offence_status"></a>

#### offence`_`status

```python
@composite
def offence_status(draw: DrawFn) -> OffenceStatus
```

Build an offence status instance.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestOffenseStatusEncoderDecoder"></a>

## TestOffenseStatusEncoderDecoder Objects

```python
class TestOffenseStatusEncoderDecoder()
```

Test the `OffenseStatusEncoder` and the `OffenseStatusDecoder`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestOffenseStatusEncoderDecoder.test_encode_decode_offense_status"></a>

#### test`_`encode`_`decode`_`offense`_`status

```python
@staticmethod
@given(dictionaries(keys=text(), values=offence_status(), min_size=1))
def test_encode_decode_offense_status(offense_status: str) -> None
```

Test encoding an offense status mapping and then decoding it by using the custom encoder/decoder.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestOffenseStatusEncoderDecoder.test_encode_unknown"></a>

#### test`_`encode`_`unknown

```python
def test_encode_unknown() -> None
```

Test the encoder with an unknown input.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence"></a>

## TestRoundSequence Objects

```python
class TestRoundSequence()
```

Test the RoundSequence class.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.setup_method"></a>

#### setup`_`method

```python
def setup_method() -> None
```

Set up the test.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_slashing_properties"></a>

#### test`_`slashing`_`properties

```python
@pytest.mark.parametrize(
    "property_name, set_twice_exc, config_exc",
    ((
        "validator_to_agent",
        "The mapping of the validators' addresses to their agent addresses can only be set once. "
        "Attempted to set with {new_content_attempt} but it has content already: {value}.",
        "The mapping of the validators' addresses to their agent addresses has not been set.",
    ), ),
)
@given(data())
def test_slashing_properties(property_name: str, set_twice_exc: str,
                             config_exc: str, _data: Any) -> None
```

Test `validator_to_agent` getter and setter.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_sync_db_and_slashing"></a>

#### test`_`sync`_`db`_`and`_`slashing

```python
@mock.patch("json.loads", return_value="json_serializable")
@pytest.mark.parametrize("slashing_config", (None, "", "test"))
def test_sync_db_and_slashing(mock_loads: mock.MagicMock,
                              slashing_config: str) -> None
```

Test the `sync_db_and_slashing` method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_store_offence_status"></a>

#### test`_`store`_`offence`_`status

```python
@mock.patch("json.dumps")
@pytest.mark.parametrize("slashing_enabled", (True, False))
def test_store_offence_status(mock_dumps: mock.MagicMock,
                              slashing_enabled: bool) -> None
```

Test the `store_offence_status` method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_get_agent_address"></a>

#### test`_`get`_`agent`_`address

```python
@given(
    validator=builds(Validator, address=binary(), power=integers()),
    agent_address=text(),
)
def test_get_agent_address(validator: Validator, agent_address: str) -> None
```

Test `get_agent_address` method.

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

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_block_before_blockchain_is_init"></a>

#### test`_`block`_`before`_`blockchain`_`is`_`init

```python
def test_block_before_blockchain_is_init(caplog: LogCaptureFixture) -> None
```

Test block received before blockchain initialized.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_last_round_transition_root_hash"></a>

#### test`_`last`_`round`_`transition`_`root`_`hash

```python
@pytest.mark.parametrize("last_round_transition_root_hash", (b"", b"test"))
def test_last_round_transition_root_hash(
        last_round_transition_root_hash: bytes) -> None
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
def test_block_stall_deadline_expired(
        block_stall_deadline: datetime.datetime) -> None
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

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_track_tm_offences"></a>

#### test`_`track`_`tm`_`offences

```python
@given(offence_tracking())
@settings(suppress_health_check=[HealthCheck.too_slow])
def test_track_tm_offences(offences: Tuple[Evidences, LastCommitInfo]) -> None
```

Test `_track_tm_offences` method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_track_app_offences"></a>

#### test`_`track`_`app`_`offences

```python
@mock.patch.object(abci_base, "ADDRESS_LENGTH", len("agent_i"))
def test_track_app_offences() -> None
```

Test `_track_app_offences` method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_handle_slashing_not_configured"></a>

#### test`_`handle`_`slashing`_`not`_`configured

```python
@given(builds(SlashingNotConfiguredError, text()))
def test_handle_slashing_not_configured(
        exc: SlashingNotConfiguredError) -> None
```

Test `_handle_slashing_not_configured` method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_try_track_offences"></a>

#### test`_`try`_`track`_`offences

```python
@pytest.mark.parametrize("_track_offences_raises", (True, False))
def test_try_track_offences(_track_offences_raises: bool) -> None
```

Test `_try_track_offences` method.

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

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.last_round_values_updated"></a>

#### last`_`round`_`values`_`updated

```python
def last_round_values_updated(any_: bool = True) -> bool
```

Check if the values for the last round-related attributes have been updated.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_update_round"></a>

#### test`_`update`_`round

```python
@mock.patch.object(AbciApp, "process_event")
@mock.patch.object(RoundSequence, "serialized_offence_status")
@pytest.mark.parametrize("end_block_res", (None, (MagicMock(), MagicMock())))
@pytest.mark.parametrize(
    "slashing_enabled, offence_status_",
    (
        (
            False,
            False,
        ),
        (
            False,
            True,
        ),
        (
            False,
            False,
        ),
        (
            True,
            True,
        ),
    ),
)
def test_update_round(serialized_offence_status_mock: mock.Mock,
                      process_event_mock: mock.Mock,
                      end_block_res: Optional[Tuple[BaseSynchronizedData,
                                                    Any]],
                      slashing_enabled: bool, offence_status_: dict) -> None
```

Test '_update_round' method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_update_round_when_termination_returns"></a>

#### test`_`update`_`round`_`when`_`termination`_`returns

```python
@mock.patch.object(AbciApp, "process_event")
@pytest.mark.parametrize(
    "termination_round_result, current_round_result",
    [
        (None, None),
        (None, (MagicMock(), MagicMock())),
        ((MagicMock(), MagicMock()), None),
        ((MagicMock(), MagicMock()), (MagicMock(), MagicMock())),
    ],
)
def test_update_round_when_termination_returns(
        process_event_mock: mock.Mock,
        termination_round_result: Optional[Tuple[BaseSynchronizedData, Any]],
        current_round_result: Optional[Tuple[BaseSynchronizedData,
                                             Any]]) -> None
```

Test '_update_round' method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_reset_state"></a>

#### test`_`reset`_`state

```python
@pytest.mark.parametrize("restart_from_round", (ConcreteRoundA, MagicMock()))
@pytest.mark.parametrize("serialized_db_state", (None, "serialized state"))
@given(integers())
def test_reset_state(restart_from_round: AbstractRound,
                     serialized_db_state: str, round_count: int) -> None
```

Tests reset_state

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_reset_to_default_params"></a>

#### test`_`reset`_`to`_`default`_`params

```python
def test_reset_to_default_params() -> None
```

Tests _reset_to_default_params.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestRoundSequence.test_add_pending_offence"></a>

#### test`_`add`_`pending`_`offence

```python
def test_add_pending_offence() -> None
```

Tests add_pending_offence.

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
def test_meta_abci_app_when_final_round_not_subclass_of_degenerate_round(
) -> None
```

Test instantiation of meta-class when a final round is not a subclass of DegenerateRound.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.test_synchronized_data_type_on_abci_app_init"></a>

#### test`_`synchronized`_`data`_`type`_`on`_`abci`_`app`_`init

```python
def test_synchronized_data_type_on_abci_app_init(
        caplog: LogCaptureFixture) -> None
```

Test synchronized data access

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.test_get_name"></a>

#### test`_`get`_`name

```python
def test_get_name() -> None
```

Test the get_name method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.test_pending_offences_payload"></a>

#### test`_`pending`_`offences`_`payload

```python
@pytest.mark.parametrize(
    "sender, accused_agent_address, offense_round, offense_type_value, last_transition_timestamp, time_to_live, custom_amount",
    ((
        "sender",
        "test_address",
        90,
        3,
        10,
        2,
        10,
    ), ),
)
def test_pending_offences_payload(sender: str, accused_agent_address: str,
                                  offense_round: int, offense_type_value: int,
                                  last_transition_timestamp: int,
                                  time_to_live: int,
                                  custom_amount: int) -> None
```

Test `PendingOffencesPayload`

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestPendingOffencesRound"></a>

## TestPendingOffencesRound Objects

```python
class TestPendingOffencesRound(BaseRoundTestClass)
```

Tests for `PendingOffencesRound`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base.TestPendingOffencesRound.test_run"></a>

#### test`_`run

```python
@given(
    accused_agent_address=sampled_from(list(get_participants())),
    offense_round=integers(min_value=0),
    offense_type_value=sampled_from(
        [value.value for value in OffenseType.__members__.values()]),
    last_transition_timestamp=floats(
        min_value=timegm(datetime.datetime(1971, 1, 1).utctimetuple()),
        max_value=timegm(datetime.datetime(8000, 1, 1).utctimetuple()) - 2000,
    ),
    time_to_live=floats(min_value=1, max_value=2000),
    custom_amount=integers(min_value=0),
)
def test_run(accused_agent_address: str, offense_round: int,
             offense_type_value: int, last_transition_timestamp: float,
             time_to_live: float, custom_amount: int) -> None
```

Run tests.

