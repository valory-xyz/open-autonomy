# Benchmarks

The benchmarking tools allow measuring the performance of an {{agent_service}} realised on the {{open_autonomy}} framework.

## How to use benchmarking tools

1. Setup agent runtime environment in dev mode using `autonomy deployment SERVICE_ID KEYS --dev`.

2. Run agents for `1` period and wait until the round where the skill is configured to call the `BenchmarkTool.save` method. (You can also run agents for `N` periods if you want more data).

3. Point the aggregation script to the directory containing the benchmark data. This will generate a `benchmarks.html` file containing benchmark stats in your current directory.

## Example usage

Run benchmarks for `oracle/price_estimation`:

```bash
make run-oracle
```
or
```bash
make run-oracle-dev
```

and, if you want to use local blockchain, in a separate tab run

```bash
make run-hardhat
```

By default this will create a `4` agent runtime where you can wait until all `4` agents are at the end of the first period (you can wait for more periods if you want) and then you can stop the runtime. The data will be stored in the `abci_build/persistent_data/benchmarks` folder. You can use the following script to aggregate this data:

```bash
autonomy analyse benchmarks abci_build/persistent_data/benchmarks
```

By default the script will generate output for all periods but you can specify which period to generate output for. Similarly, block types aggregation is configurable as well.
