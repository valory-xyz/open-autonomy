The figure below presents the development process with {{open_autonomy}}: from the idea of an off-chain service to its deployment in production. If you have completed the [quick start guide](../quick_start) you have already navigated through a significant part of this process.

<figure markdown>
![](../images/development_process.svg)
<figcaption>Overview of the development process with the Open Autonomy framework</figcaption>
</figure>

This is a summary of each step:

1. **Draft the service idea.** Any service that needs to execute its functionality in an autonomous, transparent and decentralized way is a good candidate. You can take a look at some [use cases](../get_started/use_cases.md) to get an idea of what you can build with {{open_autonomy}}.

2. **Define the FSM specification.** Describe the service business logic as a [finite-state machine (FSM)](../key_concepts/fsm.md) in a language understood by the framework. This specification defines what are the states of the service, and how to transit from one to another.

3. **Code the {{fsm_app}} skill.** The actual business logic is encoded in the {{fsm_app}} that lives inside each agent. Coding the {{fsm_app}} involves scaffolding the "skeleton" of the classes, and complete the actual details of the actions executed in each state.

4. **Define the agent.** Define the components of the agent required to execute your service, including the newly created {{fsm_app}}. You can reuse already existing components publicly available on a remote registry.

5. **Define the service.** This consists in defining the service configuration and declaring what agents constitute the service, together with a number of configuration parameters required.

6. **Publish and mint packages.** Those are required steps to make the service publicly available in the remote registry and secure it in the {{ autonolas_protocol }}.

7. **Deploy the service.** You can deploy directly your service locally for testing purposes. To deploy a production service secured in the {{ autonolas_protocol }} you first need to bring the service to the _Deployed_ state in the protocol.

In the next sections, we will explore in detail each of these steps in the development process.


!!! tip "Do you already have an existing agent or service?"
    	
    If you already have an existing agent (or if you want to create a service with the default `hello_world` agent), you can skip to [Step 5](./define_service.md).
    	
    If you already have an existing service (or if you want to test the default `hello_world` service), you can skip to [Step 6](./publish_mint_packages.md) or [Step 7](./deploy_service.md).
