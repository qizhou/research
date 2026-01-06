# implement a half-path-based binary merkle tree
import hashlib

def hash_func(data):
    return hashlib.sha256(data).digest()

KIND_LEAF = 0
KIND_INTERNAL = 1

KEY_NIL = b'\0' * 32

class Node:
    def __init__(self, kind, data):
        self.kind = kind
        self.data = data

# the half path based format is implemetn at 
# https://github.com/NethermindEth/nethermind/blob/master/src/Nethermind/Nethermind.Trie/NodeStorage.cs#L37
#
# # For state (total 42 byte) 
# +--------------+------------------+------------------+--------------+
# | section byte | 8 byte from path | path length byte | 32 byte hash |
# +--------------+------------------+------------------+--------------+
# For storage (total 74 byte)
# +--------------+---------------------+------------------+------------------+--------------+
# | section byte | 32 byte from address | 8 byte from path | path length byte | 32 byte hash |
# +--------------+---------------------+------------------+------------------+--------------+
#
# The section byte is:
# - 0 if state and path length is <= 5.
# - 1 if state and path length is > 5.
# - 2 if storage.
#
# To simplify the implementation, this example only retains three fields: 
# 8 bytes from path, path length in bytes, and 32 bytes hash. 
# 
# The '8 byte from path' is the first 8 bytes of the path 
# path.Path.BytesAsSpan[..8].CopyTo(pathSpan[1..]); 
# We use the top `depth` bits of the key here.

def get_nbit(key, pos):
   b = pos >> 3          # pos // 8
   shift = 7 - (pos & 7) # 7 - (pos % 8)
   return (key[b] >> shift) & 1

def prefix8_from_key_and_depth(key: bytes, depth: int) -> bytes:
    """
    depth: 0..255
    """
    assert len(key) == 32
    assert 0 <= depth <= 255

    prefix = int.from_bytes(key[:8], "big")

    if depth >= 64:
       return prefix.to_bytes(8, "big")

    # keep top `depth` bits
    mask = ((1 << depth) - 1) << (64 - depth)
    prefix &= mask

    return prefix.to_bytes(8, "big")

def encode_half_path(key, path_len, node_hash):
    assert 0 <= path_len <= 255
    return (
        prefix8_from_key_and_depth(key, path_len) +
        bytes([path_len]) +
        node_hash
    )

