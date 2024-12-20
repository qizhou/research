blob_gas_fee = 16965135
gas_price = 25 * 10 ** 9
eth_price = 4000
l2tx_size = 100
blobs_per_l1tx = 5
blob_size = 120000
blob_fee_size = 128 * 1024

l2txs_per_l1tx = blob_size * blobs_per_l1tx // l2tx_size
l1tx_cost = (eth_price * gas_price * 21000 + eth_price * blob_gas_fee * blob_size * blobs_per_l1tx) / 1e18
print("l1tx_cost {}, l1_per_byte_cost {}, l2txs_per_l1_tx {}, l2tx_cost {}".format(l1tx_cost, l1tx_cost / blob_size / blobs_per_l1tx, l2txs_per_l1tx, l1tx_cost / l2txs_per_l1tx))

# calldataGas*(l1BaseFee*16*l1BaseFeeScalar + l1BlobBaseFee*l1BlobBaseFeeScalar)/16e6

# minimum l1 fee scalar calculation
# calldataBytesInTx * 16 * l1BaseFee * l1BaseFeeScalar / 1e6 > 21000 * l1BaseFee
# blob_size * blobs_per_l1tx * 16 * l1BaseFeeScalar > 21000
scale = (10 ** 6)
minL1BaseFeeScalar = 21000 * scale / blob_size / blobs_per_l1tx / 16
print("minL1BaseFeeScalar", minL1BaseFeeScalar)

# minimum blob fee scalar calculation
# calldataBytesInTx * l1BlobBaseFee * l1BlobBaseFeeScalar / 1e6 > totalBlobFee
# blob_size * blobs_per_l1tx * l1BlobBaseFee * l1BlobBaseFeeScalar / 1e6 > blob_fee_size * blobs_per_l1tx * l1BlobBaseFee
# l1BlobBaseFeeScalar > 1e6 * blob_fee_size / blob_size
minL1BlobBaseFeeScalar = scale * blob_fee_size / blob_size
print("minL1BlobBaseFeeScalar", minL1BlobBaseFeeScalar)

# custom gas token
gt_price = 0.01
gt_gas_price = 100e9
l2_exec_fee = gt_price * gt_gas_price * 21000 / 1e18
calldata_gas = 16 * 100
l1_exec_fee = calldata_gas * minL1BaseFeeScalar * 16 * gas_price / 16e6 * eth_price / 1e18
l1_data_fee = calldata_gas * minL1BlobBaseFeeScalar * blob_gas_fee / 16e6 * eth_price / 1e18
print("l2 exec cost {}, l1 exec cost {}, l1 data cost {}, total cost {}".format(l2_exec_fee, l1_exec_fee, l1_data_fee, l2_exec_fee + l1_exec_fee + l1_data_fee))