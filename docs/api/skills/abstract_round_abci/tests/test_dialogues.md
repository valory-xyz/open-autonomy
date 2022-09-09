<a id="packages.valory.skills.abstract_round_abci.tests.test_dialogues"></a>

# packages.valory.skills.abstract`_`round`_`abci.tests.test`_`dialogues

Test the dialogues.py module of the skill.

<a id="packages.valory.skills.abstract_round_abci.tests.test_dialogues.test_dialogues_creation"></a>

#### test`_`dialogues`_`creation

```python
@pytest.mark.parametrize(
    "dialogues_cls,expected_role_from_first_message",
    [
        (AbciDialogues, AbciDialogue.Role.CLIENT),
        (HttpDialogues, HttpDialogue.Role.CLIENT),
        (SigningDialogues, SigningDialogue.Role.SKILL),
        (LedgerApiDialogues, LedgerApiDialogue.Role.AGENT),
        (ContractApiDialogues, ContractApiDialogue.Role.AGENT),
    ],
)
def test_dialogues_creation(dialogues_cls: Type[Model], expected_role_from_first_message: Enum) -> None
```

Test XDialogues creations.

<a id="packages.valory.skills.abstract_round_abci.tests.test_dialogues.test_ledger_api_dialogue"></a>

#### test`_`ledger`_`api`_`dialogue

```python
def test_ledger_api_dialogue() -> None
```

Test 'LedgerApiDialogue' creation.

<a id="packages.valory.skills.abstract_round_abci.tests.test_dialogues.test_contract_api_dialogue"></a>

#### test`_`contract`_`api`_`dialogue

```python
def test_contract_api_dialogue() -> None
```

Test 'ContractApiDialogue' creation.

