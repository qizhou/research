import random

from poly_commit import PolyCommitment
from functools import reduce

def test_simple_lookup():
    pc = PolyCommitment()

    # 2-bit and (&) table
    table = []
    for i in range(4):
        for j in range(4):
            table.append(i * 16 + j * 4 + i & j)
    # simple 1 to 8 table
    table = []
    for i in range(8):
        table.append(i + 1)

    # same size lookup
    # TODO: any size lookup
    f = [table[random.randint(0, len(table)-1)] for i in range(len(table))]

    idx = [table.index(l) for l in f]
    idx.sort()
    f_p = [table[i] for i in idx]
    unused = {v for v in table} # unused table values
    for v in f_p:
        unused.discard(v)
    unused = [u for u in unused] # to list
    unused_idx = 0
    t_p = f_p[:]
    for i in range(1, len(t_p)):
        if f_p[i] == f_p[i - 1]:
            t_p[i] = unused[unused_idx]
            unused_idx += 1
    assert unused_idx == len(unused)
    
    # Test if (t_p, f_p) is permutable of (table, lookup)
    r0 = pc.rand()
    r1 = pc.rand()
    left = reduce(lambda a, b: a * b % pc.modulus, [(x - r0) * (y - r1) % pc.modulus for x, y in zip(table, f)])
    right = reduce(lambda a, b: a * b % pc.modulus, [(x - r0) * (y - r1) % pc.modulus for x, y in zip(t_p, f_p)])
    assert left == right

    # Test if t_p[0] == f_p[0]
    assert t_p[0] == f_p[0]

    # Test (f'(x) - f'(x - 1)) * (f'(x) - t'(x)) = 0
    for i in range(len(t_p)):
        assert (f_p[i] - f_p[i - 1]) * (f_p[i] - t_p[i]) == 0

    # TOOD: KZG commitment, and generate proof then verify
    print("test_simple_lookup passed")


if __name__ == "__main__":
    test_simple_lookup()