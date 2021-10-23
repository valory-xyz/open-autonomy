#!/usr/bin/env sh

AGENT_ID=$1
../configure_agents/"${AGENT_ID}".sh &&\
 python3 -m aea.cli -v DEBUG run
