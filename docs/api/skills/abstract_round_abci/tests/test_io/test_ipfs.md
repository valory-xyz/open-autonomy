<a id="packages.valory.skills.abstract_round_abci.tests.test_io.test_ipfs"></a>

# packages.valory.skills.abstract`_`round`_`abci.tests.test`_`io.test`_`ipfs

This module contains tests for the `IPFS` interactions.

<a id="packages.valory.skills.abstract_round_abci.tests.test_io.test_ipfs.TestIPFSInteract"></a>

## TestIPFSInteract Objects

```python
class TestIPFSInteract()
```

Test `IPFSInteract`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_io.test_ipfs.TestIPFSInteract.setup_method"></a>

#### setup`_`method

```python
def setup_method() -> None
```

Setup test class.

<a id="packages.valory.skills.abstract_round_abci.tests.test_io.test_ipfs.TestIPFSInteract.test_store_and_send_and_back"></a>

#### test`_`store`_`and`_`send`_`and`_`back

```python
@pytest.mark.parametrize("multiple", (True, False))
def test_store_and_send_and_back(multiple: bool, dummy_obj: StoredJSONType,
                                 dummy_multiple_obj: Dict[str, StoredJSONType],
                                 tmp_path: PosixPath) -> None
```

Test store -> send -> download -> read of objects.

<a id="packages.valory.skills.abstract_round_abci.tests.test_io.test_ipfs.TestIPFSInteract.test_store_fails"></a>

#### test`_`store`_`fails

```python
def test_store_fails(dummy_multiple_obj: Dict[str, StoredJSONType]) -> None
```

Tests when "store" fails.

<a id="packages.valory.skills.abstract_round_abci.tests.test_io.test_ipfs.TestIPFSInteract.test_load_fails"></a>

#### test`_`load`_`fails

```python
def test_load_fails(dummy_multiple_obj: Dict[str, StoredJSONType]) -> None
```

Tests when "load" fails.

