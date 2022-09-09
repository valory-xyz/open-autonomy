<a id="packages.valory.skills.price_estimation_abci.tests.test_tools"></a>

# packages.valory.skills.price`_`estimation`_`abci.tests.test`_`tools

Test the tools.py module of the skill.

<a id="packages.valory.skills.price_estimation_abci.tests.test_tools.test_random_selection_function"></a>

#### test`_`random`_`selection`_`function

```python
def test_random_selection_function() -> None
```

Test `random_selection` function.

<a id="packages.valory.skills.price_estimation_abci.tests.test_tools.test_random_selection_function_raises"></a>

#### test`_`random`_`selection`_`function`_`raises

```python
@pytest.mark.parametrize("value", (-1, 2))
def test_random_selection_function_raises(value: int) -> None
```

Test `random_selection` function.

<a id="packages.valory.skills.price_estimation_abci.tests.test_tools.test_fuzz_random_selection"></a>

#### test`_`fuzz`_`random`_`selection

```python
@pytest.mark.skip
def test_fuzz_random_selection() -> None
```

Test fuzz random_selection.

