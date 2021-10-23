<a id="packages.valory.skills.price_estimation_abci.price_api"></a>

# packages.valory.skills.price`_`estimation`_`abci.price`_`api

This module contains the model to interact with crypto price API.

<a id="packages.valory.skills.price_estimation_abci.price_api.Currency"></a>

## Currency Objects

```python
class Currency(Enum)
```

Enumeration of currencies (slug).

<a id="packages.valory.skills.price_estimation_abci.price_api.Currency.slug"></a>

#### slug

```python
@property
def slug()
```

To slug.

<a id="packages.valory.skills.price_estimation_abci.price_api.ApiSpecs"></a>

## ApiSpecs Objects

```python
class ApiSpecs(ABC)
```

Wrap an API library to access cryptocurrencies' prices.

<a id="packages.valory.skills.price_estimation_abci.price_api.ApiSpecs.__init__"></a>

#### `__`init`__`

```python
def __init__(api_key: Optional[str] = None)
```

Initialize the API wrapper.

<a id="packages.valory.skills.price_estimation_abci.price_api.ApiSpecs.get_spec"></a>

#### get`_`spec

```python
@abstractmethod
def get_spec(currency_id: CurrencyOrStr, convert_id: CurrencyOrStr = Currency.USD) -> Dict
```

Return API Specs for `currency_id`

<a id="packages.valory.skills.price_estimation_abci.price_api.ApiSpecs.post_request_process"></a>

#### post`_`request`_`process

```python
@abstractmethod
def post_request_process(response: HttpMessage) -> Optional[float]
```

Process the response and return observed price.

<a id="packages.valory.skills.price_estimation_abci.price_api.CoinMarketCapApiSpecs"></a>

## CoinMarketCapApiSpecs Objects

```python
class CoinMarketCapApiSpecs(ApiSpecs)
```

Contains specs for CoinMarketCap's APIs.

<a id="packages.valory.skills.price_estimation_abci.price_api.CoinMarketCapApiSpecs.get_spec"></a>

#### get`_`spec

```python
def get_spec(currency_id: CurrencyOrStr, convert_id: CurrencyOrStr = Currency.USD) -> Dict
```

Return API Specs for `coinmarket`

<a id="packages.valory.skills.price_estimation_abci.price_api.CoinMarketCapApiSpecs.post_request_process"></a>

#### post`_`request`_`process

```python
def post_request_process(response: HttpMessage) -> Optional[float]
```

Process the response and return observed price.

<a id="packages.valory.skills.price_estimation_abci.price_api.CoinGeckoApiSpecs"></a>

## CoinGeckoApiSpecs Objects

```python
class CoinGeckoApiSpecs(ApiSpecs)
```

Contains specs for CoinGecko's APIs.

<a id="packages.valory.skills.price_estimation_abci.price_api.CoinGeckoApiSpecs.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any) -> None
```

Initialize the object.

<a id="packages.valory.skills.price_estimation_abci.price_api.CoinGeckoApiSpecs.get_spec"></a>

#### get`_`spec

```python
def get_spec(currency_id: CurrencyOrStr, convert_id: CurrencyOrStr = Currency.USD) -> Dict
```

Return API Specs for `coingecko`

<a id="packages.valory.skills.price_estimation_abci.price_api.CoinGeckoApiSpecs.post_request_process"></a>

#### post`_`request`_`process

```python
def post_request_process(response: HttpMessage) -> Optional[float]
```

Process the response and return observed price.

<a id="packages.valory.skills.price_estimation_abci.price_api.BinanceApiSpecs"></a>

## BinanceApiSpecs Objects

```python
class BinanceApiSpecs(ApiSpecs)
```

Contains specs for Binance's APIs.

<a id="packages.valory.skills.price_estimation_abci.price_api.BinanceApiSpecs.get_spec"></a>

#### get`_`spec

```python
def get_spec(currency_id: CurrencyOrStr, convert_id: CurrencyOrStr = Currency.USD) -> Dict
```

Return API Specs for `binance`

<a id="packages.valory.skills.price_estimation_abci.price_api.BinanceApiSpecs.post_request_process"></a>

#### post`_`request`_`process

```python
def post_request_process(response: HttpMessage) -> Optional[float]
```

Process the response and return observed price.

<a id="packages.valory.skills.price_estimation_abci.price_api.CoinbaseApiSpecs"></a>

## CoinbaseApiSpecs Objects

```python
class CoinbaseApiSpecs(ApiSpecs)
```

Contains specs for Coinbase's APIs.

<a id="packages.valory.skills.price_estimation_abci.price_api.CoinbaseApiSpecs.get_spec"></a>

#### get`_`spec

```python
def get_spec(currency_id: CurrencyOrStr, convert_id: CurrencyOrStr = Currency.USD) -> Dict
```

Return API Specs for `coinbase`

<a id="packages.valory.skills.price_estimation_abci.price_api.CoinbaseApiSpecs.post_request_process"></a>

#### post`_`request`_`process

```python
def post_request_process(response: HttpMessage) -> Optional[float]
```

Process the response and return observed price.

<a id="packages.valory.skills.price_estimation_abci.price_api.PriceApi"></a>

## PriceApi Objects

```python
class PriceApi(Model)
```

A model that wraps APIs to get cryptocurrency prices.

<a id="packages.valory.skills.price_estimation_abci.price_api.PriceApi.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any) -> None
```

Initialize the price API model.

<a id="packages.valory.skills.price_estimation_abci.price_api.PriceApi.api_id"></a>

#### api`_`id

```python
@property
def api_id() -> str
```

Get API id.

<a id="packages.valory.skills.price_estimation_abci.price_api.PriceApi.increment_retries"></a>

#### increment`_`retries

```python
def increment_retries() -> None
```

Increment the retries counter.

<a id="packages.valory.skills.price_estimation_abci.price_api.PriceApi.is_retries_exceeded"></a>

#### is`_`retries`_`exceeded

```python
def is_retries_exceeded() -> bool
```

Check if the retries amount has been exceeded.

<a id="packages.valory.skills.price_estimation_abci.price_api.PriceApi.get_spec"></a>

#### get`_`spec

```python
def get_spec(currency_id: CurrencyOrStr, convert_id: CurrencyOrStr = Currency.USD) -> Dict
```

Get the spec of the API

<a id="packages.valory.skills.price_estimation_abci.price_api.PriceApi.post_request_process"></a>

#### post`_`request`_`process

```python
def post_request_process(response: HttpMessage) -> Optional[float]
```

Process the response and return observed price.

