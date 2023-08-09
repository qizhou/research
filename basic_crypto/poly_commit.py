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


if __name__ == "__main__":
    test_poly_commitment()
    test_full_poly()
    test_prod1()
    test_prod1_linearization()
        
        
        
    