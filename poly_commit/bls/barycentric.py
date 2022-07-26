from ec import (G1FromBytes, G1Generator, G1Infinity, G2FromBytes, G2Generator,
                G2Infinity, JacobianPoint, default_ec, default_ec_twist,
                sign_Fq2, twist, untwist, y_for_x)
from fields import Fq
from pairing import ate_pairing
from poly_commit import poly_interp, get_single_proof, poly_eval

from functools import reduce

order = 13

nroots = 3
primitive = 2
roots = [Fq(order, primitive) ** (i * (order - 1) // nroots)  for i in range(nroots)]

x = Fq(order, 4)
y = reduce(lambda x, y: x * y, [x - r for r in roots])
print(y, x ** nroots - Fq(order, 1))


order = default_ec.n
nroots = 8
primitive = 7
roots = [Fq(order, primitive) ** (i * (order - 1) // nroots)  for i in range(nroots)]

x = Fq(order, 14)
y = reduce(lambda x, y: x * y, [x - r for r in roots])
print(y, x ** nroots - Fq(order, 1))

def print_lagrange_denum(roots):
    for i in range(len(roots)):
        x = Fq(roots[0].Q, 1)
        for j in range(len(roots)):
            if i == j:
                continue
            x = x * (roots[i] - roots[j])
        print(Fq(roots[0].Q, 1) / x)

g1 = G1Generator()
g2 = G2Generator()

# secret of trusted setup
secret = Fq(order, 87362938561938363821)

# vec = [51234, 28374, 62734, 19823, 571763, 83746, 198384, 827512]
vec = [51234, 28374]
nroots = len(vec)
primitive = 7
roots = [Fq(order, primitive) ** (i * (order - 1) // nroots)  for i in range(nroots)]

# convert it to BLS field
vec = [Fq(order, x) for x in vec]
coeffs = poly_interp(vec, roots)

# evaluate the polynomial using coefficient form
print(poly_eval(coeffs, secret))
# evaluate the polynomial using evaluation form
print((secret ** nroots - Fq(order, 1)) * reduce(lambda x, y: x + y, [x * y / (secret - x) for x, y in zip(roots, vec)]) / Fq(order, nroots))

# s^i secrec vector, which is available to everybody (and cannot infer s)
sec_vec = [g1 * (secret ** i) for i in range(len(vec) + 1)]
# evaluate the commitment using trusted G1 setup
commit0 = sum(s * c for s, c in zip(sec_vec, coeffs))

# evaluate the commitment using trusted Lagrange setup
sec_roots = [(secret ** nroots - Fq(order, 1)) * w / Fq(order, nroots) / (secret - w) * g1 for w in roots]
commit1 = sum(s * y for s, y in zip(sec_roots, vec))
print("commitment is equal", commit0 == commit1)

# z = 1
# # proof
# qs = get_single_proof(coeffs, sec_vec, z, vec[z])
# sz2 = g2 * secret + (g2 * z).negate()
# pair0 = ate_pairing(qs, sz2)
# print(pair0)

# cy = commit + (g1 * vec[z]).negate()
# pair1 = ate_pairing(cy, g2)
# print(pair1)
# assert pair0 == pair1