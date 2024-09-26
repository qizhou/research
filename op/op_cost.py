l1BlobBaseFee = 1
l1BaseFee = 25.286736166 * 10 ** 9
l1BaseFeeScalar = 5227
l1blobBaseFeeScalar = 1014213
# calldataGas*(l1BaseFee*16*l1BaseFeeScalar + l1BlobBaseFee*l1BlobBaseFeeScalar)/16e6
calldataGas = 100 * 16 # minimim calldataGas
print("l1 exec cost", calldataGas*l1BaseFee*16*l1BaseFeeScalar/16e6)
print("l1 data cost", calldataGas*l1BlobBaseFee*l1blobBaseFeeScalar/16e6)
print("l1 total cost", calldataGas*(l1BaseFee*16*l1BaseFeeScalar + l1BlobBaseFee*l1blobBaseFeeScalar)/16e6)