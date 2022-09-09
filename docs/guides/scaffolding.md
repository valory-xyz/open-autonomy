Developing with the {{open_autonomy}} framework usually entails creating all the packages that the new agents need: skills, connections, protocols... This can seem a bit overwhelming at the beginning, as new developers might not be familiar with the structure of each one of those. To simplify the development, the framework provides a scaffold tool that lets developers speed up their flow by auto-generating boilerplate code.

##What you will learn

In this guide, we will show how to:

- Create different packages using the scaffold tool.

## Setup

!!!note
    You might have already prepared your enviroment if you went through the [quick start](https://docs.autonolas.network/quick_start/) guide. If that's the case, you can skip this section.

Before starting this guide, ensure that your machine satisfies the [framework requirements](./quick_start.md#requirements) and that
you have followed the [setup instructions](./quick_start.md#setup). As a result you should have a Pipenv workspace folder.

1. Create a workspace folder:
```bash
mkdir my_workspace
cd my_workspace
```

2. Setup the environment. Remember to use the Python version you have installed. Here we are using 3.10 as reference:
```bash
touch Pipfile && pipenv --python 3.10 && pipenv shell
```

3. Install the {{open_autonomy}} framework:
```bash
pip install open-autonomy
```

4. Initialize the framework to work with the remote [IPFS](https://ipfs.io) registry. This means that when the framework will be fetching a component, it will do so from the [IPFS](https://ipfs.io):
    ```bash
    autonomy init --remote --ipfs
    ```

## Ussing the scaffold tool: step-by-step instructions

First, create an empty agent using the autonomy CLI. This will create the agent directory, that will contain folders for connections, contracts, protocols and skills.
```
autonomy create my_agent
cd my_agent
```
Now that the agent is in place, you can follow the next sections examples to add your packages.

### Scaffold a connection.
To add yout first [connection](https://open-aea.docs.autonolas.tech/connection/), run:
```
autonomy scaffold connection my_connection
```

### Scaffold a contract.
To scaffold a new [contract](https://open-aea.docs.autonolas.tech/contract/), run:
```
autonomy scaffold contract my_contract
```

### Scaffold a protocol.
To generate a new [protocol](https://open-aea.docs.autonolas.tech/protocol/), execute:
```
autonomy scaffold protocol my_protocol
```

### Scaffold a skill.
Create a simple [skill](https://open-aea.docs.autonolas.tech/skill/) running:
```
autonomy scaffold skill my_skill
```

### Scaffold a skill using its FSM.
In the previous section, we generated the basic structure of a [skill](https://open-aea.docs.autonolas.tech/skill/). But there's a better way of doing so if you already have its [FSM](https://docs.autonolas.network/fsm/) specification. For example, let's copy the contents of the [Hello World](https://docs.autonolas.network/hello_world_agent_service/) service FSM specification into a file called ```fsm_specification.yaml```. Put it inside your agent's directory.

```
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

Now, run the scaffold tool:

```
autonomy scaffold fsm my_other_skill --spec fsm_specification.yaml
```

In this case, you'll see that the generated rounds, payloads and behaviours already appear with their correct names, as well as the HelloWorldAbciApp and its transition function.

### Scaffold the decision maker.
Run the following to scaffold the [decision maker](https://open-aea.docs.autonolas.tech/decision-maker/):
```
autonomy scaffold decision-maker-handler
```

### Scaffold an error-handler.
To create a new error handler, execute:
```
autonomy scaffold error-handler
```
You can learn more about message handling reading the [message routing](https://open-aea.docs.autonolas.tech/message-routing/) section of the docs.
