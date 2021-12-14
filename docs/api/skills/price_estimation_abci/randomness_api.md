<a id="packages.valory.skills.price_estimation_abci.randomness_api"></a>

# packages.valory.skills.price`_`estimation`_`abci.randomness`_`api

This module contains the model to interact with crypto price API.

<a id="packages.valory.skills.price_estimation_abci.randomness_api.RandomnessApiSpecs"></a>

## RandomnessApiSpecs Objects

```python
class RandomnessApiSpecs(ABC)
```

Wrap an API library to access cryptocurrencies' prices.

<a id="packages.valory.skills.price_estimation_abci.randomness_api.RandomnessApiSpecs.__init__"></a>

#### `__`init`__`

```python
def __init__() -> None
```

Initialize the API wrapper.

<a id="packages.valory.skills.price_estimation_abci.randomness_api.RandomnessApiSpecs.get_spec"></a>

#### get`_`spec

```python
def get_spec() -> Dict
```

Return API Specs for `coinmarket`

<a id="packages.valory.skills.price_estimation_abci.randomness_api.RandomnessApiSpecs.process_response"></a>

#### post`_`request`_`process

```python
def process_response(response: HttpMessage) -> Optional[float]
```

Process the response and return observed price.

<a id="packages.valory.skills.price_estimation_abci.randomness_api.CloudflareApiSpecs"></a>

## CloudflareApiSpecs Objects

```python
class CloudflareApiSpecs(RandomnessApiSpecs)
```

Contains specs for CoinMarketCap's APIs.

<a id="packages.valory.skills.price_estimation_abci.randomness_api.ProtocolLabsOneApiSpecs"></a>

## ProtocolLabsOneApiSpecs Objects

```python
class ProtocolLabsOneApiSpecs(
    RandomnessApiSpecs)
```

Contains specs for CoinMarketCap's APIs.

<a id="packages.valory.skills.price_estimation_abci.randomness_api.ProtocolLabsTwoApiSpecs"></a>

## ProtocolLabsTwoApiSpecs Objects

```python
class ProtocolLabsTwoApiSpecs(
    RandomnessApiSpecs)
```

Contains specs for CoinMarketCap's APIs.

<a id="packages.valory.skills.price_estimation_abci.randomness_api.ProtocolLabsThreeApiSpecs"></a>

## ProtocolLabsThreeApiSpecs Objects

```python
class ProtocolLabsThreeApiSpecs(
    RandomnessApiSpecs)
```

Contains specs for CoinMarketCap's APIs.

<a id="packages.valory.skills.price_estimation_abci.randomness_api.RandomnessApi"></a>

## RandomnessApi Objects

```python
class RandomnessApi(Model)
```

A model that wraps APIs to get cryptocurrency prices.

<a id="packages.valory.skills.price_estimation_abci.randomness_api.RandomnessApi.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any) -> None
```

Initialize the price API model.

<a id="packages.valory.skills.price_estimation_abci.randomness_api.RandomnessApi.api_id"></a>

#### api`_`id

```python
@property
def api_id() -> str
```

Get API id.

<a id="packages.valory.skills.price_estimation_abci.randomness_api.RandomnessApi.increment_retries"></a>

#### increment`_`retries

```python
def increment_retries() -> None
```

Increment the retries counter.

<a id="packages.valory.skills.price_estimation_abci.randomness_api.RandomnessApi.is_retries_exceeded"></a>

#### is`_`retries`_`exceeded

```python
def is_retries_exceeded() -> bool
```

Check if the retries amount has been exceeded.

<a id="packages.valory.skills.price_estimation_abci.randomness_api.RandomnessApi.get_spec"></a>

#### get`_`spec

```python
def get_spec() -> Dict
```

Get the spec of the API

<a id="packages.valory.skills.price_estimation_abci.randomness_api.RandomnessApi.process_response"></a>

#### post`_`request`_`process

```python
def process_response(response: HttpMessage) -> Optional[float]
```

Process the response and return observed price.

