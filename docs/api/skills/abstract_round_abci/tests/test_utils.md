<a id="packages.valory.skills.abstract_round_abci.tests.test_utils"></a>

# packages.valory.skills.abstract`_`round`_`abci.tests.test`_`utils

Test the utils.py module of the skill.

<a id="packages.valory.skills.abstract_round_abci.tests.test_utils.TestVerifyDrand"></a>

## TestVerifyDrand Objects

```python
class TestVerifyDrand()
```

Test DrandVerify.

<a id="packages.valory.skills.abstract_round_abci.tests.test_utils.TestVerifyDrand.setup"></a>

#### setup

```python
def setup() -> None
```

Setup test.

<a id="packages.valory.skills.abstract_round_abci.tests.test_utils.TestVerifyDrand.test_verify"></a>

#### test`_`verify

```python
def test_verify() -> None
```

Test verify method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_utils.TestVerifyDrand.test_verify_fails"></a>

#### test`_`verify`_`fails

```python
def test_verify_fails() -> None
```

Test verify method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_utils.TestVerifyDrand.test_negative_and_overflow"></a>

#### test`_`negative`_`and`_`overflow

```python
@pytest.mark.parametrize("value", (-1, MAX_UINT64 + 1))
def test_negative_and_overflow(value: int) -> None
```

Test verify method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_utils.test_fuzz_verify_drand"></a>

#### test`_`fuzz`_`verify`_`drand

```python
@pytest.mark.skip
def test_fuzz_verify_drand() -> None
```

Fuzz test for VerifyDrand. Run directly as a function, not through pytest

<a id="packages.valory.skills.abstract_round_abci.tests.test_utils.test_to_int_positive"></a>

#### test`_`to`_`int`_`positive

```python
def test_to_int_positive() -> None
```

Test `to_int` function.

<a id="packages.valory.skills.abstract_round_abci.tests.test_utils.test_fuzz_to_int"></a>

#### test`_`fuzz`_`to`_`int

```python
@pytest.mark.skip
def test_fuzz_to_int() -> None
```

Test fuzz to_int.

