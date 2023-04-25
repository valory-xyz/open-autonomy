<a id="autonomy.chain.subgraph.client"></a>

# autonomy.chain.subgraph.client

Subgraph client.

<a id="autonomy.chain.subgraph.client.ComponentTypes"></a>

## ComponentTypes Objects

```python
class ComponentTypes()
```

Component types.

<a id="autonomy.chain.subgraph.client.SubgraphClient"></a>

## SubgraphClient Objects

```python
class SubgraphClient()
```

Subgraph helper class.

<a id="autonomy.chain.subgraph.client.SubgraphClient.__init__"></a>

#### `__`init`__`

```python
def __init__(name: str = SUBGRAPH_NAME, url: str = SUBGRAPH_LOCAL) -> None
```

Initialize object

<a id="autonomy.chain.subgraph.client.SubgraphClient.getRecordByPackageHash"></a>

#### getRecordByPackageHash

```python
def getRecordByPackageHash(package_hash: str) -> Dict[str, Any]
```

Get component by package hash

<a id="autonomy.chain.subgraph.client.SubgraphClient.getRecordByPublicId"></a>

#### getRecordByPublicId

```python
def getRecordByPublicId(public_id: str) -> Dict[str, Any]
```

Get component by package hash

