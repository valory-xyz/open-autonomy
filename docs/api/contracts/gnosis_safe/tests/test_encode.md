<a id="packages.valory.contracts.gnosis_safe.tests.test_encode"></a>

# packages.valory.contracts.gnosis`_`safe.tests.test`_`encode

Unit tests for the EIP-712 encode helpers.

<a id="packages.valory.contracts.gnosis_safe.tests.test_encode.test_encode_forwards_to_codec_registry"></a>

#### test`_`encode`_`forwards`_`to`_`codec`_`registry

```python
def test_encode_forwards_to_codec_registry() -> None
```

`encode` resolves an encoder from the codec registry and calls it.

<a id="packages.valory.contracts.gnosis_safe.tests.test_encode.test_to_string_bytes_passthrough"></a>

#### test`_`to`_`string`_`bytes`_`passthrough

```python
def test_to_string_bytes_passthrough() -> None
```

`to_string` leaves a bytes input untouched.

<a id="packages.valory.contracts.gnosis_safe.tests.test_encode.test_to_string_str_encodes_utf8"></a>

#### test`_`to`_`string`_`str`_`encodes`_`utf8

```python
def test_to_string_str_encodes_utf8() -> None
```

`to_string` encodes a str input as UTF-8.

<a id="packages.valory.contracts.gnosis_safe.tests.test_encode.test_to_string_int_encodes_as_decimal_digits"></a>

#### test`_`to`_`string`_`int`_`encodes`_`as`_`decimal`_`digits

```python
def test_to_string_int_encodes_as_decimal_digits() -> None
```

`to_string` renders an int as its decimal UTF-8 string.

<a id="packages.valory.contracts.gnosis_safe.tests.test_encode.test_to_string_rejects_unsupported_type"></a>

#### test`_`to`_`string`_`rejects`_`unsupported`_`type

```python
def test_to_string_rejects_unsupported_type() -> None
```

`to_string` raises on unsupported types (mirrors original).

<a id="packages.valory.contracts.gnosis_safe.tests.test_encode.test_sha3_256_delegates_to_ledger_keccak"></a>

#### test`_`sha3`_`256`_`delegates`_`to`_`ledger`_`keccak

```python
def test_sha3_256_delegates_to_ledger_keccak() -> None
```

`sha3_256` calls `ledger_api.api.keccak`.

<a id="packages.valory.contracts.gnosis_safe.tests.test_encode.test_sha3_coerces_to_bytes_before_keccak"></a>

#### test`_`sha3`_`coerces`_`to`_`bytes`_`before`_`keccak

```python
def test_sha3_coerces_to_bytes_before_keccak() -> None
```

`sha3` runs the seed through `to_string` before hashing.

<a id="packages.valory.contracts.gnosis_safe.tests.test_encode.test_scan_bin_handles_str_0x_prefix"></a>

#### test`_`scan`_`bin`_`handles`_`str`_`0x`_`prefix

```python
def test_scan_bin_handles_str_0x_prefix() -> None
```

`scan_bin` strips a leading ``0x`` before hex decoding.

<a id="packages.valory.contracts.gnosis_safe.tests.test_encode.test_scan_bin_handles_unprefixed_hex"></a>

#### test`_`scan`_`bin`_`handles`_`unprefixed`_`hex

```python
def test_scan_bin_handles_unprefixed_hex() -> None
```

`scan_bin` accepts hex without a ``0x`` prefix.

<a id="packages.valory.contracts.gnosis_safe.tests.test_encode.test_create_struct_definition_formats_fields"></a>

#### test`_`create`_`struct`_`definition`_`formats`_`fields

```python
def test_create_struct_definition_formats_fields() -> None
```

`create_struct_definition` formats ``Name(type name,...)``.

<a id="packages.valory.contracts.gnosis_safe.tests.test_encode.test_find_dependencies_returns_reachable_types"></a>

#### test`_`find`_`dependencies`_`returns`_`reachable`_`types

```python
def test_find_dependencies_returns_reachable_types() -> None
```

`find_dependencies` adds every reachable named type.

<a id="packages.valory.contracts.gnosis_safe.tests.test_encode.test_find_dependencies_stops_on_already_seen"></a>

#### test`_`find`_`dependencies`_`stops`_`on`_`already`_`seen

