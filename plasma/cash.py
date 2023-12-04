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
        self.tokens = dict()  # list of tokens owned by the user
        self.new_tokens = dict()

    def receive(self, protocol, token_id, proof_history):
        # Given protocol and the proof_history from last block to deposit, check whether
        # 1. the tx history proof is correct
        # 2. the tx history is correct
        # 3. the last tx in the last block is sent to the user
        # 4. the first tx is deposit tx
        owner_id = self.id
        for i, h in enumerate(reversed(proof_history)):
            tx, proof = h

            assert protocol.blocks[-(i+1)].verifyProof(protocol.block_hashes[-(i+1)], token_id, tx, proof)
            if tx.receiver_id == 0 and tx.sender_id == 0:
                continue

            assert tx.receiver_id == owner_id
            owner_id = tx.sender_id
        
        # check if the first tx is deposit tx
        if len(proof_history) != len(protocol.blocks):
            assert len(protocol.blocks[-len(proof_history)].txs) == len(protocol.blocks[-len(proof_history)-1].txs) + 1

    def addToken(self, token_id, proof_history):
        # Add a token with previous history of sender (if deposit, then it is null)
        assert not token_id in self.new_tokens
        self.new_tokens[token_id] = proof_history

    def notifyNewBlock(self, protocol):
        # TODO: check block no == user block no + 1
        for k, v in self.new_tokens.items():
            self.tokens[k] = v

        for token_id, proof_history in self.tokens.items():
            proof_history.append((protocol.blocks[-1].txs[token_id], protocol.blocks[-1].getProof(token_id)))
            # NOTE, in the following case, the user will withdraw
            # 1, (data unavailable) operator may not share block and proof
            # 2, (invalid block) the block added by the operator is invalid
            if token_id in self.new_tokens:
                self.receive(protocol, token_id, proof_history)
            elif not protocol.blocks[-1].txs[token_id].isEmpty():
                print("Invalid block, starting withdraw")
        
        self.new_tokens = dict()

    def hasToken(self, token_id):
        return token_id in self.tokens
    
    def transfer(self, protocol, token_id, receiver):
        # Transfer a token to user by sending all proof history and sign the Tx
        # The receiver can acknowledge the token by checking the proof history and the new block includes the Tx
        protocol.addTx(token_id, self, receiver)
        receiver.addToken(token_id, self.tokens[token_id])
        del self.tokens[token_id]

    def deposit(self, protocol):
        protocol.deposit(self)
        self.addToken(protocol.tokens-1, [])


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
    
    def isEmpty(self):
        return self.sender_id == 0 and self.receiver_id == 0
    
    def __repr__(self) -> str:
        return "Tx({} {})".format(self.sender_id, self.receiver_id)

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

# Plasma protocol with contract deployed on L1 and maintained by an operator
class PlasmaProtocol:
    def __init__(self):
        self.blocks = []            # maintained by operator, not on contract
        self.block = None           # block to add, maintained by operator, not on contract

        self.tokens = 0             # available on contract
        self.block_hashes = []      # available on contract

    def deposit(self, user):
        # Create a single block for deposit
        self.tokens += 1
        block = PlasmaBlock(self.tokens)
        block.txs[-1] = PlasmaTx(0, user.id) # Genesis token tx
        self.blocks.append(block)
        self.block_hashes.append(block.root())
        print("Block {}: Deposited from user {} at token id {} with root {}".format(len(self.block_hashes)-1, user.id, self.tokens-1, self.block_hashes[-1].hex()))

    def newBlock(self):
        self.block = PlasmaBlock(self.tokens)

    def addTx(self, token_id, sender, receiver):
        # Add a transfer a token and add a tx in the block
        self.block.txs[token_id] = PlasmaTx(sender.id, receiver.id)
    
    def commitBlock(self):
        self.blocks.append(self.block)
        self.block_hashes.append(self.block.root())
        self.block = None
        print("Block {}: Commit new block".format(len(self.block_hashes)-1))

    def commitEmptyBlock(self):
        self.newBlock()
        self.commitBlock()


def test_blockn(n):
    b = PlasmaBlock(n)
    for i in range(n):
        b.txs[i] = PlasmaTx(i + 1, i + 2)
    
    for i in range(n):
        assert b.verifyProof(b.root(), i, b.txs[i], b.getProof(i))

def test_block():
    for i in range(1, 16):
        test_blockn(i)


def test_simple():
    # A -> B -> C
    users = [User.newUser() for i in range(3)]

    pp = PlasmaProtocol()
    users[0].deposit(pp)
    [user.notifyNewBlock(pp) for user in users]
    assert users[0].hasToken(0)

    pp.commitEmptyBlock()
    [user.notifyNewBlock(pp) for user in users]

    pp.newBlock()
    users[0].transfer(pp, 0, users[1])
    pp.commitBlock()

    [user.notifyNewBlock(pp) for user in users]
    assert users[1].hasToken(0)
    assert not users[0].hasToken(0)

    pp.newBlock()
    users[1].transfer(pp, 0, users[2])
    pp.commitBlock()
    [user.notifyNewBlock(pp) for user in users]
    assert users[2].hasToken(0)
    assert not users[1].hasToken(0)

def test_2token():
    # A -> C
    # B -> D
    users = [User.newUser() for i in range(4)]

    pp = PlasmaProtocol()
    users[0].deposit(pp)
    [user.notifyNewBlock(pp) for user in users]
    assert users[0].hasToken(0)

    users[1].deposit(pp)
    [user.notifyNewBlock(pp) for user in users]
    assert users[1].hasToken(1)

    pp.commitEmptyBlock()
    [user.notifyNewBlock(pp) for user in users]

    pp.newBlock()
    users[0].transfer(pp, 0, users[2])
    users[1].transfer(pp, 1, users[3])
    pp.commitBlock()

    [user.notifyNewBlock(pp) for user in users]
    assert users[2].hasToken(0)
    assert not users[0].hasToken(0)
    assert users[3].hasToken(1)
    assert not users[1].hasToken(1)

def test_2token_single_sender():
    # A -> C
    # B -> D
    users = [User.newUser() for i in range(3)]

    pp = PlasmaProtocol()
    users[0].deposit(pp)
    [user.notifyNewBlock(pp) for user in users]
    assert users[0].hasToken(0)

    users[0].deposit(pp)
    [user.notifyNewBlock(pp) for user in users]
    assert users[0].hasToken(1)

    pp.commitEmptyBlock()
    [user.notifyNewBlock(pp) for user in users]

    pp.newBlock()
    users[0].transfer(pp, 0, users[1])
    users[0].transfer(pp, 1, users[2])
    pp.commitBlock()

    [user.notifyNewBlock(pp) for user in users]
    assert users[1].hasToken(0)
    assert not users[0].hasToken(0)
    assert users[2].hasToken(1)
    assert not users[0].hasToken(1)

test_block()
test_simple()
test_2token()
test_2token_single_sender()