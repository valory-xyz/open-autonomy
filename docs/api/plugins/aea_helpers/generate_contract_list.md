<a id="plugins.aea-helpers.aea_helpers.generate_contract_list"></a>

# plugins.aea-helpers.aea`_`helpers.generate`_`contract`_`list

Script to generate a markdown contract addresses table.

<a id="plugins.aea-helpers.aea_helpers.generate_contract_list.to_title"></a>

#### to`_`title

```python
def to_title(string: str) -> str
```

Convert camelCase to Title Case with spaces.

<a id="plugins.aea-helpers.aea_helpers.generate_contract_list.main"></a>

#### main

```python
def main() -> None
```

Generate contract addresses list.

<a id="plugins.aea-helpers.aea_helpers.generate_contract_list.generate_contract_list"></a>

#### generate`_`contract`_`list

```python
@click.command(name="generate-contract-list")
def generate_contract_list() -> None
```

Generate the on-chain contract addresses markdown file.

