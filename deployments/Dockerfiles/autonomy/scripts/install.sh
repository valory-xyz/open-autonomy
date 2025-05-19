#! /bin/bash

if [ "$AEA_AGENT" == "" ];
then
    echo "No Application specified!"
    exit 1
fi

echo Running the aea with $(aea --version)

echo "Loading $AEA_AGENT"
cd /home
aea fetch $AEA_AGENT --alias agent || exit 1
cd agent

echo "Building the deployments host dependencies."
pip install --upgrade pip
aea build || exit 1
echo "Successfully built the host dependencies."

echo "Installing the necessary python dependencies!"
aea install --timeout 21600 $EXTRA_DEPENDENCIES || exit 1
echo "Successfully Installed the python dependencies."

echo "Done."
cd ..
