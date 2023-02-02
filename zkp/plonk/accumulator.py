# A simple accumulator example
import random

# 1D accumulator
modulus = 2**256 - 2**32 * 351 + 1

xs = [5, 2, 3, 1]
ps = [1]
v = random.randint(0, modulus - 1)

for x in xs:
    ps.append((ps[-1] * (x + v)) % modulus)

print(ps[-1])

# ps[-1] = p(v) = \prod (v - x_i)
# so it is essentially the evaluated of a poly with roots at xs at random r
# (definitively suffering from permutation)

# 1D accumulator with exact sequence
modulus = 2**256 - 2**32 * 351 + 1

ps = [1]
v0 = random.randint(0, modulus - 1)
v1 = random.randint(0, modulus - 1)

for i, x in enumerate(xs):
    ps.append((ps[-1] * (v0 + i + v1 * x)) % modulus)

print(ps[-1])

# ps[-1] = p(v0, v1) = \prod (v0 + i + v1 * x_i) with roots at (i, x_i)