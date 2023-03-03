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

1. **Create an empty agent.** Use the CLI to create an empty agent in the workspace folder.

    ```bash
    autonomy create your_agent
    cd your_agent
    ```

    You will notice that a number of files and folders have already been created. Take a moment to look at the agent configuration file `aea-config.yaml`, which defines all the component dependencies for the agent.

2. **Add the {{fsm_app}}.** You can add it from the local registry or from the remote registry (using the `<hash>` value obtained when you pushed it using `autonomy push`):

    === "Add from the remote registry"

        ```bash
        autonomy add skill your_name/your_fsm_app:0.1.0:<hash>
        ```

    === "Add from the local registry"

        ```bash
        autonomy --registry-path=../packages add skill your_name/your_fsm_app:0.1.0
        ```

    Observe that when adding a component, it will automatically add all its dependencies to the agent. Look how the agent configuration file `aea-config.yaml` has been updated.

3. **(Optional) Add further components.** If you require further components, you can add them in a similar way. You can browse the [list of packages](../package_list.md) available in the default remote IPFS registry.
    For example, if your service agent requires to connect to an HTTP server, you can add the `http_client` connection as follows:

    === "Add from the remote registry"

        ```bash
        autonomy add connection valory/http_client:0.23.0:bafybeidykl4elwbcjkqn32wt5h4h7tlpeqovrcq3c5bcplt6nhpznhgczi
        ```

    === "Add from the local registry"

        ```bash
        autonomy --registry-path=../packages add connection valory/http_client:0.23.0
        ```

    Note that you can only add components from the local registry if they are present there.

5. **Publish the agent.** Once you have finished coding and testing the agent, [pubish it on the local and/or remote registry](./publish_fetch_packages.md#publish-an-agent-on-a-registry). Note down the agent public ID and the package hash:

    === "Publish to the remote registry"

        ```bash
        autonomy publish
        ```

    === "Publish to the remote registry"

        ```bash
        (This section will be updated soon)
        ```

!!! tip

    If your service agent requires to develop other kind of custom components, you can browse the {{open_aea_doc}} for further guidance. For example, have a look at how to create and interact with contracts in our [contract development guide](https://open-aea.docs.autonolas.tech/creating-contracts/).

