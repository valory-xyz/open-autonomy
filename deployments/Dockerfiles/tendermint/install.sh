# Install architecture specific version of tendermint

echo Fetching binaries for $(uname -m)
if [[ "$(uname -m)" == "aarch64" ]]
then
    curl -L https://github.com/tendermint/tendermint/releases/download/v0.34.19/tendermint_0.34.19_linux_arm64.tar.gz > tendermint.tar.gz
elif [[ "$(uname -m)" == "armv7l" ]]
then
    curl -L https://github.com/tendermint/tendermint/releases/download/v0.34.19/tendermint_0.34.19_linux_arm64.tar.gz > tendermint.tar.gz
else
    curl -L https://github.com/tendermint/tendermint/releases/download/v0.34.19/tendermint_0.34.19_linux_amd64.tar.gz > tendermint.tar.gz
fi

tar -xvf tendermint.tar.gz
mv tendermint /usr/bin
rm -fr tendermint.tar.gz

/usr/bin/tendermint --help