When developing your service (and its required components, including the {{fsm_app}}), it is important to ensure that the code is exhaustively tested and adheres to best practices. This will not only help identify and fix any bugs or errors early, but also ensure your code is reliable, efficient, and maintainable.

## Static code analysis

### Standard tools

For convenience the [Dev template](https://github.com/valory-xyz/dev-template) comes with a Pipenv that includes a number of tools grouped under predefined make targets.

Make target: `make formatters`

: | Tool                                       | Description                                                                                             |
    |--------------------------------------------|---------------------------------------------------------------------------------------------------------|
    | [`black`](https://black.readthedocs.io/)   | A Python code formatter that automatically reformats code to conform to a consistent style.             |
    | [`isort`](https://pycqa.github.io/isort/ ) | A Python tool that sorts imports alphabetically and separates them into sections, making it easier to read and maintain import statements in Python code. |

Make target: `make code-checks`

: | Tool                                                 | Description                                                                                                                                                         |
|------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [`darglint`](https://pypi.org/project/darglint/)     | A Python docstring argument linter that checks for adherence to Google's style guide.                                                                               |
| [`mypy`](https://mypy-lang.org/)                     | A static type checker for Python that analyses code and provides feedback on variable types and potential errors.                                                   |
| [`flake8`](https://flake8.pycqa.org/en/latest/)      | A Python tool that combines multiple linters to check code for syntax errors, style violations, and other issues.                                                   |
| [`pylint`](https://github.com/pylint-dev/pylint)     | A Python code analyser that checks code for potential errors, security vulnerabilities, and style violations, and provides feedback on how to improve code quality. |
| [`vulture`](https://github.com/jendrikseipp/vulture) | A Python tool that analyses code for unused variables, functions, and other dead code that can be safely removed to improve code quality and performance.           |

### Framework-specific tools

In addition, the framework comes with a number of dedicated tools that you might find useful for analysing your service and component packages.

`autonomy check-packages`
: Performs several consistency checks on the component packages to make sure there are no issues with the component configurations (including checking that every package has existing dependencies and a non-empty description).

[`autonomy analyse handlers`](../advanced_reference/commands/autonomy_analyse.md#autonomy-analyse-handlers)
: This command verifies that all the {{fsm_app}} skills in a local registry (except the explicitly excluded ones) have defined the specified handlers. See the command documentation [here](../advanced_reference/commands/autonomy_analyse.md#autonomy-analyse-handlers).

[`autonomy analyse dialogues`](../advanced_reference/commands/autonomy_analyse.md#autonomy-analyse-dialogues)
: This command verifies that all the {{fsm_app}} skills in a local registry (except the explicitly excluded ones) have defined the specified dialogues. See the command documentation [here](../advanced_reference/commands/autonomy_analyse.md#autonomy-analyse-dialogues).

[`autonomy analyse service`](../advanced_reference/commands/autonomy_analyse.md#autonomy-analyse-service)
: This command verifies a service configuration to see if there is any potential issue with it which can cause issues when running the service deployment. See the command documentation [here](../advanced_reference/commands/autonomy_analyse.md#autonomy-analyse-service) and the [on-chain deployment checklist](./on-chain_deployment_checklist.md) for more information.

## Testing

### Unit testing

The `valory/abstract_round_abci` skill packages come with a number of testing tools located in `packages/valory/skills/abstract_round_abci/test_tools` which you can use to write unit tests for your {{fsm_app}}s.

???+ example

    Fetch the `hello_world` agent, which comes with the `hello_world_abci` {{fsm_app}} skill within:

    ```bash
    autonomy fetch valory/hello_world:0.1.0:bafybeihtmp45mbfs5tyzrgxfoimh552on6dif42ifqidifait3ej2m5zvq --alias hello_world_agent
    ```

    Look at the unit tests for the `hello_world_abci` skill, located in the folder

    ```
    ./hello_world_agent/vendor/valory/skills/hello_world_abci/tests/
    ```

### Integration testing

The `open-aea-test-autonomy` plugin provides several test classes which can be utilized for various Docker integration tests. Here are some examples of the base test classes:

* `aea_test_autonomy.base_test_classes.BaseContractTest`: Comes with utilities required for testing a contract.
* `aea_test_autonomy.base_test_classes.BaseGanacheContractTest`: Can be used for testing contracts on a local Ganache instance.
* `aea_test_autonomy.base_test_classes. BaseRegistriesContractsTest`: Launches a local Hardhat node with pre-deployed Autonolas registries contracts image.

### End-to-end testing

The same plugin also provides tools for writing end-to-end tests for agents. The `aea_test_autonomy.base_test_classes.agents.BaseTestEnd2End` class provides an environment for testing agents end to end.

???+ example

    Fetch the `hello_world` agent:

    ```bash
    autonomy fetch valory/hello_world:0.1.0:bafybeihtmp45mbfs5tyzrgxfoimh552on6dif42ifqidifait3ej2m5zvq --alias hello_world_agent
    ```

    Look at the end-to-end tests, located in the folder

    ```
    ./hello_world_agent/tests/
    ```

The framework also provides CLI tools for building and running [local testing deployments](../guides/deploy_service.md#local-deployment-full-workflow).
You can include additional images in your testing deployment, for example, a Hardhat node with custom contracts, or an ACN node. This is achieved through the flags `--use-hardhat` and `--use-acn`, respectively. Read the [`autonomy deploy build` command documentation](../advanced_reference/commands/autonomy_deploy.md#autonomy-deploy-build) and the guide for [using custom images in a deployment](../advanced_reference/use_custom_images.md#images-used-in-testing-only) for more information.
