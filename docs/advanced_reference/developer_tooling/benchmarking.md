The benchmarking tool allows measuring the performance of an agent service. The tool is accessed through the class

```python
packages.valory.skills.abstract_round_abci.models.BenchmarkTool
```

The benchmarking information is saved upon calling the method `BenchmarkTool.save()`. This function call is typically executed within the `async_act()` method of a behaviour. Therefore, the sequence of events that should occur so that the benchmarking information is saved correctly is as follows:

1. A behaviour executes the `BenchmarkTool.save()` method.
2. The agent service reaches the `reset_and_pause` round, and the Tendermint data is dumped.
3. Stop the service execution after, at least, steps 1. and 2. have occurred in that sequence.

The benchmarking data will be stored in the folder `<service_folder>/abci_build/persistent_data/benchmarks`.

## Use the benchmarking tool

1. **Run the service.** Build and run the agent service. You can build and run the service either in [normal mode](../../guides/deploy_service.md#local-deployment) or in [dev mode](./dev_mode.md#build-and-run-an-agent-service-in-dev-mode).

2. **Wait for service execution.** Wait until the service has completed, at least, one period before cancelling the execution. That is, wait until the `reset_and_pause` round has occurred at least once. This is required because the Tendermint server will only dump Tendermint data when it reaches that state. Once you have a data dump, you can stop the local execution by pressing `Ctrl-C`.

3. **Aggregate the benchmarking data.** The benchmarking data will be stored in the folder `<service_folder>/abci_build/persistent_data/benchmarks`. Aggregate the data for all periods executing:

    ```bash
    autonomy analyse benchmarks abci_build/persistent_data/benchmarks
    ```

    This will generate a `benchmarks.html` file containing benchmark stats in your current directory.
    By default the script will generate output for all periods but you can specify which period to generate output for. Similarly, block types aggregation is configurable as well. For example,

    ```bash
    autonomy analyse benchmarks abci_build/persistent_data/benchmarks --period 2 --block-type consensus
    ```

    will aggregate stats for `consensus` block type in the second period.
