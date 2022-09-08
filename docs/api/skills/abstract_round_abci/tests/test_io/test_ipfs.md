<a id="packages.valory.skills.abstract_round_abci.tests.test_io.test_ipfs"></a>

# packages.valory.skills.abstract`_`round`_`abci.tests.test`_`io.test`_`ipfs

This module contains tests for the `IPFS` interactions.

<a id="packages.valory.skills.abstract_round_abci.tests.test_io.test_ipfs.ipfs_daemon"></a>

#### ipfs`_`daemon

```python
@pytest.fixture(scope="module")
def ipfs_daemon() -> Iterator[bool]
```

Starts an IPFS daemon for the tests.

<a id="packages.valory.skills.abstract_round_abci.tests.test_io.test_ipfs.TestIPFSInteract"></a>

## TestIPFSInteract Objects

```python
@use_ipfs_daemon
class TestIPFSInteract()
```

Test `IPFSInteract`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_io.test_ipfs.TestIPFSInteract.setup"></a>

#### setup

```python
def setup() -> None
```

Setup test class.

<a id="packages.valory.skills.abstract_round_abci.tests.test_io.test_ipfs.TestIPFSInteract.test_store_and_send_and_back"></a>

#### test`_`store`_`and`_`send`_`and`_`back

```python
@pytest.mark.parametrize("multiple", (True, False))
def test_store_and_send_and_back(multiple: bool, tmp_path: PosixPath, dummy_obj: StoredJSONType, dummy_multiple_obj: Dict[str, StoredJSONType]) -> None
```

Test store -> send -> download -> read of objects.

