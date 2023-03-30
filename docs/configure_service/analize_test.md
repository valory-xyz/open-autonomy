It is important to ensure that the code of your service and components that you develop is exhaustively tested and adheres to best practices. This will not only help identify and fix any bugs or errors early, but also ensure your code is reliable, efficient, and maintainable.
Most of the tools cited in this section are already included in the [Dev template](https://github.com/valory-xyz/dev-template) grouped under predefined make targets.

## Third-party tools

These are customary tools to ensure that your Python code has no errors.

Make target: `make formatters`

| Tool                                       | Description                                                                                             |
|--------------------------------------------|---------------------------------------------------------------------------------------------------------|
| [`black`](https://black.readthedocs.io/)   | A Python code formatter that automatically reformats code to conform to a consistent style.             |
| [`isort`](https://pycqa.github.io/isort/ ) | A Python utility to sort imports alphabetically, and automatically separated into sections and by type. |

Make target: `make code-checks`

| Tool                                       | Description                                                                                             |
|--------------------------------------------|---------------------------------------------------------------------------------------------------------|
| [`black`](https://black.readthedocs.io/)   | A Python code formatter that automatically reformats code to conform to a consistent style.             |
| [`isort`](https://pycqa.github.io/isort/ ) | A Python utility to sort imports alphabetically, and automatically separated into sections and by type. |

Use code analysers like `pylint`, `mypy` and `flake8` to catch issues early. The `dev-template` repository provides predefined make targets to make the code analysis easy. Some examples of the these targets are

generators : Runs the ABCI docstring generator, copyright checker and API documentation generator
code-checks : Runs `pylint`, `mypy`, `vulture`, `flake8` and `darglint`

## Custom framework checks

In addition to the third-party tools above, the {{open_autonomy}} framework also comes with dedicated tools for analyzing the component packages:

`autonomy check-packages`
: Performs several consistency checks on the component packages to make sure there are no issues with the component configurations.

`autonomy analyse handlers`
: Performs an analysis of the handler definitions in the {{fsm_app}} skill packages.

`autonomy analyse dialogues`
: Performs an analysis of the dialogue definitions in the {{fsm_app}} packages.

`autonomy analyse service`
: Performs various checks on the service components to make sure it is ready for deployment.

# Testing

Unit testing
: The `valory/abstract_round_abci` skill packages come with the testing tools located in `packages/valory/skills/abstract_round_abci/test_tools` which you can use to write unit tests for your {{fsm_app}}.

Integration testing
: The `open-aea-test-autonomy` plugin provides several test classes which can be utilized for various Docker integration tests. Here are some examples of the base test classes:

    * `aea_test_autonomy.base_test_classes.BaseContractTest`: Comes with utilities required for testing a contract.
    * `aea_test_autonomy.base_test_classes.BaseGanacheContractTest`: Can be used for testing contracts on a local Ganache instance.
    * `aea_test_autonomy.base_test_classes. BaseRegistriesContractsTest`: Launches a local Hardhat node with pre-deployed Autonolas registries contracts image.

End-to-end testing
: The same plugin also provides tools for writing end to end tests for autonomous agents. The `aea_test_autonomy.base_test_classes.agents.BaseTestEnd2End` class provides an environment for testing agents end to end.

The open-autonomy framework also provides CLI tools for setting up and running the deployments locally. To run a service locally before putting it in a production environment use the development mode on the `autonomy deploy build` command. Follow [this guide](https://github.com/valory-xyz/autonolas-registries/blob/main/docs/running_with_custom_contracts.md) to include the custom contracts in the local hardhat deployment if you have any.