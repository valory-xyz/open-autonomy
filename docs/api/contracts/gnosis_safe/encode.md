<a id="packages.valory.contracts.gnosis_safe.encode"></a>

# packages.valory.contracts.gnosis`_`safe.encode

ETH encoder.

<a id="packages.valory.contracts.gnosis_safe.encode.encode"></a>

#### encode

```python
def encode(typ: t.Any, arg: t.Any) -> bytes
```

Encode by type.

<a id="packages.valory.contracts.gnosis_safe.encode.to_string"></a>

#### to`_`string

```python
def to_string(value: t.Union[bytes, str, int]) -> bytes
```

Convert to byte string.

<a id="packages.valory.contracts.gnosis_safe.encode.sha3_256"></a>

#### sha3`_`256

```python
def sha3_256(x: bytes) -> bytes
```

Calculate SHA3-256 hash.

<a id="packages.valory.contracts.gnosis_safe.encode.sha3"></a>

#### sha3

```python
def sha3(seed: t.Union[bytes, str, int]) -> bytes
```

Calculate SHA3-256 hash.

<a id="packages.valory.contracts.gnosis_safe.encode.scan_bin"></a>

#### scan`_`bin

```python
def scan_bin(v: str) -> bytes
```

Scan bytes.

<a id="packages.valory.contracts.gnosis_safe.encode.create_struct_definition"></a>

#### create`_`struct`_`definition

```python
def create_struct_definition(name: str, schema: t.List[t.Dict[str,
                                                              str]]) -> str
```

Create method struction defintion.

<a id="packages.valory.contracts.gnosis_safe.encode.find_dependencies"></a>

#### find`_`dependencies

```python
def find_dependencies(name: str, types: t.Dict[str, t.Any],
                      dependencies: t.Set) -> None
```

Find dependencies.

<a id="packages.valory.contracts.gnosis_safe.encode.create_schema"></a>

#### create`_`schema

```python
def create_schema(name: str, types: t.Dict) -> str
```

Create schema.

<a id="packages.valory.contracts.gnosis_safe.encode.create_schema_hash"></a>

#### create`_`schema`_`hash

```python
def create_schema_hash(name: str, types: t.Dict) -> bytes
```

Create schema hash.

<a id="packages.valory.contracts.gnosis_safe.encode.encode_value"></a>

#### encode`_`value

```python
def encode_value(data_type: str, value: t.Any, types: t.Dict) -> bytes
```

Encode value.

<a id="packages.valory.contracts.gnosis_safe.encode.encode_data"></a>

#### encode`_`data

```python
def encode_data(name: str, data: t.Dict[str, t.Dict[str, str]],
                types: t.Dict) -> bytes
```

Encode data.

<a id="packages.valory.contracts.gnosis_safe.encode.create_struct_hash"></a>

#### create`_`struct`_`hash

```python
def create_struct_hash(name: str, data: t.Dict[str, t.Dict[str, str]],
                       types: t.Dict) -> bytes
```

Create struct hash.

<a id="packages.valory.contracts.gnosis_safe.encode.encode_typed_data"></a>

#### encode`_`typed`_`data

```python
def encode_typed_data(data: t.Dict[str, t.Any]) -> bytes
```

Encode typed data.

