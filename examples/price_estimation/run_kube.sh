#!/usr/bin/env sh
echo -n $AGENT_KEY > ethereum_private_key.txt
python3 -m aea.cli run
