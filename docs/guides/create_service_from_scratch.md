Developing an agent service with the {{open_autonomy}} framework sometimes requires to build a custom agent for it, especially when the business logic of existing agents do not fit for the functionality of the service. This involves reusing or creating the packages that the new agents need: skills, connections, protocols, etc. This can seem a bit overwhelming at the beginning, as new developers might not be familiar with the structure of each one of those.

To simplify the development, the framework provides a scaffold tool that allow developers speed up their flow by auto-generating functional, skeleton classes with all the boilerplate code in place. Therefore, you can focus on implementing the actual business logic of the service.

##What you will learn

In this guide, you will learn how to:

- Use the scaffold tool to generate the skeleton classes that define the {{fsm_app}} skill of an agent service.
- Push the generated skill to the local registry for future reuse.

Before starting this guide, ensure that your machine satisfies the framework requirements and that you have followed the [set up guide](./set_up.md). As a result you should have a Pipenv workspace folder.

## Step-by-step instructions: using the scaffold tool

1. **Create an empty agent.** Use the {{open_autonomy}} CLI to create an empty agent as follows:
    ```bash
    autonomy create my_agent
    cd my_agent
    ```
    This will create the agent directory, that will contain folders for connections, contracts, protocols and skills.

2. **Create the FSM specification.** Now that the agent is in place, you can generate the basic structure of the {{fsm_app}} [skill](https://open-aea.docs.autonolas.tech/skill/). Recall that the {{fsm_app}} defines the business logic of the skill as a finite-state machine (see the [introduction to {{fsm_app}}s](../fsm_app_introduction.md)).

    To use the scaffold tool, you need the [FSM](../fsm.md) specification of the service. In this example, let's copy the contents of the [Hello World](../hello_world_agent_service.md) service FSM specification into a file called `fsm_specification.yaml`, which should be located in the agent's directory.

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

4. **Fill in the business logic code of the service.** By default, the generated rounds, payloads and behaviours are initialized to empty values. It is your turn to define what actions are occurring at each state of the service. You can review how a number of [demo services](../demos/index.md) are implemented, or read more about the internals of [{{fsm_app}}s](../fsm_app_introduction.md)).

5. **Push the generated skill to the local registry.** Now that you have successfully created the skill, you can push it to the local registry.

    To use the local registry, the framework expects that a `packages` directory exists at the same level as our agent. In this example, it expects that the directory `my_workspace/packages` exists. If you don't have a local registry, you can create it as
    ```bash
    mkdir ../packages
    ```

    Now, you can push the new skill to the local registry:
    ```bash
    autonomy push skill <your_author_name>/my_skill --local
    ```

    !!!note
        The flag `--local` in the command above forces to use the local registry.
        Recall that in the [setup instructions](./quick_start.md#setup) the framework has been initialized to use
        the remote registry. For this reason, this flag is required to instruct the framework to store the skill in the local registry.


6. **Clean up.** If we are only interested on the skill, we don't need the agent any more, so we can safely delete it:
    ```bash
    cd ..
    autonomy delete my_agent
    ```

Now, you can use the generated {{fsm_app}} skill to define the agent that will be part of your custom agent service. 