# a), initial tree
#  root=internal('0'*32 + '0'*32)
#
# b), put(h0,d0) h0=0b010....
#    root=internal(n0 + '0'*32)
#  n0=leaf(h0+d0)
#  key '0'*8 + '0' + root_hash => root
#  key b'00000000' + '0'*7 + '1' + n0_hash => n0
#
# c), put(h1,d1) h1=0b00...
#       root=internal(inode0 + '0'*32)
#  inode0=internal(n1 + n0)
#  n0=leaf(h0+d0), n1=leaf(h1+d1)
#  key '0'*8 + '0' + root_hash => root
#  key b'00000000' + '0'*7 + '1' + inode0_hash => inode0
#  key b'00000000' + '0'*7 + '2' + n1_hash => n1
#  key b'01000000' + '0'*7 + '2' + n0_hash => n0
#
# d), put(h2,d2) h2=0b11...
#       root=internal(inode0 + n2)
#  inode0=internal(n1 + n0)
#  n0=leaf(h0+d0), n1=leaf(h1+d1), n2=leaf(h2+d2)
#  key '0'*8 + '0' + root_hash => root
#  key b'00000000' + '0'*7 + '1' + inode0_hash => inode0
#  key b'00000000' + '0'*7 + '2' + n1_hash => n1
#  key b'01000000' + '0'*7 + '2' + n0_hash => n0
#  key b'10000000' + '0'*7 + '1' + n2_hash => n2
#
# f), from b), put(h1,d1) h1=0b011
#  root=internal(inode0 + '0'*32)
#  inode0=internal('0'*32 + inode1)
#  inode1=internal(n1 + n0)
#  n0=leaf(h0+d0), n1=leaf(h1+d1)
#  key '0'*8 + '0' + root_hash => root
#  key b'00000000' + '0'*7 + '1' + inode0_hash => inode0
#  key b'01000000' + '0'*7 + '2' + inode1_hash => inode1
#  key b'00000000' + '0'*7 + '2' + n1_hash => n1
#  key b'01000000' + '0'*7 + '3' + n0_hash => n0
#  key b'10000000' + '0'*7 + '1' + n2_hash => n2
#  key b'01100000' + '0'*7 + '3' + n3_hash => n3
class Tree:
    def __init__(self):
        self.kv = dict()
        self.root, _ = self.__createInternal(KEY_NIL + KEY_NIL, KEY_NIL, 0)

    def __store(self, node, key, depth):
        h = hash_func(node.data)
        db_key = encode_half_path(key, depth, h)
        self.kv[db_key] = node
        return h, node

    def __get_node(self, node_hash, key, depth):
        if node_hash == KEY_NIL:
            return None
        return self.kv.get(encode_half_path(key, depth, node_hash))

    def __createInternal(self, value, key, depth):
        return self.__store(Node(KIND_INTERNAL, value), key, depth)

    def __createLeaf(self, key, value, depth):
        return self.__store(Node(KIND_LEAF, key + value), key, depth)

    def put(self, key, value):
        leaf_node = Node(KIND_LEAF, key + value)
        leaf_hash = hash_func(leaf_node.data)
        node_hash = self.root
        path = []

        while True:
            node = self.__get_node(node_hash, key, len(path))
            if node is None:
                break

            depth = len(path)
            if node.kind == KIND_LEAF:
                existing_key = node.data[:32]
                if existing_key == key:
                    node_hash, _ = self.__store(leaf_node, key, depth)
                    break

                for common in range(depth, 256):
                    if get_nbit(key, common) != get_nbit(existing_key, common):
                        break
                
                self.__store(leaf_node, key, common+1)
                self.__store(node, existing_key, common+1)

                if get_nbit(key, common) == 0:
                    node_hash, _ = self.__createInternal(leaf_hash + node_hash, key, common)
                else:
                    node_hash, _ = self.__createInternal(node_hash + leaf_hash, key, common)

                for i in range(common - 1, depth - 1, -1):
                    if get_nbit(key, i) == 0:
                        data = node_hash + KEY_NIL
                    else:
                        data = KEY_NIL + node_hash
                    node_hash, _ = self.__createInternal(data, key, i)
                break

            bit = get_nbit(key, len(path))
            next_hash = node.data[bit * 32:(bit + 1) * 32]

            if next_hash == KEY_NIL:
                self.__store(leaf_node, key, depth+1)
                if bit == 0:
                    data = leaf_hash + node.data[32:]
                else:
                    data = node.data[:32] + leaf_hash
                node_hash, _ = self.__createInternal(data, key, len(path))
                break

            path.append(node)
            node_hash = next_hash

        for depth, parent in reversed(list(enumerate(path))):
            bit = get_nbit(key, depth)
            if bit == 0:
                data = node_hash + parent.data[32:]
            else:
                data = parent.data[:32] + node_hash
            node_hash, _ = self.__createInternal(data, key, depth)

        self.root = node_hash

    def get(self, key):
        node_hash = self.root

        for depth in range(256):
            node = self.__get_node(node_hash, key, depth)
            if node is None:
                return None

            if node.kind == KIND_LEAF:
                return node.data[32:] if node.data[:32] == key else None

            bit = get_nbit(key, depth)
            node_hash = node.data[bit * 32:(bit + 1) * 32]

        return None

    def setRoot(self, root):
        self.root = root

t = Tree()
t.put(b'\x40'+b'\1'*31, b'\0')   # b'\x40' -> 0100 0000
assert t.get(b'\x40'+b'\1'*31) == b'\0'
t.put(b'\x00'+b'\1'*31, b'\1')   # b'\x00' -> 0000 0000
assert t.get(b'\x40'+b'\1'*31) == b'\0'
assert t.get(b'\x00'+b'\1'*31) == b'\1'
t.put(b'\xc0'+b'\1'*31, b'\2')   # b'\xc0' -> 1100 0000
assert t.get(b'\x40'+b'\1'*31) == b'\0'
assert t.get(b'\x00'+b'\1'*31) == b'\1'
assert t.get(b'\xc0'+b'\1'*31) == b'\2'
root = t.root
t.put(b'\x60'+b'\1'*31, b'\3')   # b'\x60' -> 0110 0000 
assert t.get(b'\x40'+b'\1'*31) == b'\0'
assert t.get(b'\x00'+b'\1'*31) == b'\1'
assert t.get(b'\xc0'+b'\1'*31) == b'\2'
assert t.get(b'\x60'+b'\1'*31) == b'\3'
t.setRoot(root)
assert t.get(b'\x40'+b'\1'*31) == b'\0'
assert t.get(b'\x00'+b'\1'*31) == b'\1'
assert t.get(b'\xc0'+b'\1'*31) == b'\2'
assert t.get(b'\x60'+b'\1'*31) == None

# test multi-version
t.put(b'\x00'+b'\1'*31, b'\3')
assert t.get(b'\x40'+b'\1'*31) == b'\0'
assert t.get(b'\x00'+b'\1'*31) == b'\3'
assert t.get(b'\xc0'+b'\1'*31) == b'\2'
assert t.get(b'\x60'+b'\1'*31) == None
t.setRoot(root)
assert t.get(b'\x40'+b'\1'*31) == b'\0'
assert t.get(b'\x00'+b'\1'*31) == b'\1'
assert t.get(b'\xc0'+b'\1'*31) == b'\2'
assert t.get(b'\x60'+b'\1'*31) == None