# A simple polynomial commitment interface

import random
import hashlib

from fft import fft
from ec import (G1Generator, G2Generator, default_ec)
from poly_utils import PrimeField
from pairing import ate_pairing

class PolyCommitment:
    def __init__(self, setup=None):
        assert setup == None
        self.modulus = default_ec.n
        self.pf = PrimeField(self.modulus)  # order of Elliptic curve
        if setup == None:
            self.secret = random.randint(0, self.pf.modulus - 1)
            self.G1 = G1Generator()
            self.G2 = G2Generator()
            self.setup_vec1 = []
            self.setup_vec2 = []
        else:
            assert False

    def getSetupVector1(self, length):
        for i in range(len(self.setup_vec1), length):
            self.setup_vec1.append(self.G1 * (self.secret ** i))
        return self.setup_vec1[0:length]

    def getSetupVector2(self, length):
        for i in range(len(self.setup_vec2), length):
            self.setup_vec2.append(self.G2 * (self.secret ** i))
        return self.setup_vec2[0:length]

    # get the commitment of a polynomial in evaluation form
    # return a curve point
    def getCommitment(self, evals, g):
        # g - roots of unity
        coeffs = fft(evals, self.pf.modulus, g, inv=True)
        sv = self.getSetupVector1(len(coeffs))
        return sum(s * c for s, c in zip(sv, coeffs))
    
    # get the commitment of a polynomial in evaluation form
    # return a curve point
    def getCommitmentByCoeffs(self, coeffs):
        # g - roots of unity
        sv = self.getSetupVector1(len(coeffs))
        return sum(s * c for s, c in zip(sv, coeffs))

    def getSingleProofByEvalIdx(self, evals, g, idx):
        # g - primitive root of unity
        # order - order of g
        # n - g^n root of unity
        # qx = (x^n - 1) / (x-x0)
        coeffs = fft(evals, self.pf.modulus, g, inv=True)
        y0 = evals[idx]
        x0 = self.pf.exp(g, idx)
        return self.getSingleProofAt(coeffs, x0, y0)

    def getSingleProofAt(self, coeffs, x0, y0):
        coeffs = coeffs[:]
        coeffs[0] = coeffs[0] - y0
        qx = self.pf.div_polys(coeffs, [self.modulus-x0, 1])
        sv = self.getSetupVector1(len(qx))
        return sum(s * c for s, c in zip(sv, qx))

    def verifySingleProof(self, commit, proof, x0, y0):
        # verify using
        # e(c - [y0], [1]) = e(proof, [tau - x0])
        sz2 = self.G2 * self.secret + (self.G2 * x0).negate()
        pair0 = ate_pairing(proof, sz2)

        cy = commit + (self.G1 * y0).negate()
        pair1 = ate_pairing(cy, self.G2)
        return pair0 == pair1
    
    def verifySingleProof2(self, commit, proof, x0, y0):
        # verify using
        # e(c - [y0] + proof * x0, [1]), e(proof, [tau])
        pair0 = ate_pairing(proof, self.G2 * self.secret)

        cy = commit + (self.G1 * y0).negate() + proof * x0
        pair1 = ate_pairing(cy, self.G2)
        return pair0 == pair1
    
    def rand(self):
        return random.randint(0, self.modulus - 1)


def ec_lincomb(points, vs):
    # simple, inefficient linear combination
    ps = [p * v for p, v in zip(points, vs)]
    return sum(ps[1:], start=ps[0])


