
class Node:
    def __init__(self, i, deps, comp, isOutput):
        self.idx = i
        self.deps = deps
        self.comp = comp
        self.isOutput = isOutput


class Trace:
    def __init__(self):
        self.nodes = []
    
    def addNode(self, deps, comp, isOutput=False):
        self.nodes.append(Node(len(self.nodes), deps, comp, isOutput))

    def getNode(self, idx):
        return self.nodes[idx]
    
    def getLastNode(self):
        return self.nodes[-1]
    
    def getPreviousNode(self, n):
        return self.nodes[-n]

    def calculateOutputComp(self, func, cache=None):
        comps = []
        output = []
        for i, n in enumerate(self.nodes):
            comp = set()
            if cache is not None and i in cache:
                pass
            else:
                if n.comp != 0:
                    comp.add(n)
                for dep in n.deps:
                    comp = comp.union(comps[dep.idx])
            
            comps.append(comp)
            if n.isOutput:
                output.append((i, func(comp)))
        return output
    

def sum_comp(nodes):
    comp = 0
    for n in nodes:
        comp += n.comp
    return comp


def cbc_example(layers=1, cache=None):
    n = 8

    trace = Trace()
    # first layer, each with computational cost 1
    for _ in range(n):
        trace.addNode([], 1)

    # first output
    trace.addNode([trace.getNode(0)], 0, layers==1)
    # first layer
    for i in range(1, n):
        trace.addNode([trace.getNode(i), trace.getLastNode()], 0, layers==1)

    for l in range(1, layers):
        for i in range(0, n):
            trace.addNode([trace.getPreviousNode(n), trace.getLastNode()], 0, layers-1==l)

    output = trace.calculateOutputComp(sum_comp, cache)
    print(output)
    print(sum([x[1] for x in output]) / len(output))

cbc_example()
cbc_example(1, cache=[12])
cbc_example(1, cache=[10, 12, 14])

cbc_example(2)
cbc_example(2, cache=[12])
cbc_example(2, cache=[20])
cbc_example(2, cache=[12, 20])
cbc_example(2, cache=[11, 19])
cbc_example(2, cache=[11, 12])
cbc_example(2, cache=[19, 20])
cbc_example(2, cache=[11, 20])