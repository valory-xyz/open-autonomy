The figure below presents the development process with {{open_autonomy}}: from the idea of an off-chain AI agent to its deployment in production. If you have completed the [quick start guide](./quick_start.md) you have already navigated through a significant part of this process.

<figure markdown>
![](../images/development_process.svg)
<figcaption>Overview of the development process with the Open Autonomy framework</figcaption>
</figure>

This is a summary of each step:

1. [Draft the AI agent idea.](./draft_service_idea_and_define_fsm_specification.md#draft-the-ai-agent-idea) Any AI agent that needs to execute its functionality in an autonomous, transparent and decentralized way is a good candidate. You can take a look at some [use cases](../get_started/use_cases.md) to get an idea of what you can build with {{open_autonomy}}.

2. [Define the FSM specification.](./draft_service_idea_and_define_fsm_specification.md#define-the-fsm-specification) Describe the AI agent business logic as a [finite-state machine (FSM)](../key_concepts/fsm.md) in a language understood by the framework. This specification defines what are the states of the AI agent, and how to transit from one to another.

3. [Code the {{fsm_app}} skill.](./code_fsm_app_skill.md) The actual business logic is encoded in the {{fsm_app}} that lives inside each agent instance. Coding the {{fsm_app}} involves scaffolding the "skeleton" of the classes, and complete the actual details of the actions executed in each state.

4. [Define the agent blueprint.](./define_agent.md) Define the components of the agent blueprint required to execute your AI agent, including the newly created {{fsm_app}}. You can reuse already existing components publicly available on a remote registry.

5. [Define the AI agent.](./define_service.md) This consists in defining the AI agent configuration and declaring what agent blueprint constitute the AI agent, together with a number of configuration parameters required.

6. [Publish and mint packages.](./publish_mint_packages.md) Those are required steps to make the AI agent publicly available in the remote registry and secure it in the {{ autonolas_protocol }}.

7. [Deploy the AI agent.](./deploy_service.md) You can deploy directly your AI agent locally for testing purposes. To deploy a production AI agent secured in the {{ autonolas_protocol }} you first need to bring the AI agent to the _Deployed_ state in the protocol.

## Populate the local registry for the guides

To follow the next sections, you need to populate the local registry with a number of [packages shipped with the framework](../package_list.md). To do so, edit the local registry index file (`./packages/packages.json`) and ensure that it has the following `third_party` entries:

```json
{
    "dev": {
    },
    "third_party": {
        "service/valory/hello_world/0.1.0": "bafybeib5a5qxpx7sq6kzqjuirp6tbrujwz5zvj25ot7nsu3tp3me3ikdhy",
        "agent/valory/hello_world/0.1.0": "bafybeigfvkvjaqnelvjgrl2uroxdrwlcsabnusgdnkbsu6smwtg6skd52y",
        "connection/valory/abci/0.1.0": "bafybeidohvgi6hobingv3kftdp42h67mc2fonpwvfzsvwwab6me7mdlhjm",
        "connection/valory/http_client/0.23.0": "bafybeib34a2ukancj5524tz64smczju2q2njscgufmtml6dcjb3bjyaocy",
        "connection/valory/ipfs/0.1.0": "bafybeidhf3rcmxfk62rtzb5syij6546yygoldwyxrn3cnwql32nzabiiae",
        "connection/valory/ledger/0.19.0": "bafybeifdsep5suryfufmto4j5fyvjhmlgypyg6zvvwqsm4edlwfbfsav5y",
        "contract/valory/service_registry/0.1.0": "bafybeia2ojsye42jngihatprxcz4cpp2mysyidnmy5zehpshwt4zjf6xha",
        "protocol/open_aea/signing/1.0.0": "bafybeib7p5as3obcdzseiwg5umj2piiqaodkxkto7qh7b552l5emwsmdzm",
        "protocol/valory/abci/0.1.0": "bafybeicjjeintlqgg53zrreflmoafeiynt3gvdnovy5ocea7doddos3e5a",
        "protocol/valory/acn/1.1.0": "bafybeicztpzulro64brsms6qmlav3dz635eykpb7ihtchu2eke2hr52efa",
        "protocol/valory/contract_api/1.0.0": "bafybeicmo2ufeoqyyczkom6xp3nwmhosd75kpe4xfwn7gaz6vegj732b4m",
        "protocol/valory/http/1.0.0": "bafybeibxab2yfpchusrzw4rgrasjomtpphazanpivhhtznmuao5ny2lsmi",
        "protocol/valory/ipfs/0.1.0": "bafybeidqfs3njcishcwv4ymf4srxibw44u7qrnryxiwrg5ulk2h7myvt6q",
        "protocol/valory/ledger_api/1.0.0": "bafybeiga6gdd3ccdt5jgrov474koz524f3pfbhprwxfjj7wextkl7wozsa",
        "protocol/valory/tendermint/0.1.0": "bafybeie4jqosqiicefnlnxsvrymqj6tycv7x5qeitsdew6abhdcxlu23r4",
        "skill/valory/abstract_abci/0.1.0": "bafybeibvaza2eipkaclhqxojoyqn3prejqb64imamqxzi2qg5fnlkwicpi",
        "skill/valory/abstract_round_abci/0.1.0": "bafybeib4apybhtx3gx6o4x5b2nwqjkbdqi7dx7rxyrb5r3zztcdjiezvh4",
        "skill/valory/hello_world_abci/0.1.0": "bafybeibj7uripgimp6eklmkltpo2gwqyinq524wficoulod3b5ehzrivv4",
        "connection/valory/p2p_libp2p_client/0.1.0": "bafybeihezztwiiismlbblbv67i4zibp7w6xzpqadt67mcdjaoauibjqii4"
    }
}
```

Execute the following command after updating the `packages.json` file:

```bash
autonomy packages sync
```

The framework will fetch components from the remote registry into the local registry.

!!! tip "Do you already have an existing agent blueprint or AI agent?"

    If you already have an existing agent blueprint (or if you want to create an AI agent with the default `hello_world` agent blueprint), you can skip to [Step 5](./define_service.md).

    If you already have an existing AI agent (or if you want to test the default `hello_world` AI agent), you can skip to [Step 6](./publish_mint_packages.md) or [Step 7](./deploy_service.md).
