#! /bin/bash
echo ¨Running the aea with $(aea --version)
echo "Loading the $VALORY_APPLICATION configuration"
aea fetch $VALORY_APPLICATION --local --alias agent 
echo -n $AEA_KEY > agent/ethereum_private_key.txt
cd agent
aea install
aea build
aea run --aev
