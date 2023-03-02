The next step consists in defining the service agent. All agents in the service share the same code base.
However, each operator can configure each agent instance. For example, in an oracle service,
each operator can define a different data provider.

<figure markdown>
![](../images/development_process_define_agent.svg)
<figcaption>Part of the development process covered in this guide</figcaption>
</figure>

## What you will learn

In this guide, you will learn how to define the service agent, and how to add the components that your service requires, including the {{fsm_app}}.

Before starting this guide, ensure that your machine satisfies the framework requirements and that you have followed the [set up guide](./set_up.md). As a result you should have a Pipenv workspace folder.

## Step-by-step instructions

1. **Create an empty agent.**

    ```bash
    autonomy create your_agent
    cd your_agent
    ```

2. **Add the {{fsm_app}}.** You can add it from the local registry or from the remote registry (if you have pushed it using `autonomy push`):

    === "Add from the local registry"

        ```bash
        autonomy --registry-path=../packages add skill your_name/your_fsm_app:0.1.0
        ```

    === "Add from the remote registry"

        ```bash
        autonomy add skill your_name/your_fsm_app:0.1.0:<hash>
        ```

    Observe that when adding a component, it will automatically add all its dependencies to the agent. Take a look at the agent configuration file `aea-config.yaml` to see what components have been added with the {{fsm_app}}.

3. **(Optional) Add further components.** If you require further components, you can add them in a similar way. You can browse the [list of packages](../package_list.md) available in the default remote IPFS registry.
    For example, if your service agent requires to connect to an HTTP server, you can add the `http_client` connection as follows:

    === "Add from the local registry"

        ```bash
        autonomy --registry-path=../packages add connection valory/http_client:0.23.0
        ```

    === "Add from the remote registry"

        ```bash
        autonomy add connection valory/http_client:0.23.0:bafybeidykl4elwbcjkqn32wt5h4h7tlpeqovrcq3c5bcplt6nhpznhgczi
        ```

    !!! warning "Important"

        In the [set up guide](./set_up.md) we initialized an empty local registry. You need first to fetch and sync the component from the remote registry, or use the remote registry directly.

5. **Publish the agent.** Once you have finished coding and testing the agent, [pubish it on a local or remote registry](./publish_fetch_packages.md#publish-an-agent-on-a-registry) for future reuse of the agent. Note down the agent public ID and the package hash.

    === "Publish to the remote registry"

        ```bash
        autonomy publish
        ```

!!! tip

    If your service requires to develop other kind of custom components, you can browse the {{open_aea_doc}} for further guidance. For example, have a look at how to create and interact with contracts in our [contract development guide](https://open-aea.docs.autonolas.tech/creating-contracts/).