```python
def test_find_dependencies_stops_on_already_seen() -> None
```

A type already in the set is not re-traversed (early return).

<a id="packages.valory.contracts.gnosis_safe.tests.test_encode.test_find_dependencies_stops_on_unknown_name"></a>

#### test`_`find`_`dependencies`_`stops`_`on`_`unknown`_`name

```python
def test_find_dependencies_stops_on_unknown_name() -> None
```

Non-registered types short-circuit without adding to the set.

<a id="packages.valory.contracts.gnosis_safe.tests.test_encode.test_create_schema_builds_sorted_definition"></a>

#### test`_`create`_`schema`_`builds`_`sorted`_`definition

```python
def test_create_schema_builds_sorted_definition() -> None
```

`create_schema` joins the primary + sorted dependency definitions.

<a id="packages.valory.contracts.gnosis_safe.tests.test_encode.test_create_schema_handles_array_type_names"></a>

#### test`_`create`_`schema`_`handles`_`array`_`type`_`names

```python
def test_create_schema_handles_array_type_names() -> None
```

Array type names (``Foo[]``) are stripped before lookup.

<a id="packages.valory.contracts.gnosis_safe.tests.test_encode.test_create_schema_hash_composes_encode_and_sha3"></a>

#### test`_`create`_`schema`_`hash`_`composes`_`encode`_`and`_`sha3

```python
def test_create_schema_hash_composes_encode_and_sha3() -> None
```

`create_schema_hash` returns ``encode("bytes32", keccak(schema))``.

<a id="packages.valory.contracts.gnosis_safe.tests.test_encode.test_encode_value_string_branch"></a>

#### test`_`encode`_`value`_`string`_`branch

```python
def test_encode_value_string_branch() -> None
```

A ``string`` field is hashed then encoded as ``bytes32``.

<a id="packages.valory.contracts.gnosis_safe.tests.test_encode.test_encode_value_bytes_branch_goes_through_scan_bin"></a>

#### test`_`encode`_`value`_`bytes`_`branch`_`goes`_`through`_`scan`_`bin

```python
def test_encode_value_bytes_branch_goes_through_scan_bin() -> None
```

A ``bytes`` field is hex-decoded via ``scan_bin`` before hashing.

<a id="packages.valory.contracts.gnosis_safe.tests.test_encode.test_encode_value_struct_branch"></a>

#### test`_`encode`_`value`_`struct`_`branch

```python
def test_encode_value_struct_branch() -> None
```

A custom struct type recurses through ``encode_data``.

<a id="packages.valory.contracts.gnosis_safe.tests.test_encode.test_encode_value_array_branch"></a>

#### test`_`encode`_`value`_`array`_`branch

```python
def test_encode_value_array_branch() -> None
```

A ``T[]`` field encodes each element then hashes the concatenation.

<a id="packages.valory.contracts.gnosis_safe.tests.test_encode.test_encode_value_primitive_fallback"></a>

#### test`_`encode`_`value`_`primitive`_`fallback

```python
def test_encode_value_primitive_fallback() -> None
```

Primitive ABI types fall through to the default ``encode`` path.

<a id="packages.valory.contracts.gnosis_safe.tests.test_encode.test_encode_data_concats_schema_hash_and_field_values"></a>

#### test`_`encode`_`data`_`concats`_`schema`_`hash`_`and`_`field`_`values

```python
def test_encode_data_concats_schema_hash_and_field_values() -> None
```

Test that `encode_data` prefixes field encodings with the schema hash.

<a id="packages.valory.contracts.gnosis_safe.tests.test_encode.test_create_struct_hash_runs_sha3_over_encode_data"></a>

#### test`_`create`_`struct`_`hash`_`runs`_`sha3`_`over`_`encode`_`data

```python
def test_create_struct_hash_runs_sha3_over_encode_data() -> None
```

Test that `create_struct_hash` is `sha3(encode_data(...))`.

<a id="packages.valory.contracts.gnosis_safe.tests.test_encode.test_encode_typed_data_assembles_eip712_digest"></a>

#### test`_`encode`_`typed`_`data`_`assembles`_`eip712`_`digest

```python
def test_encode_typed_data_assembles_eip712_digest() -> None
```

`encode_typed_data` returns ``sha3(0x19 01 || domainHash || messageHash)``.

