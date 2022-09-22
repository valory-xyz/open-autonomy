Developing with the {{open_autonomy}} framework usually entails creating all the packages that the new agents need: skills, connections, protocols... This can seem a bit overwhelming at the beginning, as new developers might not be familiar with the structure of each one of those. To simplify the development, the framework provides a scaffold tool that lets developers speed up their flow by auto-generating boilerplate code.

##What you will learn

In this guide, we will show how to:

- Create a skill package using the scaffold tool.
- Push the generated skill to the local registry.


## Using the scaffold tool: step-by-step instructions

Before starting this guide, ensure that your machine satisfies the [framework requirements](./quick_start.md#requirements) and that
you have followed the [setup instructions](./quick_start.md#setup). As a result you should have a Pipenv workspace folder.

1. **Create an empty agent.** Use the {{open_autonomy}} CLI to create an empty agent as follows:
    ```bash
    autonomy create my_agent
    cd my_agent
    ```
    This will create the agent directory, that will contain folders for connections, contracts, protocols and skills.

2. **Create the FSM specification.** Now that the agent is in place, you can generate the basic structure of a [skill](https://open-aea.docs.autonolas.tech/skill/). For that, you need its [FSM](../fsm.md) specification. In this example, let's copy the contents of the [Hello World](../hello_world_agent_service.md) service FSM specification into a file called ```fsm_specification.yaml```. Put it inside your agent's directory.

    ```yaml
    alphabet_in:
    - DONE
    - NO_MAJORITY
    - RESET_TIMEOUT
    - ROUND_TIMEOUT
    default_start_state: RegistrationRound
    final_states: []
    label: packages.valory.skills.hello_world_abci.rounds.HelloWorldAbciApp
    start_states:
    - RegistrationRound
    states:
    - PrintMessageRound
    - RegistrationRound
    - ResetAndPauseRound
    - SelectKeeperRound
    transition_func:
        (PrintMessageRound, DONE): ResetAndPauseRound
        (PrintMessageRound, ROUND_TIMEOUT): RegistrationRound
        (RegistrationRound, DONE): SelectKeeperRound
        (ResetAndPauseRound, DONE): SelectKeeperRound
        (ResetAndPauseRound, NO_MAJORITY): RegistrationRound
        (ResetAndPauseRound, RESET_TIMEOUT): RegistrationRound
        (SelectKeeperRound, DONE): PrintMessageRound
        (SelectKeeperRound, NO_MAJORITY): RegistrationRound
        (SelectKeeperRound, ROUND_TIMEOUT): RegistrationRound
    ```

3. **Generate the template classes.** Using the scaffold tool to generate the skeleton for the classes:
    ```bash
    autonomy scaffold fsm my_skill --spec fsm_specification.yaml
    ```
    You will see that the generated rounds, payloads and behaviours already appear with their correct names, as well as the `HelloWorldAbciApp` and its transition function.

4. **Push the generated skill to the local registry.** Now that you have successfully created the skill, you can push it to the local registry. Since to fetch all packages from IPFS we had used the remote registry, we now need to reset it so we use a local one during the development:

    ```bash
    autonomy init --local --reset --author AUTHOR
    ```

    To use the local registry, it is expected that a `packages` directory exists at the same level as our agent. If you already have it then you can skip this step, but if you don't then you need to create it. In this example, we need to create `my_workspace/packages`.
    ```bash
    mkdir ../packages
    ```

    And we can now push our new skill to the local registry:
    ```bash
    autonomy push skill <your_author_name>/my_skill
    ```

5. **Clean up.** If we were only interested on the skill we don't need the agent any more, so we can safely delete it:
    ```bash
    cd ..
    autonomy delete my_agent
    ```
