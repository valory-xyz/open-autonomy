<a id="autonomy.chain.config"></a>

# autonomy.chain.config

On-chain tools configurations.

<a id="autonomy.chain.config.LedgerType"></a>

## LedgerType Objects

```python
class LedgerType(str, Enum)
```

Ledger type enum.

<a id="autonomy.chain.config.LedgerType.config_file"></a>

#### config`_`file

```python
@property
def config_file() -> str
```

Config filename.

<a id="autonomy.chain.config.LedgerType.key_file"></a>

#### key`_`file

```python
@property
def key_file() -> str
```

Key filename.

<a id="autonomy.chain.config.LedgerType.from_id"></a>

#### from`_`id

```python
@classmethod
def from_id(cls, chain_id: int) -> "LedgerType"
```

Load from chain ID.

<a id="autonomy.chain.config.ChainType"></a>

## ChainType Objects

```python
class ChainType(Enum)
```

Chain types.

<a id="autonomy.chain.config.ChainType.id"></a>

#### id

```python
@property
def id() -> Optional[int]
```

Chain ID

<a id="autonomy.chain.config.ChainType.rpc"></a>

#### rpc

```python
@property
def rpc() -> Optional[str]
```

RPC String

<a id="autonomy.chain.config.ChainType.rpc_env_name"></a>

#### rpc`_`env`_`name

```python
@property
def rpc_env_name() -> str
```

RPC Environment variable name

<a id="autonomy.chain.config.ChainType.ledger_type"></a>

#### ledger`_`type

```python
@property
def ledger_type() -> LedgerType
```

Ledger type.

<a id="autonomy.chain.config.ChainType.from_string"></a>

#### from`_`string

```python
@classmethod
def from_string(cls, chain: str) -> "Chain"
```

Load from string.

<a id="autonomy.chain.config.ChainType.from_id"></a>

#### from`_`id

```python
@classmethod
def from_id(cls, chain_id: int) -> "Chain"
```

Load from chain ID.

<a id="autonomy.chain.config.ContractConfig"></a>

## ContractConfig Objects

```python
@dataclass
class ContractConfig()
```

Contract config class.

<a id="autonomy.chain.config.ChainConfig"></a>

## ChainConfig Objects

```python
@dataclass
class ChainConfig()
```

Chain config

<a id="autonomy.chain.config.ChainConfigs"></a>

## ChainConfigs Objects

```python
class ChainConfigs()
```

Name space for chain configs.

<a id="autonomy.chain.config.ChainConfigs.get"></a>

#### get

```python
@classmethod
def get(cls, chain_type: ChainType) -> ChainConfig
```

Return chain config for given chain type.

<a id="autonomy.chain.config.ChainConfigs.get_rpc_env_var"></a>

#### get`_`rpc`_`env`_`var

```python
@classmethod
def get_rpc_env_var(cls, chain_type: ChainType) -> Optional[str]
```

Return chain config for given chain type.

<a id="autonomy.chain.config.ContractConfigs"></a>

## ContractConfigs Objects

```python
class ContractConfigs()
```

A namespace for contract configs.

<a id="autonomy.chain.config.ContractConfigs.get"></a>

#### get

```python
@classmethod
def get(cls, name: str) -> ContractConfig
```

Return chain config for given chain type.

