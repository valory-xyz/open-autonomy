# Valory Application Deployment

Tooling has been provided to allow for the automatic generation of deployments.

Valory application deployments can be built on the fly.


```bash
[I] (consensus-algorithms) tom@gefion~/D/c/v/consensus-algorithms> python deployments/create_deployment.py --help
usage: create_deployment.py [-h] [-ct] [-type {kubernetes,docker-compose}] -app {valory/counter:0.1.0,valory/price_estimation_deployable:0.1.0,valory/apy_estimation:0.1.0} [-n NUMBER_OF_AGENTS] [-b] [-dsc] [-doc] -net {hardhat,ropsten}

Generic Deployment Generator for Valory Stack.

optional arguments:
  -h, --help            show this help message and exit

Deployment Targets:
  -ct, --tendermint_configuration
                        Run to produce build step for tendermint validator nodes.
  -type {kubernetes,docker-compose}, --type_of_deployment {kubernetes,docker-compose}
                        The underlying deployment mechanism to generate for.
  -app {valory/counter:0.1.0,valory/price_estimation_deployable:0.1.0,valory/apy_estimation:0.1.0}, --valory_application {valory/counter:0.1.0,valory/price_estimation_deployable:0.1.0,valory/apy_estimation:0.1.0}
                        The Valory Agent Stack to be deployed.

deployment_parameters:
  -n NUMBER_OF_AGENTS, --number_of_agents NUMBER_OF_AGENTS
  -b, --copy_to_build
  -dsc, --deploy_safe_contract
  -doc, --deploy_oracle_contract
  -net {hardhat,ropsten}, --network {hardhat,ropsten}
                        Network to be used for deployment

```

Once the script is run, a build configuration will be output to;

deployments/build/$BUILD.yaml

This can then be launched using the appropriate tool.


## Building Images

Conceptually, the image to be used within a deployment should contain all required dependencies and packages.

Configuration of containers and agents is done via environment variables.




```python

```
