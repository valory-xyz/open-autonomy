#! /bin/bash
if [ "$DEBUG" == "1" ];
then
    echo "Debugging..."
    while true; do echo "waiting" ; sleep 2; done
fi
echo ¨Running the aea with $(aea --version)
if [ "$VALORY_APPLICATION" == "" ];
then
    echo "No Application specified!"
    exit 1
fi

echo "Loading $VALORY_APPLICATION"
aea fetch $VALORY_APPLICATION --local --alias agent
cd agent

export FILE=/agent_key/ethereum_private_key.txt
if [ -f "$FILE" ]; then
    echo "AEA key provided. Copying to agent."
    cp $FILE .
else
    echo "No AEA key provided. Creating fresh."
    aea generate-key ethereum
fi
if [ "$INSTALL" == "1" ];
then
    echo "Installing the necessary dependencies!"
    aea install && cd .. && aea delete agent
else
    if [ "$AEA_PASSWORD" != "" ];
    then
        echo "Running the aea with a password!"
        aea add-key ethereum --password $AEA_PASSWORD
        aea run --aev --password $AEA_PASSWORD
    else
        echo "Running the aea without a password!"
        aea add-key ethereum
        aea run --aev
    fi
fi
