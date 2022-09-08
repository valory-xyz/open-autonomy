<a id="packages.valory.skills.abstract_abci.tests.test_dialogues"></a>

# packages.valory.skills.abstract`_`abci.tests.test`_`dialogues

Test the dialogues.py module of the skill.

<a id="packages.valory.skills.abstract_abci.tests.test_dialogues.test_dialogues_creation"></a>

#### test`_`dialogues`_`creation

```python
@pytest.mark.parametrize(
    "dialogues_cls,expected_role_from_first_message",
    [
        (AbciDialogues, AbciDialogue.Role.CLIENT),
    ],
)
def test_dialogues_creation(dialogues_cls: Type[AbciDialogues], expected_role_from_first_message: Enum) -> None
```

Test XDialogues creations.

