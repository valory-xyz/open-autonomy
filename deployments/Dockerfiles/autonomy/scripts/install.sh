#! /bin/bash

if [ "$AEA_AGENT" == "" ];
then
    echo "No Application specified!"
    exit 1
fi

echo Running the aea with $(aea --version)

echo "Loading $AEA_AGENT"
aea fetch $AEA_AGENT --alias agent || exit 1
cd agent

echo "Building the deployments host dependencies."
aea build || exit 1
echo "Successfully built the host dependencies."

echo "Installing the necessary python dependencies!"
aea install --timeout 600 $EXTRA_DEPENDENCIES || exit 1
echo "Successfully Installed the python dependecies."

echo "Done."
cd ..
