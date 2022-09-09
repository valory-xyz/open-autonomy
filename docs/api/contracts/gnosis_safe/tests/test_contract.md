<a id="packages.valory.contracts.gnosis_safe.tests.test_contract"></a>

# packages.valory.contracts.gnosis`_`safe.tests.test`_`contract

Tests for valory/gnosis contract.

<a id="packages.valory.contracts.gnosis_safe.tests.test_contract.BaseContractTest"></a>

## BaseContractTest Objects

```python
class BaseContractTest(BaseGanacheContractTest)
```

Base test case for GnosisSafeContract

<a id="packages.valory.contracts.gnosis_safe.tests.test_contract.BaseContractTest.setup_class"></a>

#### setup`_`class

```python
@classmethod
def setup_class(cls) -> None
```

Setup test.

<a id="packages.valory.contracts.gnosis_safe.tests.test_contract.BaseContractTest.deployment_kwargs"></a>

#### deployment`_`kwargs

```python
@classmethod
def deployment_kwargs(cls) -> Dict[str, Any]
```

Get deployment kwargs.

<a id="packages.valory.contracts.gnosis_safe.tests.test_contract.BaseContractTest.owners"></a>

#### owners

```python
@classmethod
def owners(cls) -> List[str]
```

Get the owners.

<a id="packages.valory.contracts.gnosis_safe.tests.test_contract.BaseContractTest.deployer"></a>

#### deployer

```python
@classmethod
def deployer(cls) -> Tuple[str, str]
```

Get the key pair of the deployer.

<a id="packages.valory.contracts.gnosis_safe.tests.test_contract.BaseContractTest.threshold"></a>

#### threshold

```python
@classmethod
def threshold(cls) -> int
```

Returns the amount of threshold.

<a id="packages.valory.contracts.gnosis_safe.tests.test_contract.BaseContractTest.get_nonce"></a>

#### get`_`nonce

```python
@classmethod
def get_nonce(cls) -> int
```

Get the nonce.

<a id="packages.valory.contracts.gnosis_safe.tests.test_contract.BaseContractTestHardHatSafeNet"></a>

## BaseContractTestHardHatSafeNet Objects

```python
class BaseContractTestHardHatSafeNet(BaseHardhatGnosisContractTest)
```

Base test case for GnosisSafeContract

<a id="packages.valory.contracts.gnosis_safe.tests.test_contract.BaseContractTestHardHatSafeNet.setup_class"></a>

#### setup`_`class

```python
@classmethod
def setup_class(cls) -> None
```

Setup test.

<a id="packages.valory.contracts.gnosis_safe.tests.test_contract.BaseContractTestHardHatSafeNet.deployment_kwargs"></a>

#### deployment`_`kwargs

```python
@classmethod
def deployment_kwargs(cls) -> Dict[str, Any]
```

Get deployment kwargs.

<a id="packages.valory.contracts.gnosis_safe.tests.test_contract.BaseContractTestHardHatSafeNet.owners"></a>

#### owners

```python
@classmethod
def owners(cls) -> List[str]
```

Get the owners.

<a id="packages.valory.contracts.gnosis_safe.tests.test_contract.BaseContractTestHardHatSafeNet.deployer"></a>

#### deployer

```python
@classmethod
def deployer(cls) -> Tuple[str, str]
```

Get the key pair of the deployer.

<a id="packages.valory.contracts.gnosis_safe.tests.test_contract.BaseContractTestHardHatSafeNet.threshold"></a>

#### threshold

```python
@classmethod
def threshold(cls) -> int
```

Returns the amount of threshold.

<a id="packages.valory.contracts.gnosis_safe.tests.test_contract.BaseContractTestHardHatSafeNet.get_nonce"></a>

#### get`_`nonce

```python
@classmethod
def get_nonce(cls) -> int
```

Get the nonce.

<a id="packages.valory.contracts.gnosis_safe.tests.test_contract.TestDeployTransactionHardhat"></a>

## TestDeployTransactionHardhat Objects

```python
@skip_docker_tests
class TestDeployTransactionHardhat(BaseContractTestHardHatSafeNet)
```

Test.

<a id="packages.valory.contracts.gnosis_safe.tests.test_contract.TestDeployTransactionHardhat.test_deployed"></a>

