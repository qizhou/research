# R1CS to QAP conversion
# Using Vitalik as an example but use finite fields
from poly_utils import PrimeField

PF = PrimeField(13)

# R1CS A, B, C matrics
A = [[0, 1, 0, 0, 0, 0],
     [0, 0, 0, 1, 0, 0],
     [0, 1, 0, 0, 1, 0],
     [5, 0, 0, 0, 0, 1]]

B = [[0, 1, 0, 0, 0, 0],
     [0, 1, 0, 0, 0, 0],
     [1, 0, 0, 0, 0, 0],
     [1, 0, 0, 0, 0, 0]]

C = [[0, 0, 0, 1, 0, 0],
     [0, 0, 0, 0, 1, 0],
     [0, 0, 0, 0, 0, 1],
     [0, 0, 1, 0, 0, 0]]


# solution
s = [1, 3, 35, 9, 27, 30]

# check if s satisfied R1CS
def r1cs_check(A, B, C, s):
    for i in range(len(A)):
        ap = sum([a * x for a, x in zip(A[i], s)])
        bp = sum([b * x for b, x in zip(B[i], s)])
        cp = sum([c * x for c, x in zip(C[i], s)])
        if PF.sub(PF.mul(ap, bp), cp) != 0:
            return False
    return True

# obtain polynomials
def r1cs_to_poly(A):
    xs = [i + 1 for i in range(len(A))]
    Ap = []
    for i in range(len(A[0])):
        ys = [j[i] for j in A]
        Ap.append(PF.lagrange_interp(xs, ys))
    return Ap

# check QAP with multiple evaluation
def qap_multi_check(Ap, Bp, Cp, s):
    Aps = PF.linearcomb_polys(Ap, s)
    Bps = PF.linearcomb_polys(Bp, s)
    Cps = PF.linearcomb_polys(Cp, s)
    # check constraint one by one
    xs = [i + 1 for i in range(len(A))]
    for x in xs:
        a = PF.eval_poly_at(Aps, x)
        b = PF.eval_poly_at(Bps, x)
        c = PF.eval_poly_at(Cps, x)
        if PF.sub(PF.mul(a, b), c) != 0:
            return False
    return True

# check QAP with single evaluation
def qap_single_check(Ap, Bp, Cp, s):
    Aps = PF.linearcomb_polys(Ap, s)
    Bps = PF.linearcomb_polys(Bp, s)
    Cps = PF.linearcomb_polys(Cp, s)
    # check constraint with single evaluation
    lhs = PF.sub_polys(PF.mul_polys(Aps, Bps), Cps)
    rhs = PF.zpoly([i + 1 for i in range(len(A))])
    rem = PF.mod_polys(lhs, rhs)
    return rem == [0 for i in range(len(rhs) - 1)]


assert r1cs_check(A, B, C, s)
print("passed R1CS check")

Ap = r1cs_to_poly(A)
Bp = r1cs_to_poly(B)
Cp = r1cs_to_poly(C)
assert qap_multi_check(Ap, Bp, Cp, s)
assert qap_single_check(Ap, Bp, Cp, s)
print("passed QAP check")