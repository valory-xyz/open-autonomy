<a id="autonomy.chain.subgraph.client"></a>

# autonomy.chain.subgraph.client

Subgraph client.

<a id="autonomy.chain.subgraph.client.ComponentType"></a>

## ComponentType Objects

```python
class ComponentType(Enum)
```

Component type.

<a id="autonomy.chain.subgraph.client.SubgraphClient"></a>

## SubgraphClient Objects

```python
class SubgraphClient()
```

Subgraph helper class.

<a id="autonomy.chain.subgraph.client.SubgraphClient.__init__"></a>

#### `__`init`__`

```python
def __init__(name: str = SUBGRAPH_NAME, url: str = SUBGRAPH_URL) -> None
```

Initialize object

<a id="autonomy.chain.subgraph.client.SubgraphClient.getRecordByPackageHash"></a>

#### getRecordByPackageHash

```python
def getRecordByPackageHash(package_hash: str) -> Dict[str, Any]
```

Get component by package hash

<a id="autonomy.chain.subgraph.client.SubgraphClient.getRecordByPackageId"></a>

#### getRecordByPackageId

```python
def getRecordByPackageId(package_id: PackageId) -> Dict[str, Any]
```

Get component by package hash