#### test`_`deployed

```python
def test_deployed() -> None
```

Run tests.

<a id="packages.valory.contracts.gnosis_safe.tests.test_contract.TestDeployTransactionHardhat.test_exceptions"></a>

#### test`_`exceptions

```python
def test_exceptions() -> None
```

Test exceptions.

<a id="packages.valory.contracts.gnosis_safe.tests.test_contract.TestDeployTransactionHardhat.test_non_implemented_methods"></a>

#### test`_`non`_`implemented`_`methods

```python
def test_non_implemented_methods() -> None
```

Test not implemented methods.

<a id="packages.valory.contracts.gnosis_safe.tests.test_contract.TestDeployTransactionHardhat.test_verify"></a>

#### test`_`verify

```python
def test_verify() -> None
```

Run verify test.

<a id="packages.valory.contracts.gnosis_safe.tests.test_contract.TestDeployTransactionHardhat.test_get_safe_nonce"></a>

#### test`_`get`_`safe`_`nonce

```python
def test_get_safe_nonce() -> None
```

Run get_safe_nonce test.

<a id="packages.valory.contracts.gnosis_safe.tests.test_contract.TestDeployTransactionHardhat.test_revert_reason"></a>

#### test`_`revert`_`reason

```python
def test_revert_reason() -> None
```

Test `revert_reason` method.

<a id="packages.valory.contracts.gnosis_safe.tests.test_contract.TestDeployTransactionHardhat.test_get_incoming_transfers"></a>

#### test`_`get`_`incoming`_`transfers

```python
def test_get_incoming_transfers() -> None
```

Run get_incoming txs.

<a id="packages.valory.contracts.gnosis_safe.tests.test_contract.TestRawSafeTransaction"></a>

## TestRawSafeTransaction Objects

```python
@skip_docker_tests
class TestRawSafeTransaction(BaseContractTestHardHatSafeNet)
```

Test `get_raw_safe_transaction`

<a id="packages.valory.contracts.gnosis_safe.tests.test_contract.TestRawSafeTransaction.test_run"></a>

#### test`_`run

```python
def test_run() -> None
```

Run tests.

<a id="packages.valory.contracts.gnosis_safe.tests.test_contract.TestRawSafeTransaction.test_verify_negative"></a>

#### test`_`verify`_`negative

```python
def test_verify_negative() -> None
```

Test verify negative.

<a id="packages.valory.contracts.gnosis_safe.tests.test_contract.TestRawSafeTransaction.test_verify_reverted"></a>

#### test`_`verify`_`reverted

