#!/usr/bin/bash

if [ "$DEBUG" == "1" ];
then
    while true; do echo "waiting" ; sleep 2; done
fi

if [ "$CLUSTERED" == "1" ];
then
    AGENT_ID=$(cat /etc/hostname | grep -Eo '[0-9]{1,4}' | head -n 1)
    echo "configuring $AGENT_ID for cluster"
    cp -r /build/configs/* ../configure_agents
    sudo chown -R  $(whoami) /build/configs
    bash ../configure_agents/abci"${AGENT_ID}".sh &&\
     python3 -m aea.cli -v INFO run
else
    echo "configuring ${ID}"
    bash ../configure_agents/abci"${ID}".sh &&\
     python3 -m aea.cli -v INFO run
fi
