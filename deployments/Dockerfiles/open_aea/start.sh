#! /bin/bash
if [ "$DEBUG" == "1" ];
then
    cowsay "Debugging..."
    while true; do echo "waiting" ; sleep 2; done
fi
echo ¨Running the aea with $(aea --version)
if [ "$VALORY_APPLICATION" == "" ];
then
    echo "No Application specified!"
    exit 1
fi

cowsay "Loading $VALORY_APPLICATION"
aea fetch $VALORY_APPLICATION --local --alias agent
cd agent
if [ "$AEA_KEY" == "" ];
then
    cowsay "No AEA key provided. Creating fresh."
    aea generate-key ethereum
else
    cowsay "AEA key provided."
    echo -n $AEA_KEY > ethereum_private_key.txt

fi
aea add-key ethereum
aea install
aea run --aev
