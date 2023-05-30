

def multilinear_interp(w):
    n = len(w)
    bits = len(bin(n)) - 3
    l = [i for i in range(n)]
    assert n & (n-1) == 0
    sum_c = [0] * n
    for i in range(n):
        c = []
        for j in range(bits):
            if j == 0:
                if i & 1 == 0:
                    c = [-w[i], w[i]]
                else:
                    c = [w[i], 0]
            else:
                if i & 1 == 0:
                    c1 = [0, 0] + c
                    c2 = c + [0, 0]
                    c = [a - b for a, b in zip(c1, c2)]
                else:
                    c = c + [0, 0]
            i = i // 2
        
        sum_c = [a + b for a, b in zip(sum_c, c)]
    return sum_c

def multilinear_eval0(c, idx):
    s = 0
    for i, x in enumerate(reversed(c)):
        if i & idx == i:
            s += x
    return s

def multilinear_eval(c, ids):
    s = 0
    for i, x in enumerate(reversed(c)):
        p = x
        for j in range(len(ids)):
            if (i >> j) & 1 == 1:
                p = p * ids[j]
        s += p
    return s

print(multilinear_interp([2, 5]))
c = multilinear_interp([1, 2, 1, 4])
print(multilinear_interp([1, 2, 1, 4]))
print(multilinear_eval(c, [1, 1]))
print(multilinear_eval(c, [1, 3]))

