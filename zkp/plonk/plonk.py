# A plonk implementation based on Vitalik's article

# L, R, O, M, C of the constraint
Q = [[0, 0, 0, 0, 0],
     [0, 0, -1, 1, 0],
     [0, 0, -1, 1, 0],
     [1, 1, -1, 0, 0],
     [0, 0, -1, 0, 5],
     [1, 0, 1, 0, 5],
     [1, 0, -35, 0, 0]]

n = len(Q)
def a(i):
    return i

def b(i):
    return n + i

def c(i):
    return 2 * n + i

# Copy constrant (index of A, B, C)
C = [[c(1), a(2)], [c(2), b(3)], [c(3), a(5)], [c(5), a(6)]]