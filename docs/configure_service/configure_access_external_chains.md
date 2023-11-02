The {{open_autonomy}} framework supports that agent services access different external chains
by defining certain configuration parameters appropriately.

For example, if you are developing a service to be run in Ethereum, you might first want to use
a development environment like [Hardhat](https://hardhat.org/) or [Ganache](https://trufflesuite.com/ganache/) as your testbed, then migrate to a public testnet like [Görli](https://goerli.net/), and ultimately run your service in the Ethereum main chain.

To use a service in a particular chain, you must ensure that the the relevant agent addresses are funded in that chain.



## What will you learn

In this guide, you will learn how to:

  * Configure an agent service to be run in a particular chain.
  * Configure the test classes appropriately.



## Configuring the agent service

To configure an agent service to work with a particular chain, you must configure the parameters `address` and `chain_id` accordingly in the connection `valory/ledger`. This configuration can be set up by overriding the `valory/ledger` configuration at agent level or at [service level](./service_configuration_file.md#service-level-overrides).



### Agent-level override

At agent level, the agent configuration file `aea-config.yaml` should contain an override for the parameters of the connection `valory/ledger`, either using hardcoded values or environment variables as follows:

=== "Using environment variables (recommended)"

    ```yaml title="aea-config.yaml"
    # (...)
    ---
    public_id: valory/ledger:0.19.0
    type: connection
    config:
      ledger_apis:
        ethereum:
          address: ${str:http://localhost:8545}
          chain_id: ${int:31337}
          <other_params>
    ```
=== "Using hardcoded values"

    ```yaml title="aea-config.yaml"
    # (...)
    ---
    public_id: valory/ledger:0.19.0
    type: connection
    config:
      ledger_apis:
        ethereum:
          address: http://host.docker.internal:8545
          chain_id: 31337
          <other_params>
    ```


Note that if you use agent-level hardcoded overrides, then service-level overrides will not work.
On the other hand agent-level environment variable overrides must follow the [export variable format](./service_configuration_file.md#export-to-environment-variables).


### Service-level override

Similarly, service-level overrides for the `valory/ledger` connection are defined in the service configuration file `service.yaml` using either approach:

=== "Using environment variables"
    ```yaml title="service.yaml"
    # (...)
    ---
    public_id: valory/ledger:0.19.0
    type: connection
    config:
      ledger_apis:
        ethereum:
          address: ${MY_CHAIN_ADDRESS:str:http://localhost:8545}
          chain_id: ${MY_CHAIN_ID:int:31337}
          <other_params>
    ```

=== "Using hardcoded values"

    ```yaml title="service.yaml"
    # (...)
    ---
    public_id: valory/ledger:0.19.0
    type: connection
    config:
      ledger_apis:
        ethereum:
          address: http://host.docker.internal:8545
          chain_id: 31337
          <other_params>
    ```

Observe that within the service configuration file there is no restriction for naming the environment variables.



## Configuring integration tests

The `open-aea-test-autonomy` test tools contain a collection of classes for `open-autonomy` packages
that allows you to configure the ledger connection for contract integration tests.
To use the test tools, you must include `open-aea-test-autonomy` as a dependency for your packages.

Tests that make calls to a chain inherit from the class
```
aea_test_autonomy.base_test_classes.contracts.BaseContractTest
```

The configuration of the ledger connection for tests is done through the
the `_setup_class(...)` method from `BaseContractTest`, which overrides the `valory/ledger` connection
configuration for tests. As above, you must set the parameters `address` and `chain_id` accordingly:
    ```python
    new_config = {
        "address": url,
        "chain_id": DEFAULT_CHAIN_ID,
        "denom": DEFAULT_CURRENCY_DENOM,
        "default_gas_price_strategy": "eip1559",
        "gas_price_strategies": {
            "gas_station": DEFAULT_GAS_STATION_STRATEGY,
            "eip1559": DEFAULT_EIP1559_STRATEGY,
        },
    }
    ```

Also, instead of inheriting directly from `BaseContractTest`, the test tools in `open-aea-test-autonomy` include several preconfigured helper base classes for common chains:

* `BaseGanacheContractTest`: Base test case for testing contracts on Ganache.
* `BaseHardhatGnosisContractTest`: Base test case for testing contracts on Hardhat with Gnosis.
* `BaseHardhatAMMContractTest`: Base test case for testing AMM contracts on Hardhat.
* `BaseGanacheContractWithDependencyTest`: Base test case for testing contracts with dependencies on Ganache.
* `BaseHardhatGnosisContractWithDependencyTest`: Base test case for testing contracts with dependencies on Hardhat with Gnosis.
* `BaseHardhatAMMContractWithDependencyTest`: Base test case for testing AMM contracts with dependencies on Hardhat.



## Configuring end-to-end tests

The `open-aea-test-autonomy` test tools also contain base classes for end-to-end tests. These tests inherit from the base classes
```
aea_test_autonomy.base_test_classes.agents.BaseTestEnd2End

aea_test_autonomy.base_test_classes.agents.BaseTestEnd2EndExecution
```
These classes define an `extra_configs` attribute that is used to set the agent-level overrides.
Tests that have this attribute set will override the corresponding agent configuration parameters.

!!! warning "Important"

    This does not only apply to the `valory/ledger` connection, but to any agent configuration.

???+ example

    All tests that inherit from the test class bellow will use the new configuration:

    ```python
    from aea_test_autonomy.base_test_classes.agents import BaseTestEnd2EndExecution
    
    class MyEndToEndTest(BaseTestEnd2EndExecution):
        """Base class for my end-to-end tests."""
    
        extra_configs = [
            {
                "dotted_path": "vendor.valory.skills.my_skill_abci.models.params.args.ipfs_domain_name",
                "value": "/dns/localhost/tcp/5001/http",
            }
        ]
    ```



## Configuring the validation timeout

Last but not least, it is important to keep in mind what the average block times are in the deploying network.
This is going to play a significant role when performing transactions, since the validation logic is based on that.

More specifically, the attribute `validate_timeout` in the skill configuration file `skill.yaml` 
should not be less than the average block time of the network, because timeouts  and unnecessary repricing
will happen too often. For reference, at the time this document was written, [the average block time
in the Ethereum mainnet](https://etherscan.io/chart/blocktime) was around 13.3 seconds. Therefore, it is not recommended that you specify a value less than that. Moreover, it
would be advisable to allow for some margin before stopping retrials, because actual block times might be higher than their average value,
and there is no guarantee that a transaction will be included into the next block.

The underlying retrial mechanism has a backoff that scales linearly, starting at `retry_timeout`, and stopping either when `retry_attempts` have been executed or `validate_timeout` has been reached.

???+ example
    An example configuration in the `skill.yaml` file for the Ethereum mainnet is as follows:
    
    ```yaml
    # (...)
    models:
      params:
        args:
          retry_attempts: 13
          retry_timeout: 13.3
          validate_timeout: 1205
    ```

    Therefore, unsuccessful transactions will be retried at the following times:

    * 1st retry: $13.3\cdot(1)=13.3$
    * 2nd retry: $13.3\cdot(1+2)=26.6$
    * ...
    * $i$th retry: $13.3\cdot\frac{i(i+1)}2$
    * ...
    * 12th retry: $13.3\cdot(1+2+\cdots+12)=1037.4$
    * 13th retry: $13.3\cdot(1+2+\cdots+12+13)=1210.3$
    
    Note, however, that it will stop at the 12th retry, because
    $1210.3 >$ `validate_timeout` $=1205$.

