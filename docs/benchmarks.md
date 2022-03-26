# Benchmarks

## How to use benchmarking tools

1. Setup agent runtime environment using deployment configs given in `deployments/`
2. Run agents for 1 period and wait till the round where you called `BenchmarkTool.save` method. (You can also run agents for N periods if you want more data).
3. Point aggregation script to the directory containing benchmark data, this will generate a `benchmarks.html` file containing benchmark stats in your current directory.

## For example

Run benchmarks for oracle/price_esimation skill

```
make run-oracle 
```
or
```
make run-oracle-dev
```

and if you want to use local blockchain setup in a separate tab run

```bash
make run-hardhat
```

By default this will create a 4 agent runtime where you can wait until all 4 agents
are at the end of the first period (you can wait for more periods if you want) and
then you can stop the runtime. The data will be stored in deployments/build/logs
folder. You can use this script to aggregate this data.

```bash
python script/aggregate_benchmark_results.py -p deployments/build/logs
```

By default script will generate output for all periods but you can specify which
period to generate output for, same goes for block types as well.