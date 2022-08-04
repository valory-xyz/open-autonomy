<a id="autonomy.deploy.chain"></a>

# autonomy.deploy.chain

Utils to support on-chain contract interactions.

<a id="autonomy.deploy.chain.get_abi"></a>

#### get`_`abi

```python
def get_abi(url: str) -> Dict
```

Get ABI from provided URL

<a id="autonomy.deploy.chain.ServiceRegistry"></a>

## ServiceRegistry Objects

```python
class ServiceRegistry()
```

Class to represent on-chain service registry.

<a id="autonomy.deploy.chain.ServiceRegistry.resolve"></a>

#### resolve

```python
@classmethod
def resolve(cls, w3: web3.Web3, token_id: int) -> Dict
```

Resolve token ID.

<a id="autonomy.deploy.chain.resolve_token_id"></a>

#### resolve`_`token`_`id

```python
def resolve_token_id(token_id: int) -> Dict
```

Resolve token id using on-chain contracts.

