<a id="packages.valory.connections.abci.tests.test_abci_spec"></a>

# packages.valory.connections.abci.tests.test`_`abci`_`spec

Tests to ensure implementation is on par with ABCI spec

<a id="packages.valory.connections.abci.tests.test_abci_spec.test_local_types_file_matches_github"></a>

#### test`_`local`_`types`_`file`_`matches`_`github

```python
def test_local_types_file_matches_github(request_attempts: int = 3) -> None
```

Test local file containing ABCI spec matches Tendermint GitHub

<a id="packages.valory.connections.abci.tests.test_abci_spec.test_all_custom_types_used"></a>

#### test`_`all`_`custom`_`types`_`used

```python
def test_all_custom_types_used() -> None
```

Test if all custom types are used in speech acts.

By asserting their usage in the speech acts we can delegate
the verification of their implementation and translation to
another test that addresses this (test_aea_to_tendermint).

<a id="packages.valory.connections.abci.tests.test_abci_spec.test_defined_dialogues_match_abci_spec"></a>

#### test`_`defined`_`dialogues`_`match`_`abci`_`spec

```python
def test_defined_dialogues_match_abci_spec() -> None
```

Test defined dialogues match ABCI spec.

It verifies solely that request response pairs match:
  - AEA requests match Tendermint requests
  - AEA responses match Tendermint responses
  - That all requests have a matching response
  - That all request, response and the exception are covered

<a id="packages.valory.connections.abci.tests.test_abci_spec.test_aea_to_tendermint"></a>

#### test`_`aea`_`to`_`tendermint

```python
def test_aea_to_tendermint() -> None
```

Test translation from AEA-native to Tendermint-native ABCI protocol.

"repeated" fields are returned as list in python,
but must be passed as tuples to Tendermint protobuf.

<a id="packages.valory.connections.abci.tests.test_abci_spec.test_tendermint_decoding"></a>

#### test`_`tendermint`_`decoding

```python
def test_tendermint_decoding() -> None
```

Test Tendermint ABCI message decoding

