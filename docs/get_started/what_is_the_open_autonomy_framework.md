{{open_autonomy}} is a framework for the creation of [agent services](./what_is_an_agent_service.md), and is realized on top of the {{open_aea}} framework.

{{open_aea}} is a framework for building arbitrary agent-based applications. It provides the elements to define and implement the required components of an agent, e.g., connections, protocols or skills.

On the other hand, the {{open_autonomy}} framework extends {{open_aea}} to a service architecture. That is, it allows to build applications as distributed systems (agent services) run by sets of agents.

Thus, the {{open_autonomy}} framework provides:

* A collection of **command line tools** to build, deploy, publish and test agent services.
* A collection of **packages with base classes** to create the necessary components that provide the underlying functionalities that AEAs need to become part of an agent service.

Throughout this doc pages you will learn both how AEAs are extended to a service architecture, and how to use the framework to manage these services.
