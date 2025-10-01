The figure below presents the development process with {{open_autonomy}}: from the idea of an off-chain service to its deployment in production. If you have completed the [quick start guide](./quick_start.md) you have already navigated through a significant part of this process.

<figure markdown>
![](../images/development_process.svg)
<figcaption>Overview of the development process with the Open Autonomy framework</figcaption>
</figure>

This is a summary of each step:

1. [Draft the service idea.](./draft_service_idea_and_define_fsm_specification.md#draft-the-service-idea) Any service that needs to execute its functionality in an autonomous, transparent and decentralized way is a good candidate. You can take a look at some [use cases](../get_started/use_cases.md) to get an idea of what you can build with {{open_autonomy}}.

2. [Define the FSM specification.](./draft_service_idea_and_define_fsm_specification.md#define-the-fsm-specification) Describe the service business logic as a [finite-state machine (FSM)](../key_concepts/fsm.md) in a language understood by the framework. This specification defines what are the states of the service, and how to transit from one to another.

3. [Code the {{fsm_app}} skill.](./code_fsm_app_skill.md) The actual business logic is encoded in the {{fsm_app}} that lives inside each agent. Coding the {{fsm_app}} involves scaffolding the "skeleton" of the classes, and complete the actual details of the actions executed in each state.

4. [Define the agent.](./define_agent.md) Define the components of the agent required to execute your service, including the newly created {{fsm_app}}. You can reuse already existing components publicly available on a remote registry.

5. [Define the service.](./define_service.md) This consists in defining the service configuration and declaring what agents constitute the service, together with a number of configuration parameters required.

6. [Publish and mint packages.](./publish_mint_packages.md) Those are required steps to make the service publicly available in the remote registry and secure it in the {{ autonolas_protocol }}.

7. [Deploy the service.](./deploy_service.md) You can deploy directly your service locally for testing purposes. To deploy a production service secured in the {{ autonolas_protocol }} you first need to bring the service to the _Deployed_ state in the protocol.

## Populate the local registry for the guides

To follow the next sections, you need to populate the local registry with a number of [packages shipped with the framework](../package_list.md). To do so, edit the local registry index file (`./packages/packages.json`) and ensure that it has the following `third_party` entries:

```json
{
    "dev": {
    },
    "third_party": {
        "service/valory/hello_world/0.1.0": "bafybeicj73kflta5sfxq7gnnk7smcdp2gwcfvfvm2plxc5ojhulwa3xnoq",
        "agent/valory/hello_world/0.1.0": "bafybeig2mv6afojsype4v2fwkpzkvdohbeg6ilvp2tokn7i6ub2csd6wxi",
        "connection/valory/abci/0.1.0": "bafybeig6hnll4fddbqlgt26z74mgo2scaxlhnwhzusxrz7tbd7at6boxdi",
        "connection/valory/http_client/0.23.0": "bafybeib34a2ukancj5524tz64smczju2q2njscgufmtml6dcjb3bjyaocy",
        "connection/valory/ipfs/0.1.0": "bafybeif7exoq2viwhfgfcjplxq73hnxvgpsx7pwshhntx6aekza25mdwli",
        "connection/valory/ledger/0.19.0": "bafybeifdsep5suryfufmto4j5fyvjhmlgypyg6zvvwqsm4edlwfbfsav5y",
        "contract/valory/service_registry/0.1.0": "bafybeigi3efqi5nofhe6d24tnznr5xisacyav24zc37f77xetm4t7azovy",
        "protocol/open_aea/signing/1.0.0": "bafybeib7p5as3obcdzseiwg5umj2piiqaodkxkto7qh7b552l5emwsmdzm",
        "protocol/valory/abci/0.1.0": "bafybeigdi6wsbdn2nv7clzhnuhki3taywgiiajwawdaat57o5ntlgqj2qe",
        "protocol/valory/acn/1.1.0": "bafybeicztpzulro64brsms6qmlav3dz635eykpb7ihtchu2eke2hr52efa",
        "protocol/valory/contract_api/1.0.0": "bafybeicmo2ufeoqyyczkom6xp3nwmhosd75kpe4xfwn7gaz6vegj732b4m",
        "protocol/valory/http/1.0.0": "bafybeibxab2yfpchusrzw4rgrasjomtpphazanpivhhtznmuao5ny2lsmi",
        "protocol/valory/ipfs/0.1.0": "bafybeib7jhgyocjwdq3r5wzq3z4qeubj3dwi3aqjn2uxzuwnjp5fhvafcu",
        "protocol/valory/ledger_api/1.0.0": "bafybeiga6gdd3ccdt5jgrov474koz524f3pfbhprwxfjj7wextkl7wozsa",
        "protocol/valory/tendermint/0.1.0": "bafybeif5wq5i2ugr66alniej2bk4vws5sikal7otx674y5kz52e3ulo2qm",
        "skill/valory/abstract_abci/0.1.0": "bafybeidswz43c4c3ivxuqz6iqbo7snxc6snox3ztn6dzh76si3k7uiolou",
        "skill/valory/abstract_round_abci/0.1.0": "bafybeiemzg3e2hc5hjnpqj4kulxq4mjz65ktelqdgb6wvxekiwudjp63uu",
        "skill/valory/hello_world_abci/0.1.0": "bafybeihmpphbsrr5niduaf3r2jzqjjoip5ep5aynphxfoqqqdzmkwobwyi",
        "connection/valory/p2p_libp2p_client/0.1.0": "bafybeihezztwiiismlbblbv67i4zibp7w6xzpqadt67mcdjaoauibjqii4"
    }
}
```

Execute the following command after updating the `packages.json` file:

```bash
autonomy packages sync
```

The framework will fetch components from the remote registry into the local registry.

!!! tip "Do you already have an existing agent or service?"

    If you already have an existing agent (or if you want to create a service with the default `hello_world` agent), you can skip to [Step 5](./define_service.md).

    If you already have an existing service (or if you want to test the default `hello_world` service), you can skip to [Step 6](./publish_mint_packages.md) or [Step 7](./deploy_service.md).
