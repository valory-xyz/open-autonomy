<a id="packages.valory.skills.abstract_round_abci.test_tools.abci_app"></a>

# packages.valory.skills.abstract`_`round`_`abci.test`_`tools.abci`_`app

ABCI App test tools.

<a id="packages.valory.skills.abstract_round_abci.test_tools.abci_app.ConcreteRoundA"></a>

## ConcreteRoundA Objects

```python
class ConcreteRoundA(AbstractRound)
```

Dummy instantiation of the AbstractRound class.

<a id="packages.valory.skills.abstract_round_abci.test_tools.abci_app.ConcreteRoundA.end_block"></a>

#### end`_`block

```python
def end_block() -> Tuple[MagicMock, MagicMock]
```

End block.

<a id="packages.valory.skills.abstract_round_abci.test_tools.abci_app.ConcreteRoundA.check_payload"></a>

#### check`_`payload

```python
def check_payload(payload: BaseTxPayload) -> None
```

Check payloads of type 'payload_a'.

<a id="packages.valory.skills.abstract_round_abci.test_tools.abci_app.ConcreteRoundA.process_payload"></a>

#### process`_`payload

```python
def process_payload(payload: BaseTxPayload) -> None
```

Process payloads of type 'payload_a'.

<a id="packages.valory.skills.abstract_round_abci.test_tools.abci_app.ConcreteRoundB"></a>

## ConcreteRoundB Objects

```python
class ConcreteRoundB(AbstractRound)
```

Dummy instantiation of the AbstractRound class.

<a id="packages.valory.skills.abstract_round_abci.test_tools.abci_app.ConcreteRoundB.end_block"></a>

#### end`_`block

```python
def end_block() -> None
```

End block.

<a id="packages.valory.skills.abstract_round_abci.test_tools.abci_app.ConcreteRoundB.check_payload"></a>

#### check`_`payload

```python
def check_payload(payload: BaseTxPayload) -> None
```

Check payloads of type 'payload_b'.

<a id="packages.valory.skills.abstract_round_abci.test_tools.abci_app.ConcreteRoundB.process_payload"></a>

#### process`_`payload

```python
def process_payload(payload: BaseTxPayload) -> None
```

Process payloads of type 'payload_b'.

<a id="packages.valory.skills.abstract_round_abci.test_tools.abci_app.ConcreteRoundC"></a>

## ConcreteRoundC Objects

```python
class ConcreteRoundC(AbstractRound)
```

Dummy instantiation of the AbstractRound class.

<a id="packages.valory.skills.abstract_round_abci.test_tools.abci_app.ConcreteRoundC.end_block"></a>

#### end`_`block

```python
def end_block() -> None
```

End block.

<a id="packages.valory.skills.abstract_round_abci.test_tools.abci_app.ConcreteRoundC.check_payload"></a>

#### check`_`payload

```python
def check_payload(payload: BaseTxPayload) -> None
```

Check payloads of type 'payload_c'.

<a id="packages.valory.skills.abstract_round_abci.test_tools.abci_app.ConcreteRoundC.process_payload"></a>

#### process`_`payload

```python
def process_payload(payload: BaseTxPayload) -> None
```

Process payloads of type 'payload_c'.

<a id="packages.valory.skills.abstract_round_abci.test_tools.abci_app.AbciAppTest"></a>

## AbciAppTest Objects

```python
class AbciAppTest(AbciApp[str])
```

A dummy AbciApp for testing purposes.

