from ec import (G1FromBytes, G1Generator, G1Infinity, G2FromBytes, G2Generator,
                G2Infinity, JacobianPoint, default_ec, default_ec_twist,
                sign_Fq2, twist, untwist, y_for_x)
from fields import Fq
from pairing import ate_pairing

g1 = G1Generator()

g2 = G2Generator()

q = default_ec.q

order = default_ec.n

def poly_mul(coeffs1, coeffs2):
    # multiplication of two polynomials (convolution)
    q = coeffs1[0].Q
    nc = [Fq(q, 0)] * (len(coeffs1) + len(coeffs2) - 1)
    for i in range(len(coeffs1)):
        for j in range(len(coeffs2)):
            nc[i + j] += coeffs1[i] * coeffs2[j]
    return nc

def poly_eval(coeffs1, x):
    q = coeffs1[0].Q
    y = Fq(q, 1)
    s = Fq(q, 0)
    for c in coeffs1:
        s += y * c
        y = y * x
    return s

def poly_div(num, den):
    r = []
    tmp = num[:]
    for i in range(len(num) - len(den) + 1, 0, -1):
        v = tmp[i] / den[-1]
        r.append(v)
        for j in range(len(den)):
            tmp[i + j - len(den) + 1] = tmp[i + j - len(den) + 1] - den[j] * v
    r.reverse()
    return r, tmp[0:len(den)-1]

def poly_interp(vec, x = None):
    # compute the coefficient of the vector using Lagrange interpolation
    q = vec[0].Q
    coeffs = [Fq(q, 0)] * len(vec) # from low to hight
    if x == None:
        x = [Fq(q, i) for i in range(len(vec))]
    for i in range(len(vec)):
        cc = [Fq(q, 1)]
        for j in range(len(vec)):
            if i == j:
                continue
            denom = x[i] - x[j]
            cc = poly_mul(cc, [-x[j] / denom, Fq(q, 1) / denom])
        cc = poly_mul(cc, [vec[i]])
        coeffs = [x + y for x, y in zip(cc, coeffs)]
    return coeffs

def get_single_proof(coeffs, sec_vec, z, y):
    px = coeffs[:]
    px[0] = px[0] - y
    qx, rem = poly_div(px, [-z, Fq(order, 1)])
    assert rem == [Fq(order, 0)]
    qs = sum(s * c for s, c in zip(sec_vec[0:len(qx)], qx))
    return qs

def proof_example():
    # secret of trusted setup
    secret = 87362938561938363821

    # elements in the vector
    vec = [51234, 28374, 62734, 19823, 571763, 83746, 198384, 827512]
    vec = [Fq(order, x) for x in vec]
    coeffs = poly_interp(vec)

    # s^i secrec vector, which is available to everybody (and cannot infer s)
    sec_vec = [g1 * (secret ** i) for i in range(len(vec))]
    commit = sum(s * c for s, c in zip(sec_vec, coeffs))
    print("commitment is", commit)

    z = 1
    # proof
    qs = get_single_proof(coeffs, sec_vec, Fq(order, z), vec[z])
    sz2 = g2 * secret + (g2 * z).negate()
    pair0 = ate_pairing(qs, sz2)
    print(pair0)

    cy = commit + (g1 * vec[z]).negate()
    pair1 = ate_pairing(cy, g2)
    print(pair1)
    assert pair0 == pair1

if __name__ == "__main__":
    proof_example()
