Having a service developed and deployed using the {{open_autonomy}} is a journey that consists of a number of steps. The process may look intimidating at a first glance, but if you have completed the [quick start guide](../quick_start) you have already navigated through a significant part of it.

The overall development process is summarized in the figure below. Whereas you don't need to memorize it, it is recommended that you have a certain familiarity with it when you use the framework. You can always revisit this documentation when in doubt.

<figure markdown>
![](../images/development_process.svg)
<figcaption>Overview of the development process with the Open Autonomy framework</figcaption>
</figure>

We will explore this process in detail in several guides included in this section. But for now, let us briefly present what is going on in each of the steps (1-6):

1. It all starts with an **idea for a service**. Any service that needs to execute its functionality in an autonomous, transparent and decentralized way is a good candidate. You can take a look at some [use cases](../get_started/use_cases.md) to get an idea of what you can build with {{open_autonomy}}.

2. Here is where the development starts. The first task towards having your agent service up and running is to describe the service business logic as a **finite-state machine (FSM) specification**. Roughly speaking, the specification defines the states where the agent service can be, and how to transit from one state to another. We will discuss this in further guides.

3. Once we have the FSM specification, the next step consists in coding the component that will be the core of the agents running the service: the **FSM App component**.
  The framework provides scaffolding tools so that you can create boilerplate code using the simple FSM specified in Step 2, and you will only need to implement the business logic part for your service. You can also use the [developer template repository](https://github.com/valory-xyz/dev-template) as the starting point. It includes
  the recommended linters, continuous integration and several other files so you don't need to start from scratch.

    !!! note
        We recommend that your developed components have exhaustive tests and pass the library linters before uploading them to a remote registry.

4. Having the FSM App for the service coded the next step is the **agent definition**. That is, use the FSM App just defined, and possibly some other readily available components, to define the agent that will run the service.

5. Similarly, the **service configuration** declares what agents constitute the service, together with a number of configuration parameters required by the service.

6. The next step is to **register the service on-chain**. This is required to use the service with the on-chain protocol.

7. Finally, the next step consists in have the **service deployed**. If you want to deploy the service locally (e.g., for testing purposes), you can do so directly with the {{open_autonomy}} CLI. On the other hand, if you want that your service is secured through the on-chain registry, you need to interact with the on-chain protocol front-end. We will detail how to do this in the guide [deploy a service](./deploy_service.md)

As you can see in the diagram above any developed component can be pushed/published to a remote registry, and registered in the on-chain registry. This mechanism allows that developers reuse components written by other developers, thus reducing the invested time in developing common functionalities.

We will explore in a number of guides how to navigate through the development process in various scenarios.
