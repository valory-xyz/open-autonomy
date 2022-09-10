<a id="packages.valory.connections.abci.tests.test_fuzz.test_fuzz"></a>

# packages.valory.connections.abci.tests.test`_`fuzz.test`_`fuzz

Fuzzy tests for valory/abci connection

<a id="packages.valory.connections.abci.tests.test_fuzz.test_fuzz.GrpcFuzzyTests"></a>

## GrpcFuzzyTests Objects

```python
@pytest.mark.skip(reason="broken & takes too long time to complete on CI")
class GrpcFuzzyTests(BaseFuzzyTests,  TestCase)
```

Test the connection when gRPC is used

<a id="packages.valory.connections.abci.tests.test_fuzz.test_fuzz.TcpFuzzyTests"></a>

## TcpFuzzyTests Objects

```python
@pytest.mark.skip(reason="broken & takes too long time to complete on CI")
class TcpFuzzyTests(BaseFuzzyTests,  TestCase)
```

Test the connection when TCP is used