```python
@mock.patch.object(
        Eth,
        "get_transaction",
        return_value=AttributeDict(
            {
                "accessList": [],
                "blockHash": HexBytes(
                    "0x8543592f08d1d9e6d722ba9d600270d7e7789ecc9b66f27ca81b104df9c5dd4a"
                ),
                "blockNumber": 31190129,
                "chainId": "0x89",
                "from": "0x5eF6567079c6c26d8ebf61AC0716163367E9B3cf",
                "gas": 270000,
                "gasPrice": 36215860217,
                "hash": HexBytes(
                    "0x09d5be525caea564b2d4fd31af424c8f0414a9b270937a1bee29167a883e6ce5"
                ),
                "input": "0x6a7612020000000000000000000000003d9e92b0fe7673dda3d7c33b9ff302768a03de190000000000000000000"
                "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
                "000000000000014000000000000000000000000000000000000000000000000000000000000000000000000000000"
                "00000000000000000000000000000000000000000000001d4c0000000000000000000000000000000000000000000"
                "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
                "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
                "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002000"
                "0000000000000000000000000000000000000000000000000000000000000846b0bac970000000000000000000000"
                "000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000"
                "000000000004000000000000000000000000000000000000000000000000000000000001df5000000000000000000"
                "00000000000000000000000000000487da3583c85e1e0000000000000000000000000000000000000000000000000"
                "000000000000000000000000000000000000000000000000000000000000000000000000104c292f99a14d354c669"
                "3f9037a4a3d09c85c8ad5f1ab4de79bbc8bab845560f797f385ecbe77e90245b7b45e218a2c56fec17c9d38729264"
                "83d0ed800df46daa71c3afaa87b5959d644cd0d311a93acb398ec4f9d4c545c54ea6f4adbaa3e99dd9668f948eb64"
                "10f1b2105e2f6ca762badf17539d9221cef7af55a244c6ae3c6b401cfd01fe829d711a372b9d8ad5b91e0956a4da1"
                "6929d04a2581b10f9f4599899b625c367bef18656c90efcf9d9ee5063860774f08517488b05ef5090acd31aa9d91b"
                "7df8080d69fdddfe9b326f3ae0cb95227e21d2d265b6a83861998dd9e91fb980415e78c2bb0b10dbe3b4d7bead977"
                "2f32fa26b738c5670aa69ee9d09973ea2b81c00000000000000000000000000000000000000000000000000000000",
                "maxFeePerGas": 36215860217,
                "maxPriorityFeePerGas": 36215860202,
                "nonce": 2231,
                "r": HexBytes(
                    "0x5d5d369d5fc30c5604d974761d41b08118120eb94fd65a827bab1f6ea558d67c"
                ),
                "s": HexBytes(
                    "0x12f68826bd41989335e62d43fd36547fe171ad536b99bc93766622438d3f8355"
                ),
                "to": "0x37ba5291A5bE8cbE44717a0673fe2c5a45B4B6A8",
                "transactionIndex": 28,
                "type": "0x2",
                "v": 1,
                "value": 0,
            }
        ),
    )
@mock.patch.object(
        EthereumApi,
        "get_transaction_receipt",
        return_value={
            "blockHash": "0x8543592f08d1d9e6d722ba9d600270d7e7789ecc9b66f27ca81b104df9c5dd4a",
            "blockNumber": 31190129,
            "contractAddress": None,
            "cumulativeGasUsed": 5167853,
            "effectiveGasPrice": 36215860217,
            "from": "0x5eF6567079c6c26d8ebf61AC0716163367E9B3cf",
            "gasUsed": 48921,
            "logs": [
                {
                    "address": "0x0000000000000000000000000000000000001010",
                    "blockHash": "0x8543592f08d1d9e6d722ba9d600270d7e7789ecc9b66f27ca81b104df9c5dd4a",
                    "blockNumber": 31190129,
                    "data": "0x00000000000000000000000000000000000000000000000000064b5dcc9920c1000000000000000000000000"
                    "00000000000000000000000032116d529b00f7490000000000000000000000000000000000000000000004353d"
                    "1a5e0a73394e1e000000000000000000000000000000000000000000000000320b21f4ce67d688000000000000"
                    "0000000000000000000000000000000004353d20a9683fd26edf",
                    "logIndex": 115,
                    "removed": False,
                    "topics": [
                        "0x4dfe1bbbcf077ddc3e01291eea2d5c70c2b422b415d95645b9adcfd678cb1d63",
                        "0x0000000000000000000000000000000000000000000000000000000000001010",
                        "0x0000000000000000000000005ef6567079c6c26d8ebf61ac0716163367e9b3cf",
                        "0x000000000000000000000000f0245f6251bef9447a08766b9da2b07b28ad80b0",
                    ],
                    "transactionHash": "0x09d5be525caea564b2d4fd31af424c8f0414a9b270937a1bee29167a883e6ce5",
                    "transactionIndex": 28,
                }
            ],
            "logsBloom": "0x0000000000000000000000000000000000000000000000000000000000000000000000000000800000000000000"
            "000000000800000000000000000000000000000008000000000000000000000000080000000000000000000010000"
            "000000000000000000000000000000000000000000000000000000008000000000000000000000008000000000000"
            "000000000000000000000000000000000000088000020000000000000000000000000000000000000000000000000"
            "000000000000400000000000000000000100000000000000000000000000000010000000000000000000000000000"
            "0000000800000000000000000000000000000000000100000",
            "status": 0,
            "to": "0x37ba5291A5bE8cbE44717a0673fe2c5a45B4B6A8",
            "transactionHash": "0x09d5be525caea564b2d4fd31af424c8f0414a9b270937a1bee29167a883e6ce5",
            "transactionIndex": 28,
            "type": "0x2",
            "revert_reason": "execution reverted: GS026",
        },
    )
def test_verify_reverted(*_: Any) -> None
```

Test verify for reverted tx.

