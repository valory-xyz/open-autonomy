
if [["$(uname -m)" == "amd64"]]
then
    arch="amd64"
else
    arch="arm64"
fi

curl -L https://github.com/tendermint/tendermint/releases/download/v${TENDERMINT_VERSION}/tendermint_${TENDERMINT_VERSION}_linux_${$arch}.tar.gz > tendermint.tar.gz
tar -xf tendermint.tar.gz
mv tendermint /usr/bin
rm -fr tendermint.tar.gz
