#! /bin/bash
if [ "$DEBUG" == "1" ];
then
    echo "Debugging..."
    while true; do echo "waiting" ; sleep 2; done
fi
echo Running the aea with $(aea --version)
if [ "$VALORY_APPLICATION" == "" ];
then
    echo "No Application specified!"
    exit 1
fi

echo "Loading $VALORY_APPLICATION"
aea fetch $VALORY_APPLICATION --alias agent
cd agent

export FILE=/agent_key/ethereum_private_key.txt
if [ -f "$FILE" ]; then
    echo "AEA key provided. Copying to agent."
    cp $FILE .
else
    echo "No AEA key provided. Creating fresh."
    if [ "$AEA_PASSWORD" != "" ];
    then
        echo "Generating the fresh key with a password!"
        aea generate-key ethereum --password $AEA_PASSWORD
    else
        echo "Generating the fresh key without a password!"
        aea generate-key ethereum
    fi
fi
if [ "$INSTALL" == "1" ];
then
    echo "Installing the necessary dependencies!"
    aea install && cd .. && aea delete agent
else
    if [ "$AEA_PASSWORD" != "" ];
    then
        echo "Running the aea with a password!"
        aea generate-key cosmos --connection --password $AEA_PASSWORD
        aea add-key cosmos --connection --password $AEA_PASSWORD || (echo "Failed to generate the cosmos key needed for libp2p connection" && exit 1)
        aea add-key ethereum --password $AEA_PASSWORD
        aea issue-certificates --password $AEA_PASSWORD --aev || (echo "Failed to add cosmos key needed for libp2p connection" && exit 1)
        aea run --aev --password $AEA_PASSWORD
    else
        echo "Running the aea without a password!"
        aea generate-key cosmos --connection
        aea add-key cosmos --connection || (echo "Failed to generate the cosmos key needed for libp2p connection" && exit 1)
        aea add-key ethereum
        aea issue-certificates --aev || (echo "Failed to add cosmos key needed for libp2p connection" && exit 1)
        aea run --aev
    fi
fi
