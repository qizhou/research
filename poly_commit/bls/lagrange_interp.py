from ec import (G1FromBytes, G1Generator, G1Infinity, G2FromBytes, G2Generator,
                G2Infinity, JacobianPoint, default_ec, default_ec_twist,
                sign_Fq2, twist, untwist, y_for_x)
from fields import Fq

g1 = G1Generator()

q = default_ec.q

def poly_mul(coeffs1, coeffs2):
    # multiplication of two polynomials (convolution)
    nc = [Fq(q, 0)] * (len(coeffs1) + len(coeffs2) - 1)
    for i in range(len(coeffs1)):
        for j in range(len(coeffs2)):
            nc[i + j] += coeffs1[i] * coeffs2[j]
    return nc

def poly_eval(coeffs1, x):
    y = Fq(q, 1)
    s = Fq(q, 0)
    for c in coeffs1:
        s += y * c
        y = y * x
    return s
        
# secret of trusted setup
secret = 87362938561938363821

# elements in the vector
vec = [51234, 28374, 62734, 19823, 571763, 83746, 198384, 827512]
vec = [Fq(q, x) for x in vec]

# compute the coefficient of the vector using Lagrange interpolation
coeffs = [Fq(q, 0)] * len(vec) # from low to hight
for i in range(len(vec)):
    cc = [Fq(q, 1)]
    for j in range(len(vec)):
        if i == j:
            continue
        # print(cc)
        # print([vec[j], Fq(q, 1)])
        denom = Fq(q, i) - Fq(q, j)
        cc = poly_mul(cc, [-Fq(q, j) / denom, Fq(q, 1) / denom])
    cc = poly_mul(cc, [vec[i]])
    coeffs = [x + y for x, y in zip(cc, coeffs)]

for i in range(len(vec)):
    print(poly_eval(coeffs, Fq(q, i)).value)
    assert poly_eval(coeffs, Fq(q, i)) == vec[i]