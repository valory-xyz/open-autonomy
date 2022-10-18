Developing an agent service with the {{open_autonomy}} framework sometimes requires to build a custom agent for it, especially when the business logic of existing agents do not fit for the functionality of the service. This involves reusing or creating the packages that the new agents need: skills, connections, protocols, etc. This can seem a bit overwhelming at the beginning, as new developers might not be familiar with the structure of each one of those.

To simplify the development, the framework provides a scaffold tool that allow developers speed up their flow by auto-generating functional, skeleton classes with all the boilerplate code in place. Therefore, you can focus on implementing the actual business logic of the {{fsm_app}} skill of the service.

##What you will learn

In this guide, you will learn how to:

- The overall life cycle to create the {{fsm_app}} of a new agent service.
- Use the scaffold tool to generate the skeleton classes that define the {{fsm_app}} skill of an agent service.


Before starting this guide, ensure that your machine satisfies the framework requirements and that you have followed the [set up guide](./set_up.md). As a result you should have a Pipenv workspace folder.

## Step-by-step instructions: using the scaffold tool

1. **Create an empty agent.** Use the {{open_autonomy}} CLI to create an empty agent as follows:
    ```bash
    autonomy create my_agent
    cd my_agent
    ```
    This will create the agent directory, that will contain folders for connections, contracts, protocols and skills.

2. **Create the FSM specification.** Now that the agent is in place, you can generate the basic structure of the {{fsm_app}} skill. Recall that the {{fsm_app}} defines the business logic of the skill as a finite-state machine (see the [introduction to {{fsm_app}}s](../key_concepts/fsm_app_introduction.md)).

    To use the scaffold tool, you need the [FSM](../key_concepts/fsm.md) specification of the service. In this example, let's copy the contents of the [Hello World](../demos/hello_world_demo.md) service FSM specification into a file called `fsm_specification.yaml`, which should be located in the agent's directory.

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

3. **Generate the template classes.** Using the scaffold tool to generate the skeleton for the classes for the skill:
    ```bash
    autonomy scaffold fsm my_skill --spec fsm_specification.yaml
    ```
    You will see that the generated rounds, payloads and behaviours already appear with their correct names, as well as the `HelloWorldAbciApp` and its transition function.

4. **Fill in the business logic code of the service.** By default, the generated rounds, payloads and behaviours are initialized to empty values. It is your turn to define what actions are occurring at each state of the service, by filling up the code of the template {{fsm_app}} skill generated above. You can review how a number of [demo services](../demos/index.md) are implemented, or read more about the internals of [{{fsm_app}}s](../key_concepts/fsm_app_introduction.md)).

5. **Optionally, create additional components**. If required by your skills, you can add additional components for the agents that make up the service. You can browse the {{open_aea}} docs for further guidance. For example, have a look at how to create and interact with contracts in our [contract development guide](https://open-aea.docs.autonolas.tech/creating-contracts/).

6. **Push the generated skill to the local registry.** Once you have finished creating the {{fsm_app}} skill, you can [push it to a local or remote registry](./managing_packages.md) for future reuse of the component.

7. **Clean up.** If you are only interested in the {{fsm_app}} skill created, you don't need the agent any more, so it can be safely deleted:
    ```bash
    cd ..
    autonomy delete my_agent
    ```

Now, you can use the generated {{fsm_app}} skill to define the agent that will be part of your custom agent service.
