# implement a simple path-based trie
import hashlib
import hash

def hash_func(data):
    return hashlib.sha256(data).digest()

KIND_LEAF = 0
KIND_INTERNAL = 1

KEY_NIL = b'\0' * 32

class Node:
    def __init__(self, kind, data):
        self.kind = kind
        self.data = data

    def hash(self):
        return hash_func(self.data)

def get_nbit(key, pos):
    b = pos // 8
    return (key[b] >> (pos % 8)) % 2

# a), initial tree
#  root=internal('0'*32 + '0'*32)
#
# b), put(h0,d0) h0=0b010....
#    root=internal(n0 + '0'*32)
#  n0=leaf(h0+d0)
#  key '' => root
#  key '0' => n0
#
# c), put(h1,d1) h1=0b00...
#       root=internal(inode0 + '0'*32)
#  inode0=internal(n1 + n0)
#  n0=leaf(h0+d0), n1=leaf(h1+d1)
#  key '' => root
#  key '0' => inode0
#  key '00' => n1
#  key '01' => n0
#
# d), put(h2,d2) h2=0b11...
#       root=internal(inode0 + n2)
#  inode0=internal(n1 + n0)
#  n0=leaf(h0+d0), n1=leaf(h1+d1), n2=leaf(h2+d2)
#  key '' => root
#  key '0' => inode0
#  key '00' => n1
#  key '01' => n0
#  key '1' => n2
#
# f), from b), put(h1,d1) h1=0b011
#  root=internal(inode0 + '0'*32)
#  inode0=internal('0'*32 + inode1)
#  inode1=internal(n1 + n0)
#  n0=leaf(h0+d0), n1=leaf(h1+d1)
#  key '' => root
#  key '0' => inode0
#  key '01' => inode1
#  key '010' => n1
#  key '011' => n0

class Tree:
    def __init__(self, kv=None):
        self.kv = {b'': Node(KIND_INTERNAL, KEY_NIL + KEY_NIL)} if kv == None else kv

    def put(self, key, value):
        # assume key is already hashed
        path = b''
        for i in range(256):
            path = path + bytes([get_nbit(key, i)])
            if path not in self.kv:
                # assert parent path's entry for this node is KEY_NIL
                break # insert the node at the path here
            node = self.kv[path]
            if node.kind == KIND_INTERNAL:
                pass
            elif node.kind == KIND_LEAF:
                if node.data[:32] == key:
                    # update
                    break
                # move the leaf to next depth
                leaf_key = node.data[:32]
                leaf_path = path + bytes([get_nbit(leaf_key, i+1)])
                assert leaf_path not in self.kv
                self.kv[leaf_path] = node
                if get_nbit(leaf_key, i+1) == 0:
                    self.kv[path] = Node(KIND_INTERNAL, node.hash() + KEY_NIL)
                else:
                    self.kv[path] = Node(KIND_INTERNAL, KEY_NIL + node.hash())
            else:
                assert AssertionError("unknown node")

        node = Node(KIND_LEAF, key + value)
        self.kv[path] = node
        for i in reversed(range(0, len(path))):
            idx = get_nbit(key, i)
            if idx == 0:
                pnode = Node(KIND_INTERNAL, node.hash()+self.kv[path[:i]].data[32:])
            else:
                pnode = Node(KIND_INTERNAL, self.kv[path[:i]].data[:32]+node.hash())
            self.kv[path[:i]] = pnode
            node = pnode

    def get(self, key):
        path = b''
        for i in range(256):
            path = path + bytes([get_nbit(key, i)])
            if path not in self.kv:
                return None
            node = self.kv[path]
            if node.kind == KIND_LEAF:
                if node.data[:32] == key:
                    return node.data[32:]
                else:
                    return None

    @property
    def root(self):
        return self.kv[b''].hash()

