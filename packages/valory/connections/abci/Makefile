# Origin
version_branch = v0.34.19
tendermint = https://raw.githubusercontent.com/tendermint/tendermint/$(version_branch)

# Outputs
tmabci = protos/tendermint/abci/types.proto
tmtypes =  protos/tendermint/types/types.proto
tmpubkey = protos/tendermint/crypto/keys.proto
tmproof =  protos/tendermint/crypto/proof.proto
tmparams = protos/tendermint/types/params.proto
tmversions =  protos/tendermint/version/types.proto
tmvalidator = protos/tendermint/types/validator.proto

# You *only* need to run this to rebuild protobufs from the tendermint source
update-proto:
	curl $(tendermint)/proto/tendermint/abci/types.proto > $(tmabci)
	curl $(tendermint)/proto/tendermint/crypto/keys.proto > $(tmpubkey)
	curl $(tendermint)/proto/tendermint/crypto/proof.proto > $(tmproof)
	curl $(tendermint)/proto/tendermint/types/params.proto > $(tmparams)
	curl $(tendermint)/proto/tendermint/types/types.proto > $(tmtypes)
	curl $(tendermint)/proto/tendermint/types/validator.proto > $(tmvalidator)
	curl $(tendermint)/proto/tendermint/version/types.proto > $(tmversions)
	curl $(tendermint)/version/version.go | grep -F -eTMVersionDefault -eABCISemVer > version.txt
	python scripts/genproto.py
