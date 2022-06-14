# Price Oracle - Running the Demo

This demo consists of a network of AEAs, implemented as {{fsm_app}}s reaching
Byzantine fault-tolerant consensus, that work as an Oracle to jointly agree on a price estimate
of the current Bitcoin price in US dollars. The underlying
consensus mechanism for the {{fsm_app}} is powered by Tendermint.

## Requirements

In addition to the general requirements presented for setting up the {{open_autonomy}} framework, make sure that you have installed on your machine:

- [Docker Engine](https://docs.docker.com/engine/install/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- [Kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation)
- Skaffold

## Running the Local Demo

To set up the network:

```bash
export VERSION=0.1.0
autonomy deploy build image valory/oracle_hardhat --dependencies
autonomy deploy build image valory/oracle_hardhat
autonomy deploy build deployment valory/oracle_hardhat deployments/keys/hardhat_keys.json --force
```

If you're working under GNU/Linux, you also need to create and change permissions for the following directories:
```bash
mkdir -p abci_build/persistent_data/logs
mkdir -p abci_build/persistent_data/venvs
sudo chown -R 1000:1000 -R abci_build/persistent_data/logs
sudo chown -R 1000:1000 -R abci_build/persistent_data/venvs
```
And finally launch the demo:
```
cd abci_build/
docker-compose up --force-recreate -t 600 --remove-orphans
```

This will spawn:

- A network of 4 Tendermint nodes, each one trying to connect to
  a separate ABCI application instance;
- 4 AEAs, each one running an instance of the ABCI application,
  and a finite-state machine behaviour to interact with
  the round phases.

The following is the output of a single AEA (you can use `docker logs {container_id} --follow`):
```
info: Building package (connection, valory/abci:0.1.0)...
info: Running command '/usr/bin/python3 check_dependencies.py /home/ubuntu/price_estimation/.build/connection/valory/abci'...
info: Command '/usr/bin/python3 check_dependencies.py /home/ubuntu/price_estimation/.build/connection/valory/abci' succeded with output:
info: Warning:  'tendermint' is required by the abci connection, but it is not installed, or it is not accessible from the system path.
Build completed!
warning: [price_estimation] The kwargs={'consensus': OrderedDict([('max_participants', 4)]), 'convert_id': 'USD', 'currency_id': 'BTC', 'initial_delay': 5.0, 'tendermint_url': 'http://node0:26657'} passed to params have not been set!
warning: [price_estimation] The kwargs={'api_key': None, 'source_id': 'coingecko'} passed to price_api have not been set!
    _     _____     _
   / \   | ____|   / \
  / _ \  |  _|    / _ \
 / ___ \ | |___  / ___ \
/_/   \_\|_____|/_/   \_\

v1.0.2

Starting AEA 'price_estimation' in 'async' mode...
info: [price_estimation] ABCI Handler: setup method called.
info: [price_estimation] Start processing messages...
info: [price_estimation] Entered in the 'registration' behaviour state
info: [price_estimation] transaction signing was successful.
info: [price_estimation] 'registration' behaviour state is done
info: [price_estimation] Entered in the 'observation' behaviour state
info: [price_estimation] Got observation of BTC price in USD: 43876.0
info: [price_estimation] transaction signing was successful.
info: [price_estimation] 'observation' behaviour state is done
info: [price_estimation] Entered in the 'estimate' behaviour state
info: [price_estimation] Using observations [44217.09, 44406.04, 44189.115714582986, 43876.0] to compute the estimate.
info: [price_estimation] Got estimate of BTC price in USD: 44172.06142864574
info: [price_estimation] transaction signing was successful.
info: [price_estimation] 'estimate' behaviour state is done
info: [price_estimation] Consensus reached on estimate: 44172.06142864574
```

From the logs, you can see the different behaviours of the
finite-state machine behaviour: `registration`, `observation`,
and `estimate` states. Moreover,
you can see that the observation of this agent
has been considered in the set of observation shared
among all the AEAs (`Using observations: ...`).
Finally, the consensus is reached among all the AEAs
on the BTC/USD estimate `44172.06142864574`,
which is a simple average of the set of observations.

An analogous output is produced by other AEAs.
Here it is reported the output of another AEA
that participated in the same round:

```
info: Building package (connection, valory/abci:0.1.0)...
info: Running command '/usr/bin/python3 check_dependencies.py /home/ubuntu/price_estimation/.build/connection/valory/abci'...
info: Command '/usr/bin/python3 check_dependencies.py /home/ubuntu/price_estimation/.build/connection/valory/abci' succeded with output:
info: Warning:  'tendermint' is required by the abci connection, but it is not installed, or it is not accessible from the system path.
Build completed!
warning: [price_estimation] The kwargs={'consensus': OrderedDict([('max_participants', 4)]), 'convert_id': 'USD', 'currency_id': 'BTC', 'initial_delay': 5.0, 'tendermint_url': 'http://node1:26657'} passed to params have not been set!
warning: [price_estimation] The kwargs={'api_key': '2142662b-985c-4862-82d7-e91457850c2a', 'source_id': 'ftx'} passed to price_api have not been set!
    _     _____     _
   / \   | ____|   / \
  / _ \  |  _|    / _ \
 / ___ \ | |___  / ___ \
/_/   \_\|_____|/_/   \_\

v1.0.2

Starting AEA 'price_estimation' in 'async' mode...
info: [price_estimation] ABCI Handler: setup method called.
info: [price_estimation] Start processing messages...
info: [price_estimation] Entered in the 'registration' behaviour state
info: [price_estimation] transaction signing was successful.
info: [price_estimation] 'registration' behaviour state is done
info: [price_estimation] Entered in the 'observation' behaviour state
info: [price_estimation] Got observation of BTC price in USD: 44189.115714582986
info: [price_estimation] transaction signing was successful.
info: [price_estimation] 'observation' behaviour state is done
info: [price_estimation] Entered in the 'estimate' behaviour state
info: [price_estimation] Using observations [44217.09, 44406.04, 44189.115714582986, 43876.0] to compute the estimate.
info: [price_estimation] Got estimate of BTC price in USD: 44172.06142864574
info: [price_estimation] transaction signing was successful.
info: [price_estimation] 'estimate' behaviour state is done
info: [price_estimation] Consensus reached on estimate: 44172.06142864574
```
