<a id="packages.valory.skills.abstract_round_abci.utils"></a>

# packages.valory.skills.abstract`_`round`_`abci.utils

This module contains utility functions for the 'abstract_round_abci' skill.

<a id="packages.valory.skills.abstract_round_abci.utils.VerifyDrand"></a>

## VerifyDrand Objects

```python
class VerifyDrand()
```

Tool to verify Randomness retrieved from various external APIs.

The ciphersuite used is BLS_SIG_BLS12381G2_XMD:SHA-256_SSWU_RO_NUL_

cryptographic-specification section in https://drand.love/docs/specification/
https://github.com/ethereum/py_ecc

<a id="packages.valory.skills.abstract_round_abci.utils.VerifyDrand.verify"></a>

#### verify

```python
def verify(data: Dict, pubkey: str) -> Tuple[bool, Optional[str]]
```

Verify drand value retried from external APIs.

**Arguments**:

- `data`: dictionary containing drand parameters.
- `pubkey`: league of entropy public key
public-endpoints section in https://drand.love/developer/http-api/

**Returns**:

bool, error message

<a id="packages.valory.skills.abstract_round_abci.utils.get_data_from_nested_dict"></a>

#### get`_`data`_`from`_`nested`_`dict

```python
def get_data_from_nested_dict(nested_dict: Dict,
                              keys: str,
                              separator: str = ":") -> Any
```

Gets content from a nested dictionary, using serialized response keys which are split by a given separator.

**Arguments**:

- `nested_dict`: the nested dictionary to get the content from
- `keys`: the keys to use on the nested dictionary in order to get the content
- `separator`: the separator to use in order to get the keys list.
Choose the separator carefully, so that it does not conflict with any character of the keys.

**Returns**:

the content result

<a id="packages.valory.skills.abstract_round_abci.utils.get_value_with_type"></a>

#### get`_`value`_`with`_`type

```python
def get_value_with_type(value: Any, type_name: str) -> Any
```

Get the given value as the specified type.

<a id="packages.valory.skills.abstract_round_abci.utils.parse_tendermint_p2p_url"></a>

#### parse`_`tendermint`_`p2p`_`url

```python
def parse_tendermint_p2p_url(url: str) -> Tuple[str, int]
```

Parse tendermint P2P url.

<a id="packages.valory.skills.abstract_round_abci.utils.get_origin"></a>

#### get`_`origin

```python
def get_origin(tp)
```

Get the unsubscripted version of a type.

This supports generic types, Callable, Tuple, Union, Literal, Final and
ClassVar. Returns None for unsupported types.

**Examples**:

  get_origin(Literal[42]) is Literal
  get_origin(int) is None
  get_origin(ClassVar[int]) is ClassVar
  get_origin(Generic) is Generic
  get_origin(Generic[T]) is Generic
  get_origin(Union[T, int]) is Union
  get_origin(List[Tuple[T, T]][int]) == list

<a id="packages.valory.skills.abstract_round_abci.utils.get_args"></a>

#### get`_`args

```python
def get_args(tp)
```

Get type arguments with all substitutions performed.

For unions, basic simplifications used by Union constructor are performed.

**Examples**:

  get_args(Dict[str, int]) == (str, int)
  get_args(int) == ()
  get_args(Union[int, Union[T, int], str][int]) == (int, str)
  get_args(Union[int, Tuple[T, int]][str]) == (int, Tuple[str, int])
  get_args(Callable[[], T][int]) == ([], int)

<a id="packages.valory.skills.abstract_round_abci.utils.is_pep604_union"></a>

#### is`_`pep604`_`union

```python
def is_pep604_union(ty: Type[Any]) -> bool
```

Check if a type is a PEP 604 union.

<a id="packages.valory.skills.abstract_round_abci.utils.AutonomyTypeError"></a>

## AutonomyTypeError Objects

```python
class AutonomyTypeError(TypeError)
```

Type Error for the Autonomy type check system.

<a id="packages.valory.skills.abstract_round_abci.utils.AutonomyTypeError.__init__"></a>

#### `__`init`__`

```python
def __init__(ty: Type[Any], value: Any, path: Optional[List[str]] = None)
```

Initialize AutonomyTypeError.

<a id="packages.valory.skills.abstract_round_abci.utils.AutonomyTypeError.__str__"></a>

#### `__`str`__`

```python
def __str__() -> str
```

Get string representation of AutonomyTypeError.

<a id="packages.valory.skills.abstract_round_abci.utils.Result"></a>

#### Result

returns error context

<a id="packages.valory.skills.abstract_round_abci.utils.check"></a>

