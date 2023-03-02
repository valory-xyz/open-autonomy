
Recall that the **{{fsm_app}}** is the core part of a service agent, and it defines the business logic of the service. Developing the {{fsm_app}} is possibly the largest step in the [development process](./overview_of_the_development_process.md).

For this reason, in order to simplify and speed up the development of agent services, the {{open_autonomy}} framework provides an **{{fsm_app}} scaffold tool** that allows you to auto-generate functional, skeleton classes with all the boilerplate code in place. Therefore, you can focus on implementing the actual business logic of the of the service itself.

<figure markdown>
![](../images/development_process_create_fsm_app.svg)
<figcaption>Part of the development process covered in this guide</figcaption>
</figure>

## What you will learn

In this guide, you will learn how to use the {{fsm_app}} scaffold tool to generate the skeleton classes that define the {{fsm_app}} skill of an agent service.

Before starting this guide, ensure that your machine satisfies the framework requirements and that you have followed the [set up guide](./set_up.md). As a result you should have a Pipenv workspace folder.

## Step-by-step instructions

This guide assumes that you have [created an {{fsm_app}} specification file](./draft_service_idea_and_define_fsm_specification.md#define-the-fsm-specification).

1. **Generate the template classes.** Use the scaffold tool to generate the template for the classes of the {{fsm_app}}:

    ```bash
    autonomy scaffold -tlr fsm your_fsm_app_name --spec fsm_specification.yaml
    ```

    This command will generate the {{fsm_app}} skill with its corresponding classes: rounds, payloads, behaviours, and the [`AbciApp` class](../key_concepts/abci_app_class.md). The {{fsm_app}} skill will be generated within the local repository (`./packages`) in the folder `./packages/<your_name>/skills/your_fsm_app_name`.

2. **Fill in the business logic code of the {{fsm_app}}.** By default, the generated classes are initialized to empty values. It is your turn to define what actions are occurring at each state of the service, by filling up the code of the template {{fsm_app}} skill generated above. You should also define a number of test classes. You can review how the [demo services](../demos/index.md) are implemented, or read about the [internals of {{fsm_app}}s](../key_concepts/fsm_app_introduction.md) to learn more.

3. **Push the generated skill to the remote registry.** Once you have finished coding and testing the {{fsm_app}} skill, you can [push it to a remote registry](./publish_fetch_packages.md#push-and-add-components). This will allow to add and reuse the {{fsm_app}} skill in newly developed agents.
