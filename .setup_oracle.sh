swarm deploy build image valory/oracle_hardhat --dev
swarm deploy build image valory/oracle_hardhat --dependencies
swarm deploy build deployment valory/oracle_hardhat deployments/keys/hardhat_keys.json --force --dev
