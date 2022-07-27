
from ec import (G1FromBytes, G1Generator, G1Infinity, G2FromBytes, G2Generator,
                G2Infinity, JacobianPoint, default_ec, default_ec_twist,
                sign_Fq2, twist, untwist, y_for_x)
from fields import Fq
from pairing import ate_pairing
from poly_commit import poly_interp, get_single_proof
from poly_commit import poly_eval
from evaluation_form import fq_sum

g1 = G1Generator()
g2 = G2Generator()
order = default_ec.n

# secret of trusted setup
secret = Fq(order, 87362938561938363821)
nroots = 16
primitive = 7
roots = [Fq(order, primitive) ** (2 * i * (order - 1) // nroots)  for i in range(nroots // 2)]
roots += [Fq(order, primitive) ** ((2 * i + 1) * (order - 1) // nroots)  for i in range(nroots // 2)]
sec_roots = [(secret ** nroots - Fq(order, 1)) * w / Fq(order, nroots) / (secret - w) * g1 for w in roots]
phi = Fq(order, primitive) ** ((order - 1) // nroots) # w^1
sec_roots2 = [((secret / phi) ** nroots - Fq(order, 1)) * w / Fq(order, nroots) / ((secret / phi) - w) * g1 for w in roots]

# elements in the vector
vec = [51234, 28374, 62734, 19823, 571763, 83746, 198384, 827512]
vec = [Fq(order, x) for x in vec]
xs = roots[0: nroots//2]
coeffs = poly_interp(vec, xs)

# obtain y's on extended roots
ys0 = [poly_eval(coeffs, w) for w in roots]
ys1 = vec + [fq_sum([(z ** (nroots // 2) - Fq(order, 1)) * y * x / (z - x) / Fq(order, nroots // 2) for x, y in zip(roots[0 : nroots // 2], vec)]) for z in roots[nroots // 2 :]]
assert ys0 == ys1

# reconstruct y's on extended roots
ys2 = [fq_sum([((z / phi) ** (nroots // 2) - Fq(order, 1)) * y * x / ((z / phi) - x) / Fq(order, nroots // 2) for x, y in zip(roots[0 : nroots // 2], ys0[nroots // 2:])]) for z in roots[0: nroots // 2]]
assert ys2 == ys0[0 : nroots // 2]

# reconstruct the polynomial with other data points
coeffs1 = poly_interp(ys1[nroots // 2 :], roots[nroots // 2 :])
assert coeffs == coeffs1