def test_poly_commitment():
    pc = PolyCommitment()
    G = pc.pf.exp(7, (pc.pf.modulus-1) // 4)
    evals = [235, 2346, 132213, 61232]
    commit = pc.getCommitment(evals, G)
    proof = pc.getSingleProofByEvalIdx(evals, G, 1) # w^1
    assert pc.verifySingleProof(commit, proof, G, 2346)
    assert pc.verifySingleProof2(commit, proof, G, 2346)
    print("poly_commitment test passed")


def test_full_poly():
    # Verify full data blobs in EIP-4844 setup
    pc = PolyCommitment()
    G = pc.pf.exp(7, (pc.pf.modulus-1) // 4)
    evals = [235, 2346, 132213, 61232]
    commit = pc.getCommitment(evals, G)

    # given evals, check evals matches the commitment with single open
    # note that we could also do the check by
    # - find the evals coeffs
    # - multiple setup s^x G's
    # which may be expensive in contract.
    def get_proof(pc, commit, evals):
        # find a random evaluation point using Fiat-Shamir heuristic
        # where inputs are commit + evals
        data = bytes(commit)
        for eval in evals:
            # BLS modulus is in 256-bit
            data += eval.to_bytes(32, byteorder="big")
        # simple hash to point
        r = int.from_bytes(hashlib.sha256(data).digest(), byteorder="big") % default_ec.n

        # use barycentric formula to calculate the point with evaluations
        pf = pc.pf
        yr = pf.eval_barycentric(r, [pf.exp(G, i) for i in range(4)], evals)

        # get the proof at random r (this part is off-chain)
        return pc.getSingleProofAt(fft(evals, pf.modulus, G, inv=True), r, yr)

    def verify_proof(pc, commit, evals, proof):
        # find a random evaluation point using Fiat-Shamir heuristic
        # where inputs are commit + evals
        data = bytes(commit)
        for eval in evals:
            # BLS modulus is in 256-bit
            data += eval.to_bytes(32, byteorder="big")
        # simple hash to point
        r = int.from_bytes(hashlib.sha256(data).digest(), byteorder="big") % default_ec.n

        # use barycentric formula to calculate the point with evaluations
        pf = pc.pf
        yr = pf.eval_barycentric(r, [pf.exp(G, i) for i in range(4)], evals)

        return pc.verifySingleProof(commit, proof, r, yr)

    proof = get_proof(pc, commit, evals)

    # single open to verify
    assert verify_proof(pc, commit, evals, proof)
    print("full_poly test passed")


def test_prod1():
    pc = PolyCommitment()
    order = 16
    G = pc.pf.exp(7, (pc.pf.modulus-1) // order)

    # obtain two polynomials
    p1 = [random.randint(0, pc.modulus -1) for i in range(4)]
    p2 = [random.randint(0, pc.modulus -1) for i in range(4)]

    # obtain p1(x) * p2(x)
    q = pc.pf.mul_polys(p1, p2)

    # commit and random evaluation point
    c_p1 = pc.getCommitmentByCoeffs(p1)
    c_p2 = pc.getCommitmentByCoeffs(p2)
    c_q = pc.getCommitmentByCoeffs(q)
    r = random.randint(0, pc.modulus - 1)
    
    # to verify p1(x) * p2(x) = q(x), find r and evaluate so that they are the same
    y_p1_r = pc.pf.eval_poly_at(p1, r)
    y_p2_r = pc.pf.eval_poly_at(p2, r)
    y_q_r = pc.pf.eval_poly_at(q, r)
    proof_p1_r = pc.getSingleProofAt(p1, r, y_p1_r)
    proof_p2_r = pc.getSingleProofAt(p2, r, y_p2_r)
    proof_q_r = pc.getSingleProofAt(q, r, y_q_r)

    # verify
    assert y_p1_r * y_p2_r % pc.modulus == y_q_r
    assert pc.verifySingleProof(c_p1, proof_p1_r, r, y_p1_r)
    assert pc.verifySingleProof(c_p2, proof_p2_r, r, y_p2_r)
    assert pc.verifySingleProof(c_q, proof_q_r, r, y_q_r)
    print("test_prod1 passed") 


def test_prod1_linearization():
    pc = PolyCommitment()
    order = 16
    G = pc.pf.exp(7, (pc.pf.modulus-1) // order)

    # obtain two polynomials
    p1x = [random.randint(0, pc.modulus -1) for i in range(4)]
    p2x = [random.randint(0, pc.modulus -1) for i in range(4)]

    # obtain p1(x) * p2(x)
    qx = pc.pf.mul_polys(p1x, p2x)

    # commit and random evaluation point
    zeta = random.randint(0, pc.modulus - 1)
    y_p1_r = pc.pf.eval_poly_at(p1x, zeta)
    # construct r(x) = p1(r) * p2(x) - q(x)
    rx = pc.pf.sub_polys(pc.pf.mul_polys([y_p1_r], p2x), qx)
    # test r(zeta) = 0

    # batch KZG
    mu = random.randint(0, pc.modulus - 1)
    # kx = p1(x) + mu r(x)
    c_p1 = pc.getCommitmentByCoeffs(p1x)
    c_p2 = pc.getCommitmentByCoeffs(p2x)
    c_q = pc.getCommitmentByCoeffs(qx)
    
    kx = pc.pf.add_polys(p1x, pc.pf.mul_polys([mu], rx))
    proof_kx_zeta = pc.getSingleProofAt(kx, zeta, 0)
    proof_p1_zeta = pc.getSingleProofAt(p1x, zeta, 0)

    
    # verify
    c_r = c_p2 * y_p1_r + c_q.negate()
    c_k = c_p1 + mu * c_r
    assert pc.verifySingleProof(c_p1, proof_p1_zeta, zeta, y_p1_r)
    assert pc.verifySingleProof(c_k, proof_kx_zeta, zeta, y_p1_r)
    print("test_prod1_linearization passed")


def test_batch():
    # Test batch KZG with mul polys with single pairing
    # e(sum(c_i * r^i) + sum(proof_i * x_i * r^i)  -  sum(r^i y_i), [1]) = e(sum(proof_i * r^i), [1])

    pc = PolyCommitment()
    order = 16
    G = pc.pf.exp(7, (pc.pf.modulus-1) // order)

    npoly = 3
    ps = []
    xs = []
    ys = []
    qs = []
    cs = []
    r = random.randint(0, pc.modulus - 1) # random linear combination
    for i in range(npoly):
        p = [random.randint(0, pc.modulus -1) for i in range(4)]
        c = pc.getCommitmentByCoeffs(p)
        ps.append(p)
        x = random.randint(0, pc.modulus - 1)
        y = pc.pf.eval_poly_at(p, x)
        q = pc.getSingleProofAt(p, x, y)
        xs.append(x)
        ys.append(y)
        qs.append(q)
        cs.append(c)

    rs = [pow(r, i, pc.pf.modulus) for i in range(npoly)]
    xrs = [xs[i] * pow(r, i, pc.pf.modulus) % pc.modulus for i in range(npoly)]
    cr = ec_lincomb(cs, rs)
    pxr = ec_lincomb(qs, xrs)
    yr = ec_lincomb(ys, rs)
    pr = ec_lincomb(qs, rs)

    left = ate_pairing(cr + pxr + yr * pc.G1.negate(), pc.G2)
    right = ate_pairing(pr, pc.G2 * pc.secret)
    assert left == right
    print("test_batch passd")


def test_zero():
    # Test if a poly is zero in a subgroup

    pc = PolyCommitment()
    degree = 16
    G = pc.pf.exp(7, (pc.pf.modulus-1) // degree)
    order = 4
    G0 = pc.pf.exp(7, (pc.pf.modulus-1) // order)

    # construct a poly with subgroup zero
    evals = [0 if i % order == 0 else random.randint(0, pc.modulus -1) for i in range(16)]
    p = fft(evals, pc.modulus, G, inv=True)
    cp = pc.getCommitmentByCoeffs(p)
    # vanishing poly
    z = [pc.modulus - 1] + [0] * (order - 1) + [1]

    # TODO: shift fft to improve div
    q, rem = pc.pf.div_polys_with_rem(p, z)
    cq = pc.getCommitmentByCoeffs(q)
    assert rem == [0] * order

    r = pc.rand()
    py = pc.pf.eval_poly_at(p, r)
    qy = pc.pf.eval_poly_at(q, r)

    # TODO: query py, qy with cp and cq (batch)
    assert py == qy * (pow(r, order, pc.modulus) - 1) % pc.modulus
    print("test_zero passed")

def test_prod_one():
    # Test if the prod of a poly in a subgroup is 1

    pc = PolyCommitment()

    order = 4
    omega = pc.pf.exp(7, (pc.pf.modulus-1) // order)
    evals = [pc.rand() for i in range(order - 1)]
    

    # construct t such that t(w^0) = 1, t(wx) = f(x) t(x)
    # (note that it is a bit different with lecture notes)
    t = [1]
    for x in evals:
        t.append(t[-1] * x % pc.modulus)
    evals.append(pc.pf.div(1, t[-1]))
    coeffs = fft(evals, pc.modulus, omega, inv=True)
    c_p = pc.getCommitmentByCoeffs(coeffs)

    coeffs_t = fft(t, pc.modulus, omega, inv=True)
    c_t = pc.getCommitmentByCoeffs(coeffs_t)

    coeffs_t1 = pc.pf.sub_polys(pc.pf.shift_poly(coeffs_t, omega), pc.pf.mul_polys(coeffs, coeffs_t))

    # vanishing poly
    z = [pc.modulus - 1] + [0] * (order - 1) + [1]
    q, rem = pc.pf.div_polys_with_rem(coeffs_t1, z)
    assert rem == [0] * order

    r = pc.rand()
    # TODO: query t(wr), f(r), t(r), t(1), q(r) (using batch)
    t_wr = pc.pf.eval_poly_at(coeffs_t, omega * r)
    f_r = pc.pf.eval_poly_at(coeffs, r)
    t_r = pc.pf.eval_poly_at(coeffs_t,  r)
    q_r = pc.pf.eval_poly_at(q, r)
    # assert f(1)= 1
    assert q_r * (pow(r, order, pc.modulus) - 1) % pc.modulus == (t_wr - f_r * t_r) % pc.modulus
    print("test_prod_one passed")


def test_permutation():
    # Test if the permutation of two polys in a subgroup

    pc = PolyCommitment()

    order = 4
    omega = pc.pf.exp(7, (pc.pf.modulus-1) // order)
    p0 = [pc.rand() for i in range(order)]
    p1 = p0[:]
    random.shuffle(p1)
    coeffs_p0 = fft(p0, pc.modulus, omega, inv=True)
    coeffs_p1 = fft(p1, pc.modulus, omega, inv=True)
    

    c_p0 = pc.getCommitmentByCoeffs(coeffs_p0)
    c_p1 = pc.getCommitmentByCoeffs(coeffs_p1)
    
    theta = pc.rand()
    f0 = [v - theta for v in p0]
    f1 = [v - theta for v in p1]
    coeffs_f0 = fft(f0, pc.modulus, omega, inv=True)
    coeffs_f1 = fft(f1, pc.modulus, omega, inv=True)
    # f0 / f1
    evals = [pc.pf.div(v0, v1) for v0, v1 in zip(f0, f1)]
    
    # construct t such that t(w^0) = 1, t(wx) f1(x) = f0(x) t(x)
    # where f(x) = p(x) - theta
    # (note that it is a bit different with lecture notes)
    t = [1]
    for x in evals[:-1]:
        t.append(t[-1] * x % pc.modulus)

    coeffs_t = fft(t, pc.modulus, omega, inv=True)
    c_t = pc.getCommitmentByCoeffs(coeffs_t)

    coeffs_t1 = pc.pf.sub_polys(
        pc.pf.mul_polys(pc.pf.shift_poly(coeffs_t, omega), coeffs_f1),
        pc.pf.mul_polys(coeffs_t, coeffs_f0)
    )

    # vanishing poly
    z = [pc.modulus - 1] + [0] * (order - 1) + [1]
    q, rem = pc.pf.div_polys_with_rem(coeffs_t1, z)
    assert rem == [0] * order

    r = pc.rand()
    # TODO: query t(wr), p0(r), p1(r), t(r), t(1), q(r) (using batch)
    t_wr = pc.pf.eval_poly_at(coeffs_t, omega * r)
    f0_r = pc.pf.sub(pc.pf.eval_poly_at(coeffs_p0, r), theta)
    f1_r = pc.pf.sub(pc.pf.eval_poly_at(coeffs_p1, r), theta)
    t_r = pc.pf.eval_poly_at(coeffs_t,  r)
    q_r = pc.pf.eval_poly_at(q, r)
    # assert t(1)= 1
    assert q_r * (pow(r, order, pc.modulus) - 1) % pc.modulus == (t_wr * f1_r - f0_r * t_r) % pc.modulus
    print("test_permutation passed")


def test_prescribed_permutation():
    # Test if the permutation of two polys in a subgroup

    pc = PolyCommitment()

    order = 4
    omega = pc.pf.exp(7, (pc.pf.modulus-1) // order)
    p0 = [pc.rand() for i in range(order)]
    p1 = p0[:]
    random.shuffle(p1)
    coeffs_p0 = fft(p0, pc.modulus, omega, inv=True)
    coeffs_p1 = fft(p1, pc.modulus, omega, inv=True)

    c_p0 = pc.getCommitmentByCoeffs(coeffs_p0)
    c_p1 = pc.getCommitmentByCoeffs(coeffs_p1)

    p0 = [pc.rand() for i in range(order)]
    seq0 = [i for i in range(order)] # can be simply seq0(x) = x
    seq1 = seq0[:]
    random.shuffle(seq1)
    p1 = [p0[i] for i in seq1]
    coeffs_p0 = fft(p0, pc.modulus, omega, inv=True)
    coeffs_p1 = fft(p1, pc.modulus, omega, inv=True)
    coeffs_seq0 = fft(seq0, pc.modulus, omega, inv=True)    
    coeffs_seq1 = fft(seq1, pc.modulus, omega, inv=True)
    
    theta = pc.rand()
    gamma = pc.rand()
    f0 = [v * gamma - s - theta for v, s in zip(p0, seq0)]
    f1 = [v * gamma - s - theta for v, s in zip(p1, seq1)]
    coeffs_f0 = fft(f0, pc.modulus, omega, inv=True)
    coeffs_f1 = fft(f1, pc.modulus, omega, inv=True)
    # f0 / f1
    evals = [pc.pf.div(v0, v1) for v0, v1 in zip(f0, f1)]
    
    # construct t such that t(w^0) = 1, t(wx) f1(x) = f0(x) t(x)
    # where f(x) = p(x) * gamma - seq(x) - theta
    # (note that it is a bit different with lecture notes)
    t = [1]
    for x in evals[:-1]:
        t.append(t[-1] * x % pc.modulus)

    coeffs_t = fft(t, pc.modulus, omega, inv=True)
    c_t = pc.getCommitmentByCoeffs(coeffs_t)

    coeffs_t1 = pc.pf.sub_polys(
        pc.pf.mul_polys(pc.pf.shift_poly(coeffs_t, omega), coeffs_f1),
        pc.pf.mul_polys(coeffs_t, coeffs_f0)
    )

    # vanishing poly
    z = [pc.modulus - 1] + [0] * (order - 1) + [1]
    q, rem = pc.pf.div_polys_with_rem(coeffs_t1, z)
    assert rem == [0] * order

    r = pc.rand()
    # TODO: query t(wr), p0(r), p1(r), t(r), t(1), q(r), seq0(r), seq1(r) (using batch)
    t_wr = pc.pf.eval_poly_at(coeffs_t, omega * r)
    f0_r = pc.pf.sub(pc.pf.eval_poly_at(coeffs_p0, r) * gamma - pc.pf.eval_poly_at(coeffs_seq0, r), theta)
    f1_r = pc.pf.sub(pc.pf.eval_poly_at(coeffs_p1, r) * gamma - pc.pf.eval_poly_at(coeffs_seq1, r), theta)
    t_r = pc.pf.eval_poly_at(coeffs_t,  r)
    q_r = pc.pf.eval_poly_at(q, r)
    # assert t(1)= 1
    assert q_r * (pow(r, order, pc.modulus) - 1) % pc.modulus == (t_wr * f1_r - f0_r * t_r) % pc.modulus
    print("test_perscribed_permutation passed")


if __name__ == "__main__":
    # test_poly_commitment()
    # test_batch()
    # test_zero()
    test_prod_one()
    test_permutation()
    test_prescribed_permutation()
    # test_full_poly()
    # test_prod1()
    test_prod1_linearization()
        
        
        
    