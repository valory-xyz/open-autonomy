The {{open_autonomy}} framework provides a benchmark tool to assist with the process of measuring the performance of an agent service. The tool is designed to measure time spent within the execution of code blocks in the behaviours that compose an {{fsm_app}}. It differentiates between two kinds of code blocks:

* **Local code blocks**: used to measure the time taken in local computations, for example, preparation of payloads or computing a local function.
* **Consensus code blocks**: used to measure the time taken by the logic in the execution of the consensus algorithm by the agents.

## Set up the benchmark tool

The benchmark tool is encapsulated in the class

```python
packages.valory.skills.abstract_round_abci.models.BenchmarkTool
```

To set up the tool, you need to follow a couple of steps detailed below. Note that these steps are automatically done if you use the [{{fsm_app}} scaffold tool](../../guides/code_fsm_app_skill.md).

1. Import the class `BenchmarkTool` in the `models.py` of your skill, and extend it, if required.

    ```python
    from packages.valory.skills.abstract_round_abci.models import (
    BenchmarkTool as BaseBenchmarkTool)

    # (...)

    # Use the class as-is.
    MyBenchmarkTool = BaseBenchmarkTool

    # Or extend the class, if required.
    class MyBenchmarkTool(BaseBenchmarkTool):
        # (...)
    ```

2. Ensure that the skill configuration file `skill.yaml` points correctly to the skill benchmark tool in the section `models`.

    ```yaml title="skill.yaml"
    # (...)
    models:
        benchmark_tool:
            args:
            log_dir: /logs
            class_name: MyBenchmarkTool    
    ```

## Defining the code blocks to measure

Once the tool is set up, it can be accessed through the skill context. Usually, the measurement of the code blocks will be executed within the `async_act()` method of the concrete behaviours.

```python
class MyBehaviour(BaseBehaviour, ABC):
    
    # (...)

    def async_act(self) -> Generator:
        # The benchmark tool can be accessed here through `self.context.benchmark_tool`
```

The syntax used to delimit the scope of the different types of code blocks (local and consensus blocks) is achieved through a [Python `with` runtime context](https://docs.python.org/3/library/stdtypes.html#context-manager-types).

```python
class MyBehaviour(BaseBehaviour, ABC):

    # (...)

    def async_act(self) -> Generator:
           
        # (...)

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            # Code which will be accounted for "local" execution
            # (...)

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            # Code which will be accounted for "consensus" execution
            # It will typically consist of the following two statements:
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()
```

## Save the benchmark data

The benchmark data is saved upon calling the method `BenchmarkTool.save()`. This function call is executed at the end of every period by the `ResetAndPauseBehaviour` (within the `reset_pause_abci` {{fsm_app}} skill). Hence, the `reset_pause_abci` {{fsm_app}} must be chained appropriately in the composed FSM, marking the end of a period in the business logic of the service.

As a summary, the sequence of events that should occur so that the benchmark information is saved correctly is as follows:

1. The overall {{fsm_app}} is composed with the `reset_pause_abci` {{fsm_app}}.
2. Any intermediate behaviour executes local and/or consensus blocks contexts within their `async_act()` method.
3. The {{fsm_app}} reaches the `ResetAndPauseRound` (`reset_pause_abci` round and calls the `BenchmarkTool.save()` method.
4. Wait for as many periods as you wish before stopping the service. Note that any measurement not saved at the end of a period will be lost.

The benchmark data will be stored in the folder `<service_folder>/abci_build/persistent_data/benchmarks`.

## Use the command line to aggregate benchmark information

1. **Run the service.** Build and run the agent service in [dev mode](./dev_mode.md#build-and-run-an-agent-service-in-dev-mode). (The tool also works if you run the agent [normal mode](../../guides/deploy_service.md#local-deployment-full-workflow).)

2. **Wait for service execution.** Wait until the service has completed at least one period before cancelling the execution. That is, wait until the `ResetAndPauseRound` round has occurred at least once. As commented above, this is required because benchmark data is saved in this state. Once you have a data dump, you can stop the local execution by pressing `Ctrl-C`.

3. **Aggregate the benchmark data.** The benchmark data will be stored in the folder `<service_folder>/abci_build/persistent_data/benchmarks`. Aggregate the data for all periods executing:

    ```bash
    autonomy analyse benchmarks abci_build/persistent_data/benchmarks
    ```

    This will generate a `benchmarks.html` file containing benchmark stats in your current directory.
    By default the script will generate output for all periods but you can specify which period to generate output for. Similarly, block types aggregation is configurable as well. For example,

    ```bash
    autonomy analyse benchmarks abci_build/persistent_data/benchmarks --period 2 --block-type consensus
    ```

    will aggregate stats for `consensus` code blocks in the second period.
    You can specify the `--block-type` option as `local` (to consider only local code blocks), `consensus` (to consider only consensus code blocks), `total` (to aggregate local + consensus code blocks) or `all` (to consider both consensus and local code blocks).
