# Fjord (4844) fee
# https://github.com/ethstorage/op-geth/blob/5f7ebba8a124ae87225f81a1a9c827f8a534f2b7/core/types/rollup_cost.go#L120

UINT32_MAX = (1 << 32) - 1
UINT64_MAX = (1 << 64) - 1


def calldata_load(calldata, off):
    return int.from_bytes(calldata[off:off+32], "big")


class L1BlockInfo:
    def __init__(self, calldata):
        self.seq = calldata_load(calldata, 4) >> 128 & (UINT64_MAX)
        self.blobBaseFeeScalar = calldata_load(calldata, 4) >> (128 + 64) & (UINT32_MAX)
        self.baseFeeScalar = calldata_load(calldata, 4) >> (128 + 32 + 64) & (UINT32_MAX)
        self.l1Number = calldata_load(calldata, 20) >> 128
        self.baseFee = calldata_load(calldata, 36)
        self.blobBaseFee = calldata_load(calldata, 68)
        self.l1BlockHash = calldata_load(calldata, 100).to_bytes(32, "big")
        self.batcher = calldata_load(calldata, 132).to_bytes(32, "big")

    def dataCostEcotone(self, calldataGas):
        #   calldataGas*(l1BaseFee*16*l1BaseFeeScalar + l1BlobBaseFee*l1BlobBaseFeeScalar)/16e6
        return calldataGas * (self.baseFee * 16 * self.baseFeeScalar + self.blobBaseFee * self.blobBaseFeeScalar) // 16 // (10 ** 6)


def print_l1block_info(l1blockInfo):
    print("seq", l1blockInfo.seq)
    print("blobBaseFeeScalar", l1blockInfo.blobBaseFeeScalar),
    print("baseFeeScalar", l1blockInfo.baseFeeScalar)
    print("l1Number", l1blockInfo.l1Number)
    print("base fee", l1blockInfo.baseFee)
    print("blob base fee", l1blockInfo.blobBaseFee)
    print("l1 blockhash", l1blockInfo.l1BlockHash.hex())
    print("batcher", l1blockInfo.batcher.hex())

# block 125777783
calldata = bytes.fromhex("440a5e200000146b000f79c500000000000000000000000066f2481b00000000013da93b0000000000000000000000000000000000000000000000000000000283f4baef000000000000000000000000000000000000000000000000000000000000000118f2d8074b61603abd467a43684f8d6e894fc2d35a7286f39b8ecb1afeafd1000000000000000000000000006887246668a3b87f54deb3b94ba47a6f63f32985")
# block 125777784
calldata1 = bytes.fromhex("440a5e200000146b000f79c500000000000000010000000066f2481b00000000013da93b0000000000000000000000000000000000000000000000000000000283f4baef000000000000000000000000000000000000000000000000000000000000000118f2d8074b61603abd467a43684f8d6e894fc2d35a7286f39b8ecb1afeafd1000000000000000000000000006887246668a3b87f54deb3b94ba47a6f63f32985")
print_l1block_info(L1BlockInfo(calldata))
print_l1block_info(L1BlockInfo(calldata1))

print(L1BlockInfo(calldata).dataCostEcotone(16 * 5))
