The replay functionality of the dev mode allows to replay a previous execution of agent instances in an AI agent for debugging purposes. This guide assumes that you have successfully [built an run an AI agent in dev mode](./dev_mode.md#build-and-run-an-ai-agent-in-dev-mode).

## Replay AI agent execution

1. **Run the AI agent.** Build and run the AI agent in [dev mode](./dev_mode.md#build-and-run-an-ai-agent-in-dev-mode).

2. **Wait for AI agent execution.** Wait until the AI agent has completed at least one period before cancelling the execution. That is, wait until the `ResetAndPauseRound` round has occurred at least once. This is required because the Tendermint server will only dump Tendermint data when it reaches that state. Once you have a data dump, you can stop the local execution by pressing `Ctrl-C`.

3. **Recreate the Tendermint network.** Spawn a Tendermint network with the available dumps.

    ```bash
    autonomy replay tendermint
    ```

4. **Replay AI agent execution.** Now, you can run replays for specified agent instances using

    ```bash
    autonomy replay agent AGENT_NUM
    ```

    where `AGENT_NUM` is a number between 0 and $N-1$, being $N$ the number of available agent instances. For example, to run the replay for the first agent instance, execute

    ```bash
    autonomy replay agent 0
    ```
