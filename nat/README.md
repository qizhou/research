# A Minimum Python Code to Demonstrate Rendezvous Protocol

## Background:
- https://github.com/ethereum/portal-network-specs/issues/144
- https://github.com/ethereum/devp2p/issues/207
- https://blog.ipfs.tech/2022-01-20-libp2p-hole-punching/

## How to Run
You need to prepare three nodes:
- Rendezvous: a node with a public address (`pub_addr`)
- Receiver: a node behind NAT
- Initiator: a node behind NAT and wants to connect the receiver

Steps:
1. `python3 rendezvous.py`
2. `python3 receiver.py ${pub_addr}`.  If the node runs successfully, the rendezvous will print the NATed address of the node.
3. `python3 initator.py ${pub_addr}`.  If the node runs successfully, the rendezvous will print the NATed address of the node.

After running these nodes, the receiver and the initiator will print the repeated messages received from another node.
