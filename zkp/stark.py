# A stark example from Vitalik's blog
import random
import poly_utils

modulus = 52435875175126190479447740508185965837690552500527637822603658699938581184513
pf = poly_utils.PrimeField(modulus)
# P(x) is a polynomial with 0 <= P(x) <= 9, with x = [1, 20] (or 1M)


N = 20 # number of data points
M = 9  # value ranges from [0, 9]
p_eval = [random.randint(0, M) for i in range(N)]
p = pf.lagrange_interp([i + 1 for i in range(N)], p_eval)

pp = p[:]
c = pf.zpoly([i for i in range(M + 1)])
c_ext = [1]
for i in range(M + 1):
    c_ext = pf.mul_polys(c_ext, pp)
    pp[0] = (pp[0] - 1) % modulus

z = pf.zpoly([i + 1 for i in range(N)])

d, r = pf.div_polys_with_rem(c_ext, z)

# Now, suppose we have p and d commitments for x = 1 to 1e9 (or a very large number)
# Those are verification keys

# For verification, we calculate 16 random positions in [1, 1e9]
pos = random.randint(1, 1000000000)

p_pos = pf.eval_poly_at(p, pos)
d_pos = pf.eval_poly_at(d, pos)
# TODO: verify p_pos and d_pos are in the commitment at pos
# check C(p_pos) = Z(pos) * d_pos
z_pos = pf.eval_poly_at(z, pos)
c_pos = pf.eval_poly_at(c, p_pos)
assert c_pos == pf.mul(z_pos, d_pos)

