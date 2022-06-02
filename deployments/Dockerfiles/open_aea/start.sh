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
aea fetch $VALORY_APPLICATION --local --alias agent
cd agent
if [ "$AEA_KEY" == "" ];
then
    echo "No AEA key provided. Creating fresh."
    aea generate-key ethereum
else
    echo "AEA key provided."
    echo -n $AEA_KEY > ethereum_private_key.txt

aea generate-key cosmos

fi
if [ "$INSTALL" == "1" ];
then
    echo "Installing the necessary dependencies!"
    aea install && cd .. && aea delete agent
else
    echo "Running the AEA!"
    aea add-key ethereum
    (aea add-key cosmos --connection && aea issue-certificates --aev) || (echo "Failed to add cosmos key for connection" && exit 1)
    aea run --aev
fi
