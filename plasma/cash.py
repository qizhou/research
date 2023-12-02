# A simple demo to illustrate plasma cash
import hashlib

hash_func = lambda x: hashlib.sha256(x).digest()

class User:
    ids = 0
    
    @classmethod
    def newUser(cls):
        cls.ids += 1 # starting from 1, 0 is reserved for empty
        return User(cls.ids)
    
    def __init__(self, id):
        self.id = id

class PlasmaTx:
    # Simple tx structure without nonce, signature, etc
    @staticmethod
    def empty():
        return PlasmaTx(0, 0)

    def __init__(self, sender_id, receiver_id):
        self.sender_id = sender_id
        self.receiver_id = receiver_id

    def serialize(self):
        return int.to_bytes(self.sender_id, 4, "big") + int.to_bytes(self.receiver_id, 4, "big")

class PlasmaBlock:
    def __init__(self, tokens):
        self.txs = [PlasmaTx.empty()] * tokens

    def root(self):
        nodes = [hash_func(x.serialize()) for x in self.txs]
        while len(nodes) != 1:
            new_nodes = [hash_func(nodes[i * 2] + nodes[i * 2 + 1]) for i in range(len(nodes) // 2)]
            if len(nodes) % 2 == 1:
                new_nodes.append(nodes[-1])

            nodes = new_nodes
        return nodes[0]
    
    def getProof(self, idx):
        nodes = [hash_func(x.serialize()) for x in self.txs]
        proof = []
        while len(nodes) != 1:
            if idx % 2 == 0:
                if idx + 1 < len(nodes):
                    proof.append(nodes[idx + 1])
            else:
                proof.append(nodes[idx - 1])
            new_nodes = [hash_func(nodes[i * 2] + nodes[i * 2 + 1]) for i in range(len(nodes) // 2)]
            if len(nodes) % 2 == 1:
                new_nodes.append(nodes[-1])

            nodes = new_nodes
            idx = idx // 2
        return proof

    def verifyProof(self, root, idx, tx, proof):
        size = len(self.txs)
        node = hash_func(tx.serialize())
        i = 0
        while size != 1:
            if idx % 2 == 0:
                if idx + 1 < size:
                    node = hash_func(node + proof[i])
                    i = i + 1
                # else node = node
            else:
                node = hash_func(proof[i] + node)
                i = i + 1
            
            size = (size + 1) // 2
            idx = idx // 2
        return node == root

# Plasma contract deployed on L1
class PlasmaContract:
    def __init__(self):
        self.blocks = []  # maintained by operator, not contract
        self.tokens = 0
        self.block_hashes = []

    def deposit(self, user):
        # Create a single block
        self.tokens += 1
        block = PlasmaBlock(self.tokens)
        block.txs[-1] = PlasmaTx(user.id, user.id) # Genesis token tx
        self.blocks.append(block)
        self.block_hashes.append(block.root())
        print("Block {}: Deposited from user {} at token id {} with root {}".format(len(self.block_hashes)-1, user.id, self.tokens-1, self.block_hashes[-1].hex()))

def test_blockn(n):
    b = PlasmaBlock(n)
    for i in range(n):
        b.txs[i] = PlasmaTx(i + 1, i + 2)
    
    for i in range(n):
        assert b.verifyProof(b.root(), i, b.txs[i], b.getProof(i))

def test_block():
    test_blockn(1)
    test_blockn(2)
    test_blockn(3)
    test_blockn(10)
    test_blockn(11)
    test_blockn(12)
    test_blockn(13)
    test_blockn(14)
    test_blockn(15)


test_block()
a = User.newUser()
b = User.newUser()
print(a.id, b.id)

pc = PlasmaContract()
pc.deposit(a)
pc.deposit(b)