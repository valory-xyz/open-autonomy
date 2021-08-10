# ABCI Price Estimation with AEAs

This demo is about a network of AEAs reaching 
Byzantine fault-tolerant consensus, powered by Tendermint, 
on a price estimate of Bitcoin price in US dollars.

## Introduction

The estimate is an average of a set of observations
on the Bitcoin price coming from different sources,
e.g. CoinMarketCap, CoinGecko, Binance and Coinbase.
Each AEA shares an observation from one of the sources above
by committing it to a temporary blockchain made with Tendermint.
Once all the observation are settled, each AEA
runs a script to aggregate the observations to compute an estimate,
and we say that the consensus is reached when one estimate
reaches 2/3 of the total voting power committed
on the temporary blockchain.
Alongside the finite-state machine behaviour, the AEAs runs
an ABCI application instance which receives all the updates from the 
underlying Tendermint network.

A round of consensus breaks down in four steps:

- Registration phase: the application accepts registrations
    from AEAs to join the round of consensus, up to a configured 
    maximum number of participants (in the demo, this limit is 4);
    once this threshold is hit ("registration threshold"), 
    the round goes to the _collect-observation_ phase.
- Collect-observation phase: the application accepts 
    observations, only one per agent,
    of the target quantity to estimate from only the AEAs
    that joined this round. Once all the AEAs have submitted their
    observations, 
    and the list of observations are replicated among the 
    different ABCI applications instances, the round goes to the _consensus_ phase
- Consensus phase: the application waits for votes on 
    estimates. The participants are supposed to run the same script
    to aggregate the set of observations.
    Once the same estimate receives a number of votes greater or equal than
    2/3 of the total voting power, the consensus is reached.
- Consensus-reached phase: the application in this phase still accepts votes,
    but they can't affect the consensus reached due to the quorum requirements.
    At this point, each AEA has a local copy of the estimate, replicated
    by the Tendermint network.

## Preliminaries

Make sure you have installed on your machine:

- [Docker Engine](https://docs.docker.com/engine/install/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Run

To set up the network:

```
make localnet-start
```

This will spawn:
- a network of 4 Tendermint nodes, each one trying to connect to
  a separate ABCI application instance;
- 4 AEAs, each one running an instance of the ABCI application,
  and a finite-state machine behaviour to interact with
  the round phases.

The following is the output of a single AEA:
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
warning: [price_estimation] The kwargs={'api_key': '2142662b-985c-4862-82d7-e91457850c2a', 'source_id': 'coinmarketcap'} passed to price_api have not been set!
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
