# implement a simple hash-based binary merkle tree
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


def get_nbit(key, pos):
    b = pos // 8
    return (key[b] >> (pos % 8)) % 2


# a), initial tree
#  root=internal('0'*32 + '0'*32); or
#  root='0'*32
#
# b), put(h0,d0) h0=0b010....
#    root=internal(n0 + '0'*32)
#  n0=leaf(h0+d0)
#
# c), put(h1,d1) h1=0b00...
#       root=internal(inode0 + '0'*32)
#  inode0=internal(n1 + n0)
#  n0=leaf(h0+d0), n1=leaf(h1+d1)
#
# d), put(h2,d2) h2=0b11...
#       root=internal(inode0 + n2)
#  inode0=internal(n1 + n0)
#  n0=leaf(h0+d0), n1=leaf(h1+d1), n2=leaf(h2+d2)

# f), from b), put(h1,d1) h1=0b011
#  root=internal(inode0 + '0'*32)
#  inode0=internal('0'*32 + inode1)
#  inode1=internal(n1 + n0)
#  n0=leaf(h0+d0), n1=leaf(h1+d1)


class Tree:
    def __init__(self):
        self.kv = dict()
        self.root, _ = self.__createInternal(KEY_NIL + KEY_NIL)

    def __createInternal(self, value):
        node = Node(KIND_INTERNAL, value)
        key = hash_func(value)
        self.kv[key] = node
        return key, node

    def __createLeaf(self, key, value):
        node = Node(KIND_LEAF, key + value) # TODO: only store the part of the key not used in path
        hkey = hash_func(key + value)
        self.kv[hkey] = node
        return hkey, node

    def put(self, key, value):
        leaf_hash, leaf_node = self.__createLeaf(key, value)
        node_key = self.root
        path = []

        while True:
            node = self.kv[node_key]
            if node.kind == KIND_LEAF:
                # need to create internal nodes to replace the leaf and update following the path
                existing_leaf_key = node.data[:32]
                if existing_leaf_key == key:
                    # update
                    node_key = leaf_hash
                    node = leaf_node
                    break

                depth = len(path)
                for common in range(depth, 256):
                    if get_nbit(key, depth) != get_nbit(existing_leaf_key, depth):
                        break

                if get_nbit(key, depth) == 0:
                    inode_data = leaf_hash + node_key
                else:
                    inode_data = node_key + leaf_hash
                inode_key, _ = self.__createInternal(inode_data)
                for i in range(common-1, depth, -1):
                    if get_nbit(key, i) == 0: 
                        inode_data = inode_key + KEY_NIL
                    else:
                        inode_data = KEY_NIL + inode_key
                    inode_key, _ = self.__createInternal(inode_data)
                node_key = inode_key
                break
    
            idx = get_nbit(key, len(path))
            next_node_key = node.data[idx*32:idx*32+32]
            if next_node_key == KEY_NIL:
                # replace the empty slot of the current node and update following the path
                if node.data[0:32] == KEY_NIL:
                    new_data = leaf_hash + node.data[32:]
                else:
                    new_data = node.data[:32] + leaf_hash
                node_key, _ = self.__createInternal(new_data)
                break
            node_key = next_node_key
                
            path.append(node)            

        # now we have a updated node with its key, and its parents in the path
        # update the path accordingly
        for i, parent in reversed(list(enumerate(path))):
            if get_nbit(key, i) == 0:
                new_data = node_key + parent.data[32:]
            else:
                new_data = parent.data[:32] + node_key
            # TODO: assert another part of the parent data is NIL
            node_key, _ = self.__createInternal(new_data)
        self.root = node_key

    def get(self, key):
        node_key = self.root
        for i in range(0, 256):
            if node_key == KEY_NIL:
                return None
            node = self.kv[node_key]
            if node.kind == KIND_LEAF:
                if node.data[:32] == key:
                    return node.data[32:]
                else:
                    return None
            idx = get_nbit(key, i)
            node_key = node.data[idx*32:idx*32+32]

    def setRoot(self, root):
        self.root = root


t = Tree()
t.put(b'\2'+b'\1'*31, b'\0')
assert t.get(b'\2'+b'\1'*31) == b'\0'
t.put(b'\0'+b'\1'*31, b'\1')
assert t.get(b'\2'+b'\1'*31) == b'\0'
assert t.get(b'\0'+b'\1'*31) == b'\1'
t.put(b'\3'+b'\1'*31, b'\2')
assert t.get(b'\2'+b'\1'*31) == b'\0'
assert t.get(b'\0'+b'\1'*31) == b'\1'
assert t.get(b'\3'+b'\1'*31) == b'\2'
root = t.root
t.put(b'\131'+b'\1'*31, b'\3')
assert t.get(b'\2'+b'\1'*31) == b'\0'
assert t.get(b'\0'+b'\1'*31) == b'\1'
assert t.get(b'\3'+b'\1'*31) == b'\2'
assert t.get(b'\131'+b'\1'*31) == b'\3'
t.setRoot(root)
assert t.get(b'\2'+b'\1'*31) == b'\0'
assert t.get(b'\0'+b'\1'*31) == b'\1'
assert t.get(b'\3'+b'\1'*31) == b'\2'
assert t.get(b'\131'+b'\1'*31) == None

# test multi-version
t.put(b'\0'+b'\1'*31, b'\3')
assert t.get(b'\2'+b'\1'*31) == b'\0'
assert t.get(b'\0'+b'\1'*31) == b'\3'
assert t.get(b'\3'+b'\1'*31) == b'\2'
assert t.get(b'\131'+b'\1'*31) == None
t.setRoot(root)
assert t.get(b'\2'+b'\1'*31) == b'\0'
assert t.get(b'\0'+b'\1'*31) == b'\1'
assert t.get(b'\3'+b'\1'*31) == b'\2'
assert t.get(b'\131'+b'\1'*31) == None