# Tree with optimization so that get() is O(1)
# The key idea is to store all leaf nodes as native key => value
# And then during path lookup, find the leaf according to the path (prefix) via range search.
class OptimizedTree:
    def __init__(self, kv=None):
        self.kv = {b'': Node(KIND_INTERNAL, KEY_NIL + KEY_NIL)} if kv == None else kv

    def __searchLeafWithPath(self, path):
        # this could be done by range search in kvs, which is very efficient
        for key, node in self.kv.items():
            if node.kind == KIND_INTERNAL:
                continue

            found = True
            for i in range(len(path)):
                if get_nbit(key, i) != path[i]:
                    found = False
                    break
            if found:
                return node

    def put(self, key, value):
        # assume key is already hashed
        path = b''
        node = self.kv[path] # root
        for i in range(256):
            path = path + bytes([get_nbit(key, i)])
            if path not in self.kv:
                # we have two cases
                # 1. the parent path's entry for this node is KEY_NIL
                # 2. the parent path's entry for this node is a leaf node
                if node.data[get_nbit(key, i)*32:get_nbit(key, i)*32+32] == KEY_NIL:
                    break # insert the leaf node after the node
                node = self.__searchLeafWithPath(path)
            else:
                node = self.kv[path]
                assert node.kind == KIND_INTERNAL
                continue

            assert node.kind == KIND_LEAF
            if node.data[:32] == key:
                # update
                break
            # move the leaf to next depth
            leaf_key = node.data[:32]
            if get_nbit(leaf_key, i+1) == 0:
                node = Node(KIND_INTERNAL, node.hash() + KEY_NIL)
            else:
                node = Node(KIND_INTERNAL, KEY_NIL + node.hash())
            self.kv[path] = node

        node = Node(KIND_LEAF, key + value)
        self.kv[key] = node
        for i in reversed(range(0, len(path))):
            idx = get_nbit(key, i)
            if idx == 0:
                pnode = Node(KIND_INTERNAL, node.hash()+self.kv[path[:i]].data[32:])
            else:
                pnode = Node(KIND_INTERNAL, self.kv[path[:i]].data[:32]+node.hash())
            self.kv[path[:i]] = pnode
            node = pnode

    def get(self, key):
        if key not in self.kv:
            return None
        return self.kv[key].data[32:]

    @property
    def root(self):
        return self.kv[b''].hash()


def test_tree(tree_func):
    t = tree_func()
    t1 = hash.Tree()
    t.put(b'\2'+b'\1'*31, b'\0')
    t1.put(b'\2'+b'\1'*31, b'\0')
    assert t.get(b'\2'+b'\1'*31) == b'\0'
    assert t.root == t1.root
    t.put(b'\0'+b'\1'*31, b'\1')
    t1.put(b'\0'+b'\1'*31, b'\1')
    assert t.get(b'\2'+b'\1'*31) == b'\0'
    assert t.get(b'\0'+b'\1'*31) == b'\1'
    assert t.root == t1.root
    t.put(b'\3'+b'\1'*31, b'\2')
    t1.put(b'\3'+b'\1'*31, b'\2')
    assert t.get(b'\2'+b'\1'*31) == b'\0'
    assert t.get(b'\0'+b'\1'*31) == b'\1'
    assert t.get(b'\3'+b'\1'*31) == b'\2'
    snapshot = dict(t.kv)
    root1 = t1.root
    assert t.root == t1.root
    t.put(b'\131'+b'\1'*31, b'\3')
    t1.put(b'\131'+b'\1'*31, b'\3')
    assert t.get(b'\2'+b'\1'*31) == b'\0'
    assert t.get(b'\0'+b'\1'*31) == b'\1'
    assert t.get(b'\3'+b'\1'*31) == b'\2'
    assert t.get(b'\131'+b'\1'*31) == b'\3'
    assert t.root == t1.root

    t = tree_func(snapshot)
    t1.setRoot(root1)
    assert t.get(b'\2'+b'\1'*31) == b'\0'
    assert t.get(b'\0'+b'\1'*31) == b'\1'
    assert t.get(b'\3'+b'\1'*31) == b'\2'
    assert t.get(b'\131'+b'\1'*31) == None
    assert t.root == t1.root

    # test multi-version
    t.put(b'\0'+b'\1'*31, b'\3')
    t1.put(b'\0'+b'\1'*31, b'\3')
    assert t.get(b'\2'+b'\1'*31) == b'\0'
    assert t.get(b'\0'+b'\1'*31) == b'\3'
    assert t.get(b'\3'+b'\1'*31) == b'\2'
    assert t.get(b'\131'+b'\1'*31) == None
    assert t.root == t1.root

test_tree(Tree)
test_tree(OptimizedTree)