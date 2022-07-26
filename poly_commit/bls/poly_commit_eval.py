# Polynomial commitment using evaluation form

from ec import (G1FromBytes, G1Generator, G1Infinity, G2FromBytes, G2Generator,
                G2Infinity, JacobianPoint, default_ec, default_ec_twist,
                sign_Fq2, twist, untwist, y_for_x)
from fields import Fq
from pairing import ate_pairing
from poly_commit import poly_interp, get_single_proof
from poly_commit import poly_eval
from functools import reduce

g1 = G1Generator()
g2 = G2Generator()
order = default_ec.n

# secret of trusted setup
secret = Fq(order, 87362938561938363821)
nroots = 16
primitive = 7
roots = [Fq(order, primitive) ** (i * (order - 1) // nroots)  for i in range(nroots)]
sec_roots = [(secret ** nroots - Fq(order, 1)) * w / Fq(order, nroots) / (secret - w) * g1 for w in roots]

# elements in the vector
vec = [51234, 28374, 62734, 19823, 571763, 83746, 198384, 827512]
vec = [Fq(order, x) for x in vec]
xs = [Fq(order, 2 + i) for i in range(len(vec))]
coeffs = poly_interp(vec, xs)

ys = [poly_eval(coeffs, w) for w in roots]

# z = Fq(order, 2)
z = secret
pb = [(z ** nroots - Fq(order, 1)) * x / (z - x) / Fq(order, nroots) for x, y in zip(roots, ys)]
print(reduce(lambda x, y: x + y, [x * y for x, y in zip(pb, ys)]))
print(poly_eval(coeffs, secret))
# eval [f(s)]_1
print(poly_eval(coeffs, secret) * g1 == sum(yi * s for yi, s in zip(ys, sec_roots)))


zi = 1
z = xs[zi]
y = vec[zi]
qs0 = sum((yi - y) / (w - z) * s for yi, w, s in zip(ys, roots, sec_roots))

# s^i secrec vector, which is available to everybody (and cannot infer s)
sec_vec = [g1 * (secret ** i) for i in range(len(vec))]
commit = sum(s * c for s, c in zip(sec_vec, coeffs))
print("commitment is", commit)

zi = 1
# proof
qs = get_single_proof(coeffs, sec_vec, xs[zi].value, vec[zi])
print("proof is equal", qs == qs0)
# sz2 = g2 * secret + (g2 * x[zi]).negate()
# pair0 = ate_pairing(qs, sz2)
# print(pair0)

# cy = commit + (g1 * vec[zi]).negate()
# pair1 = ate_pairing(cy, g2)
# print(pair1)
# assert pair0 == pair1