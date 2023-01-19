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

Raise when token ID retrieving fails for minted component.

<a id="autonomy.chain.exceptions.FailedToRetrieveComponentMetadata"></a>

## FailedToRetrieveComponentMetadata Objects

```python
class FailedToRetrieveComponentMetadata(ChainInteractionError)
```

Raise when component metadata retrieving fails.

<a id="autonomy.chain.exceptions.DependencyError"></a>

## DependencyError Objects

```python
class DependencyError(ChainInteractionError)
```

Raise when component dependency check fails.

<a id="autonomy.chain.exceptions.InvalidMintParameter"></a>

## InvalidMintParameter Objects

```python
class InvalidMintParameter(ChainInteractionError)
```

Raise when the parameter provided for minting a component is invalid

<a id="autonomy.chain.exceptions.ServiceRegistrationFailed"></a>

## ServiceRegistrationFailed Objects

```python
class ServiceRegistrationFailed(ChainInteractionError)
```

Raise when service activation fails.

<a id="autonomy.chain.exceptions.InstanceRegistrationFailed"></a>

## InstanceRegistrationFailed Objects

```python
class InstanceRegistrationFailed(ChainInteractionError)
```

Raise when instance registration fails.

<a id="autonomy.chain.exceptions.ServiceDeployFailed"></a>

## ServiceDeployFailed Objects

```python
class ServiceDeployFailed(ChainInteractionError)
```

Raise when service activation fails.

