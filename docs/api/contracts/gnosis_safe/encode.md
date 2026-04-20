<a id="packages.valory.contracts.gnosis_safe.encode"></a>

# packages.valory.contracts.gnosis`_`safe.encode

ETH encoder.

<a id="packages.valory.contracts.gnosis_safe.encode.encode"></a>

#### encode

```python
def encode(ledger_api: EthereumApi, typ: t.Any, arg: t.Any) -> bytes
```

Encode a single value of the given ABI type.

web3 bundles ``eth_abi`` and exposes its default codec via
``ledger_api.api.codec``; reaching through to the codec's
``_registry`` gives us the same per-type encoder the contract
used to import directly from ``eth_abi.default_codec._registry``,
without adding ``eth-abi`` as a declared dep.

<a id="packages.valory.contracts.gnosis_safe.encode.to_string"></a>

#### to`_`string

```python
def to_string(value: t.Union[bytes, str, int]) -> bytes
```

Convert to byte string.

<a id="packages.valory.contracts.gnosis_safe.encode.sha3_256"></a>

#### sha3`_`256

```python
def sha3_256(ledger_api: EthereumApi, x: bytes) -> bytes
```

Calculate keccak-256 hash (Ethereum's SHA3 variant).

<a id="packages.valory.contracts.gnosis_safe.encode.sha3"></a>

#### sha3

```python
def sha3(ledger_api: EthereumApi, seed: t.Union[bytes, str, int]) -> bytes
```

Calculate keccak-256 hash over *seed* (coerced to bytes).

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

Create the struct definition string.

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
def create_schema_hash(ledger_api: EthereumApi, name: str,
                       types: t.Dict) -> bytes
```

Create schema hash.

<a id="packages.valory.contracts.gnosis_safe.encode.encode_value"></a>

#### encode`_`value

```python
def encode_value(ledger_api: EthereumApi, data_type: str, value: t.Any,
                 types: t.Dict) -> bytes
```

Encode value.

<a id="packages.valory.contracts.gnosis_safe.encode.encode_data"></a>

#### encode`_`data

```python
def encode_data(ledger_api: EthereumApi, name: str,
                data: t.Dict[str, t.Dict[str, str]], types: t.Dict) -> bytes
```

Encode data.

<a id="packages.valory.contracts.gnosis_safe.encode.create_struct_hash"></a>

#### create`_`struct`_`hash

```python
def create_struct_hash(ledger_api: EthereumApi, name: str,
                       data: t.Dict[str, t.Dict[str,
                                                str]], types: t.Dict) -> bytes
```

Create struct hash.

<a id="packages.valory.contracts.gnosis_safe.encode.encode_typed_data"></a>

#### encode`_`typed`_`data

```python
def encode_typed_data(ledger_api: EthereumApi, data: t.Dict[str,
                                                            t.Any]) -> bytes
```

Encode typed data.

