Developing an agent service with the {{open_autonomy}} framework sometimes requires to build a custom agent for it, especially when the business logic of existing agents do not fit for the functionality of the service. This involves reusing or creating the packages that the new agents need: skills, connections, protocols, etc. This can seem a bit overwhelming at the beginning, as new developers might not be familiar with the structure of each one of those.


##What you will learn

In this guide, you will learn how to:

- The overall life cycle to create the {{fsm_app}} of a new agent service.
- Use the scaffold tool to generate the skeleton classes that define the {{fsm_app}} skill of an agent service.


Before starting this guide, ensure that your machine satisfies the framework requirements and that you have followed the [set up guide](./set_up.md). As a result you should have a Pipenv workspace folder.

## Step-by-step instructions: using the scaffold tool


Now, you can use the generated {{fsm_app}} skill to define the agent that will be part of your custom agent service.



5. **Optionally, create additional components**. If required by your skills, you can add additional components for the agents that make up the service. You can browse the {{open_aea}} docs for further guidance. For example, have a look at how to create and interact with contracts in our [contract development guide](https://open-aea.docs.autonolas.tech/creating-contracts/).
