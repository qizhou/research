Run Fault Proof on Devnet
=========================

# Setup Helper Functions
```
function json_to_env() {
  for key in $( jq -r 'to_entries|map("\(.key)")|.[]' $1 ); do
    skey=$(echo $key | sed -r 's/([a-z0-9])([A-Z])/\1_\L\2/g' | sed -e 's/\(.*\)/\U\1/')
    value=$(jq \.$key $1 | tr -d \")
    echo $skey=$value
    export $skey=$value
  done
}

function setup_devnet_prestate() {
  cd $OP_HOME
  cp .devnet/rollup.json op-program/chainconfig/configs/901-rollup.json
  cp .devnet/genesis-l2.json op-program/chainconfig/configs/901-genesis-l2.json
  cd op-program
  make reproducible-prestate
}
```

# Download Repo

```
git clone https://github.com/ethstorage/optimism.git
cd optimism
git checkout fp-devnet
OP_HOME=$(realpath .)
```

# Run Devnet
(Note: the devnet intentionally disables op-proposer and op-challenger)

```make devnet-up```

## (Optional) Restart a Clean Devnet

```
make devnet-down
make devnet-clean
```

# Deploy Fault Proof with Devnet Absolute Prestate

## Build op-program with Devnet Config

```
$ setup_devnet_prestate
...
Cannon Absolute prestate hash:
0x0384fd1b3e1f41288e21b315f67a691c24bf420d7fb53f9b41f6cad80dc78a50
```

## Verify Without Cannon
```
$ make verify-devnet
...
t=2024-10-15T17:46:52+0000 lvl=info msg="Validating claim" head=0x0a33510461b206f7e178d152809477bdb7336399a5f12d6dd71f7b7de58bf8ca:397 output=0x73b217962cdcdf5b878389222d79ff5c07b0ec8c7749d5bed8ead353836e7faa claim=0x73b217962cdcdf5b878389222d79ff5c07b0ec8c7749d5bed8ead353836e7faa
```
which will output the claim (output root) and its l2 block number

## Update Config

Replace the prestate hash / genesis block / genesis output root in `deploy-config/devnetL1.json`.

## Deploy Fault Proof Implementations

```
export IMPL_SALT=$(openssl rand -hex 32)
DEPLOY_CONFIG_PATH=deploy-config/devnetL1.json DEPLOYMENT_INFILE=deployments/devnetL1/.deploy forge script scripts/deploy/Deploy.s.sol:Deploy --sig deployFaultProofImplementations --private-key 0x2a871d0798f97d79848a013d4936a73bf4cc922c825d33c1cf7073dff6d409c6 --rpc-url http://localhost:8545
```

## Verify Deployments
```
json_to_env $OP_HOME/.devnet/addresses.json
FP_IMPL=$(cast call $DISPUTE_GAME_FACTORY_PROXY 'gameImpls(uint32)' 0 | cut -b 1,2,27-66 )
echo "Fault Proof Impl" $FP_IMPL
cast call $FP_IMPL 'absolutePrestate()'
ASR=$(cast call $FP_IMPL 'anchorStateRegistry()' | cut -b 1,2,27-66)
echo "Anchor State Registry" $ASR
echo "Anchor root" $(cast call $ASR 'anchors(uint32)' 0)
```

Make sure the prestate and anchor output root are correct.

# Run op-proposer & op-challenger

```
op-proposer/bin/op-proposer --l1-eth-rpc http://localhost:8545  --rollup-rpc http://localhost:7545 --proposal-interval 60s --poll-interval 1s --num-confirmations 1 --private-key 0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d --game-factory-address $DISPUTE_GAME_FACTORY_PROXY --rpc.port 10545

op-challenger/bin/op-challenger --l1-eth-rpc http://localhost:8545 --l1-beacon http://localhost:5052 --l2-eth-rpc http://localhost:9545 --rollup-rpc http://localhost:7545 --datadir /tmp/op-chg-db --cannon-server op-program/bin/op-program --cannon-bin cannon/bin/cannon --cannon-prestate $(realpath op-program/bin/prestate.bin.gz) --private-key 0x47e179ec197488593b187f80a00eb0da91f1b9d0b13f8733639f19c30a34926a --cannon-rollup-config $(realpath op-program/chainconfig/configs/901-rollup.json) --cannon-l2-genesis $(realpath op-program/chainconfig/configs/901-genesis-l2.json) --game-factory-address $DISPUTE_GAME_FACTORY_PROXY --trace-type cannon
```

# Verify with op-challenger and cannon
```
op-challenger/bin/op-challenger run-trace --l1-eth-rpc http://localhost:8545 --l1-beacon http://localhost:5052 --l2-eth-rpc http://localhost:9545 --rollup-rpc http://localhost:7545 --datadir /tmp/op-chg-db --cannon-server op-program/bin/op-program --cannon-bin cannon/bin/cannon --cannon-prestate $(realpath op-program/bin/prestate.bin.gz) --private-key 0x47e179ec197488593b187f80a00eb0da91f1b9d0b13f8733639f19c30a34926a --cannon-rollup-config $(realpath op-program/chainconfig/configs/901-rollup.json) --cannon-l2-genesis $(realpath op-program/chainconfig/configs/901-genesis-l2.json) --game-factory-address $DISPUTE_GAME_FACTORY_PROXY --trace-type cannon
```

# Do something bad
## With wrong prestate hash (or rollup config)
## With wrong anchor output root
