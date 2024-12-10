from web3 import Web3
from web3.middleware import SignAndSendRawMiddlewareBuilder
from eth_abi import encode

import os

w3 = Web3(Web3.HTTPProvider(os.environ['ETH_RPC_URL']))

acc = w3.eth.account.from_key(os.environ['AD_KEY'])
print(acc.address)

w3.middleware_onion.inject(SignAndSendRawMiddlewareBuilder.build(acc), layer=0)

contract = w3.eth.contract()
batch_size = 1000
unit = 10000
start_addr = 0x1234560000000000000000000000000000000000 + 500

addr_list = []
for i in range(batch_size):
     addr_list.append(hex(start_addr + i))
params = encode(['address[]', 'uint256[]'], [addr_list, [unit]*batch_size])
selector = bytes.fromhex('299f8170') # selector for batchDepositFor(address[],uint256[])

tx = w3.eth.send_transaction({
     "from": acc.address,
     "value": w3.to_wei(batch_size*unit, 'wei'),
     "to": "0x4200000000000000000000000000000000000800",
     "data": selector + params,
     "maxPriorityFeePerGas": 1,
})

print(tx.hex())

# http://142.132.154.16/tx/0xa3b8b660a1261ad4611320390f36e8eaa7374750bc0d806333d6f62daae8408a 500
# http://142.132.154.16/tx/0x47342bde9619c45c4042dbcaeeaeb14145cf52577c421b9a488a6f50e7017bab 1000