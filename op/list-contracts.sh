
SYS_CONFIG=0x229047fed2591dbec1eF1118d64F7aF3dB9EB290

function print_contract() {
    echo $1: $(cast call $SYS_CONFIG $1\(\) | cut -b 1,2,27-66)
}

print_contract disputeGameFactory
print_contract optimismPortal
print_contract batcherHash
print_contract batchInbox
print_contract l1StandardBridge
