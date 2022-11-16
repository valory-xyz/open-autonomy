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

               public-endpoints section in https://drand.love/developer/http-api/
- `data`: dictionary containing drand parameters.
- `pubkey`: league of entropy public key

**Returns**:

bool, error message

<a id="packages.valory.skills.abstract_round_abci.utils.to_int"></a>

#### to`_`int

```python
def to_int(most_voted_estimate: float, decimals: int) -> int
```

Convert to int.

<a id="packages.valory.skills.abstract_round_abci.utils.get_data_from_nested_dict"></a>

#### get`_`data`_`from`_`nested`_`dict

```python
def get_data_from_nested_dict(nested_dict: Dict, keys: str, separator: str = ":") -> Any
```

Gets content from a nested dictionary, using serialized response keys which are split by a given separator.

**Arguments**:

Choose the separator carefully, so that it does not conflict with any character of the keys.

- `nested_dict`: the nested dictionary to get the content from
- `keys`: the keys to use on the nested dictionary in order to get the content
- `separator`: the separator to use in order to get the keys list.

**Returns**:

the content result

<a id="packages.valory.skills.abstract_round_abci.utils.get_value_with_type"></a>

#### get`_`value`_`with`_`type

```python
def get_value_with_type(value: Any, type_name: str) -> Any
```

Get the given value as the specified type.

