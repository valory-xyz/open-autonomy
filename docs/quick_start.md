# Quick Start

The purpose of this quick start is to get you up and running with the `open-autonomy` framework for agent service development as quickly as possible.

1. Setup the environment
```
touch Pipfile && pipenv --python 3.10 && pipenv shell
```

2. Install open autonomy
```
pip install open-autonomy
pip install open-aea-ledger-ethereum
pip install open-aea-cli-ipf
```

3. Get packages 
```
svn checkout  https://github.com/valory-xyz/open-autonomy/trunk/packages packages 
```

4. Build and install your agent
```
cd hello_world
aea generate-key ethereum
aea add-key ethereum
aea install
```

5. Setup a tendermint testnet
## Prior to running we must setup a tendermint testnet;

Starting AEA 'hello_world' in 'async' mode...
open /home/tom/.tendermint/data/priv_validator_state.json: no such file or directory


6. Run your agent.

```bash
aea run
```
