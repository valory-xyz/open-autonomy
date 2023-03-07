
Recall that the **{{fsm_app}}** is the core part of a service agent, and it defines the business logic of the service. Developing the {{fsm_app}} is possibly most demanding step in the development process.

<figure markdown>
![](../images/development_process_create_fsm_app.svg)
<figcaption>Part of the development process covered in this guide</figcaption>
</figure>

In order to simplify and speed up the development, the {{open_autonomy}} framework provides an **{{fsm_app}} scaffold tool** that auto-generates functional, template classes with all the boilerplate code in place. Therefore, you can focus on completing the actual operations executed in each state of the service.

## What you will learn

This guide covers step 3 of the [development process](./overview_of_the_development_process.md). You will learn how to use the {{fsm_app}} scaffold tool to generate the template classes that define the {{fsm_app}} skill, and identify what methods you need to implement to complete the skill.

## Step-by-step instructions

1. **Generate the {{fsm_app}} template.** Given the {{fsm_app}} specification file `fsm_specification.yaml` [that you have created in the previous step](./draft_service_idea_and_define_fsm_specification.md#define-the-fsm-specification) (and which should be located in the workspace folder), use the scaffold tool to generate the template for the classes of the {{fsm_app}}:

    ```bash
    autonomy scaffold -tlr fsm your_fsm_app_name --spec fsm_specification.yaml
    ```

    This command will generate the {{fsm_app}} skill with a template for the [necessary classes](../key_concepts/fsm_app_introduction.md): rounds, payloads, behaviours, and the `AbciApp` class. The `-tlr` flag indicates that the {{fsm_app}} skill will be generated in the local registry (`workspace_folder/packages`). The actual path will be

    ```
    workspace_folder/packages/your_name/skills/your_fsm_app_name/
    ```

2. **Fill in the business logic code of the {{fsm_app}}.** By default, the generated classes don't execute any operation. It is your turn to define what actions are occurring at each state of the service, by filling up the code of the template classes generated above. You can identify the main places where you whould populate code by browsing for `# TODO` comments.

    You should also define a number of test classes. You can review how the [demo services](../demos/index.md) are implemented, or read about the [internals of {{fsm_app}}s](../key_concepts/fsm_app_introduction.md) to learn how to code the template classes.

3. **Push the {{fsm_app}} skill to the remote registry.** Once you have finished coding and testing the {{fsm_app}} skill, [push it to the remote registry](./publish_fetch_packages.md#push-and-add-components):

    ```bash
    autonomy push skill ./packages/your_name/skills/your_fsm_app_name/
    ```

    Note down the {{fsm_app}} skill public ID and the package hash.