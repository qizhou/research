export ETH_RPC_URL=https://mainnet.infura.io/v3/f077d0002b234ba3ae0ab121d2c9f604
#export ETH_RPC_URL=https://sepolia.optimism.io

#echo "L1CrossDomainMessengerProxy 0x25ace71c97B33Cc4729CF772ae268934F7ab5fA1 owner()"
#cast call 0x25ace71c97B33Cc4729CF772ae268934F7ab5fA1 'owner()' -r $RPC

function find_owner() {
  ADDR=$(cast call $SYS_CONFIG $1 | cut -b 1,2,27-66)
  echo $1 $ADDR $2
  cast call $ADDR $2 | cut -b 1,2,27-66
}

SYS_CONFIG=0x229047fed2591dbec1eF1118d64F7aF3dB9EB290

echo "SystemConfigProxy $SYS_CONFIG admin()"
cast call $SYS_CONFIG 'admin()' | cut -b 1,2,27-66

GAME_FACTORY=$(cast call $SYS_CONFIG 'disputeGameFactory()' | cut -b 1,2,27-66)
echo Game Factory $GAME_FACTORY
i=0
while [[ true ]]; do
  GAME_ADDR=$(cast call $GAME_FACTORY 'gameImpls(uint32)' $i)
  if [[ $GAME_ADDR == 0x0000000000000000000000000000000000000000000000000000000000000000 ]]; then
    break
  fi
  echo Game Impl $i is $GAME_ADDR
  i=$((i+1))
done

find_owner 'disputeGameFactory()' 'admin()'
find_owner 'optimismPortal()' 'admin()'
find_owner 'l1StandardBridge()' 'getOwner()'