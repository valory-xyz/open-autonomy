export tendermint_validators=$1
python3 create_env.py $1
make localnet-start