
SYS_CONFIG=0x229047fed2591dbec1eF1118d64F7aF3dB9EB290

echo disputeGameFactory: $(cast call $SYS_CONFIG 'disputeGameFactory()' | cut -b 1,2,27-66)
echo optimismPortal: $(cast call $SYS_CONFIG 'optimismPortal()' | cut -b 1,2,27-66)

