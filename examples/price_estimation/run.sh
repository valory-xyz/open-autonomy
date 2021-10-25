#!/usr/bin/env sh


if [ "$CLUSTERED" == "1" ];
then
    ../configure_agents/abci_kube.sh &&\
     python3 -m aea.cli -v DEBUG run
else
    AGENT_ID=$(echo /etc/hostname | grep -Eo '[0-9]{1,4}')
    ../configure_agents/abci"${AGENT_ID}".sh &&\
     python3 -m aea.cli -v DEBUG run
fi
