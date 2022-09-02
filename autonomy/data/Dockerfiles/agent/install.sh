#! /bin/bash

if [ "$AEA_AGENT" == "" ];
then
    echo "No Application specified!"
    exit 1
fi

echo Running the aea with $(aea --version)

echo "Loading $AEA_AGENT"
aea fetch $AEA_AGENT --alias agent
cd agent

echo "Installing the necessary dependencies!"
aea install
cd ..