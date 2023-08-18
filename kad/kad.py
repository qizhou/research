import random
import heapq

# bucket size
# K = 20 # default
K = 4

# number of bits in id
ID_BIT_SIZE = 16
ID_MAX = 2 ** ID_BIT_SIZE - 1

def count_bits(v):
    n = 0
    while v != 0:
        if v & 1 == 1:
            n += 1
        v = v // 2
    return n


# log2(id0 ^ id1)
def log_distance(id0, id1):
    """ Find the n where first n - 1 are common bit prefix of ids """
    v = id0 ^ id1
    d = 0
    while v != 0:
        d = d + 1
        v = v // 2
    return d


class Node:
    def __init__(self, id):
        self.id = id
        self.routingTable = [list() for i in range(ID_BIT_SIZE + 1)]

    def createRandomNode():
        return Node(random.randint(0, ID_MAX))

    def getRandomNodeIds(n):
        s = set()
        while len(s) < n:
            s.add(random.randint(0, ID_MAX))
        return s

    def addNode(self, node):
        dist = log_distance(self.id, node.id) - 1

        if len(self.routingTable[dist]) < K:
            self.routingTable[dist].append(node)
        else:
            # print("warning: routing table is full")
            # or randomly drop a node
            pass

    def findNode(self, key):
        # Implemement FIND_NODE RPC, which returns top K nodes to the key
        pq = []
        dist = log_distance(self.id, key)
        if dist == 0:
            return self

        counter = 0

        # TODO: could we optimize the search without iterate all nodes?
        for i in range(ID_BIT_SIZE):
            for n in self.routingTable[i]:
                dist0 = log_distance(key, n.id)
                if dist0 >= dist:
                    continue
                if dist0 == 0:
                    return [(0, 0, n)]
                counter += 1
                if len(pq) < K:
                    heapq.heappush(pq, (-dist0, counter, n))
                elif dist0 < -heapq[0][0]:
                    heapq.heappushpop(pq, (-dist0, counter, n))
        return pq

    def findNodeExact(self, key):
        # Repeated find the node of the key
        pq = []
        visited = set()
        dist = log_distance(self.id, key)
        if dist == 0:
            return self

        iter = 0
        print("iter %d, distance %d" % (iter, dist))
        pq = self.findNode(key)
        if len(pq) == 1 and pq[0][0] == 0:
            return pq[0][2]
        while True:
            iter += 1
            print("iter %d, nodes %s" % (iter, [(x[2].id, -x[0]) for x in pq]))
            npq = []
            counter = 0
            for n in pq:
                nodes = n[2].findNode(key)
                for ndist0, _, n in nodes:
                    if ndist0 == 0:
                        return n
                    if n.id in visited:
                        continue
                    visited.add(n.id)

                    counter += 1
                    if len(npq) < K:
                        heapq.heappush(npq, (ndist0, counter, n))
                    elif -ndist0 < -npq[0][0]:
                        heapq.heappushpop(npq, (ndist0, counter, n))

            if len(npq) == 0:
                return None

            pq = npq


random.seed(12345)
nodes = [Node(i) for i in Node.getRandomNodeIds(1000)]
for i in range(len(nodes)):
    for j in range(i+1, len(nodes)):
        nodes[i].addNode(nodes[j])
        nodes[j].addNode(nodes[i])

# print(nodes[0].findNode(nodes[99].id))
# print(nodes[0].findNodeExact(nodes[99].id).id)
# print(nodes[0].findNodeExact(nodes[55].id).id)
# print(nodes[0].findNodeExact(nodes[2].id).id)
# print(nodes[0].findNodeExact(nodes[500].id).id)
print(nodes[0].findNodeExact(nodes[987].id).id)
print(nodes[0].findNodeExact(nodes[999].id).id)