#### check

```python
def check(value: Any, ty: Type[Any]) -> Result
```

Check a value against a type.

__Examples__

>>> assert is_error(check(1, str))
>>> assert not is_error(check(1, int))
>>> assert is_error(check(1, list))
>>> assert is_error(check(1.3, int))
>>> assert is_error(check(1.3, Union[str, int]))

<a id="packages.valory.skills.abstract_round_abci.utils.check_class"></a>

#### check`_`class

```python
def check_class(value: Any, ty: Type[Any]) -> Result
```

Check class type.

<a id="packages.valory.skills.abstract_round_abci.utils.check_int"></a>

#### check`_`int

```python
def check_int(value: Any, ty: Type[Any]) -> Result
```

Check int type.

<a id="packages.valory.skills.abstract_round_abci.utils.check_literal"></a>

#### check`_`literal

```python
def check_literal(value: Any, ty: Type[Any]) -> Result
```

Check literal type.

<a id="packages.valory.skills.abstract_round_abci.utils.check_tuple"></a>

#### check`_`tuple

```python
def check_tuple(value: Any, ty: Type[Tuple[Any, ...]]) -> Result
```

Check tuple type.

<a id="packages.valory.skills.abstract_round_abci.utils.check_union"></a>

#### check`_`union

```python
def check_union(value: Any, ty: Type[Any]) -> Result
```

Check union type.

<a id="packages.valory.skills.abstract_round_abci.utils.check_mono_container"></a>

#### check`_`mono`_`container

```python
def check_mono_container(
    value: Any, ty: Union[Type[List[Any]], Type[Set[Any]],
                          Type[FrozenSet[Any]]]) -> Result
```

Check mono container type.

<a id="packages.valory.skills.abstract_round_abci.utils.check_dict"></a>

#### check`_`dict

```python
def check_dict(value: Dict[Any, Any], ty: Type[Dict[Any, Any]]) -> Result
```

Check dict type.

<a id="packages.valory.skills.abstract_round_abci.utils.check_dataclass"></a>

#### check`_`dataclass

```python
def check_dataclass(value: Any, ty: Type[Any]) -> Result
```

Check dataclass type.

<a id="packages.valory.skills.abstract_round_abci.utils.check_typeddict"></a>

#### check`_`typeddict

```python
def check_typeddict(value: Any, ty: Type[Any]) -> Result
```

Check typeddict type.

<a id="packages.valory.skills.abstract_round_abci.utils.is_typevar"></a>

#### is`_`typevar

```python
def is_typevar(ty: Type[Any]) -> TypeGuard[TypeVar]
```

Check typevar.

<a id="packages.valory.skills.abstract_round_abci.utils.is_error"></a>

#### is`_`error

```python
def is_error(ret: Result) -> TypeGuard[AutonomyTypeError]
```

Check error.

<a id="packages.valory.skills.abstract_round_abci.utils.is_typeddict"></a>

#### is`_`typeddict

```python
def is_typeddict(ty: Type[Any]) -> TypeGuard[Type[TypedDict]]
```

Check typeddict.

<a id="packages.valory.skills.abstract_round_abci.utils.check_type"></a>

#### check`_`type

```python
def check_type(name: str, value: Any, type_hint: Any) -> None
```

Check value against type hint recursively

<a id="packages.valory.skills.abstract_round_abci.utils.is_primitive_or_none"></a>

#### is`_`primitive`_`or`_`none

```python
def is_primitive_or_none(obj: Any) -> bool
```

Checks if the given object is a primitive type or `None`.

<a id="packages.valory.skills.abstract_round_abci.utils.is_json_serializable"></a>

#### is`_`json`_`serializable

```python
def is_json_serializable(obj: Any) -> bool
```

Checks if the given object is json serializable.

<a id="packages.valory.skills.abstract_round_abci.utils.filter_negative"></a>

#### filter`_`negative

```python
def filter_negative(mapping: Dict[str, int]) -> Iterator[str]
```

Return the keys of a dictionary for which the values are negative integers.

<a id="packages.valory.skills.abstract_round_abci.utils.consensus_threshold"></a>

#### consensus`_`threshold

```python
def consensus_threshold(nb: int) -> int
```

Get consensus threshold.

**Arguments**:

- `nb`: the number of participants

**Returns**:

the consensus threshold

<a id="packages.valory.skills.abstract_round_abci.utils.inverse"></a>

#### inverse

```python
def inverse(dict_: Dict[KeyType, ValueType]) -> Dict[ValueType, List[KeyType]]
```

Get the inverse of a dictionary.

