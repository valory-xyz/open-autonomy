[← Back to Developer Tools](../index.md)

The replay functionality of the dev mode allows to replay a previous execution of agents in a service for debugging purposes. This guide assumes that you have successfully [built and run an agent service in dev mode](./dev_mode.md#build-and-run-an-agent-service-in-dev-mode).

## Replay agent execution

1. **Run the service.** Build and run the agent service in [dev mode](./dev_mode.md#build-and-run-an-agent-service-in-dev-mode).

2. **Wait for service execution.** Wait until the service has completed at least one period before cancelling the execution. That is, wait until the `ResetAndPauseRound` round has occurred at least once. This is required because the CometBFT server will only dump CometBFT data when it reaches that state. Once you have a data dump, you can stop the local execution by pressing `Ctrl-C`.

3. **Recreate the CometBFT network.** Spawn a CometBFT network with the available dumps.

    ```bash
    # Replay using local CometBFT network
autonomy replay tendermint
    ```

4. **Replay agent execution.** Now, you can run replays for specified agents using

    ```bash
    autonomy replay agent AGENT_NUM
    ```

    where `AGENT_NUM` is a number between 0 and $N-1$, being $N$ the number of available agents. For example, to run the replay for the first agent, execute

    ```bash
    autonomy replay agent 0
    ```
