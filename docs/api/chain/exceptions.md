<a id="autonomy.chain.exceptions"></a>

# autonomy.chain.exceptions

Custom exceptions for chain module.

<a id="autonomy.chain.exceptions.ChainInteractionError"></a>

## ChainInteractionError Objects

```python
class ChainInteractionError(Exception)
```

Base chain interaction failure.

<a id="autonomy.chain.exceptions.ComponentMintFailed"></a>

## ComponentMintFailed Objects

```python
class ComponentMintFailed(ChainInteractionError)
```

Raise when component minting fails.

<a id="autonomy.chain.exceptions.FailedToRetrieveTokenId"></a>

## FailedToRetrieveTokenId Objects

```python
class FailedToRetrieveTokenId(ChainInteractionError)
```

Raise token ID retrieving fails for minted component.

