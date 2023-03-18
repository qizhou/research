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
        # g - primitive root of unity
        # order - order of g
        # n - g^n root of unity
        # qx = (x^n - 1) / (x-x0)
        coeffs = coeffs[:]
        coeffs[0] = coeffs[0] - y0
        qx = self.pf.div_polys(coeffs, [self.modulus-x0, 1])
        sv = self.getSetupVector1(len(qx))
        return sum(s * c for s, c in zip(sv, qx))

    def verifySingleProof(self, commit, proof, x0, y0):
        sz2 = self.G2 * self.secret + (self.G2 * x0).negate()
        pair0 = ate_pairing(proof, sz2)

        cy = commit + (self.G1 * y0).negate()
        pair1 = ate_pairing(cy, self.G2)
        return pair0 == pair1


def test_poly_commitment():
    pc = PolyCommitment()
    G = pc.pf.exp(7, (pc.pf.modulus-1) // 4)
    evals = [235, 2346, 132213, 61232]
    commit = pc.getCommitment(evals, G)
    proof = pc.getSingleProofByEvalIdx(evals, G, 1) # w^1
    assert pc.verifySingleProof(commit, proof, G, 2346)
    print("poly_commitment test passed")


def test_full_poly():
    pc = PolyCommitment()
    G = pc.pf.exp(7, (pc.pf.modulus-1) // 4)
    evals = [235, 2346, 132213, 61232]
    commit = pc.getCommitment(evals, G)

    # given evals, check evals matches the commitment with single open
    # note that we could also do the check by
    # - find the evals coeffs
    # - multiple setup s^x G's
    # which may be expensive in contract.

    # find a random evaluation point using Fiat-Shamir heuristic
    # where inputs are commit + evals
    data = bytes(commit)
    for eval in evals:
        # BLS modulus is in 256-bit
        data += eval.to_bytes(32, byteorder="big")
    # simple hash to point
    r = int.from_bytes(hashlib.sha256(b"1234").digest(), byteorder="big") % default_ec.n

    # use barycentric formula to calculate the point with evaluations
    pf = pc.pf
    yr = pf.eval_barycentric(r, [pf.exp(G, i) for i in range(4)], evals)

    # get the proof at random r (this part is off-chain)
    proof = pc.getSingleProofAt(fft(evals, pf.modulus, G, inv=True), r, yr)
    # single open to verify
    assert pc.verifySingleProof(commit, proof, r, yr)
    print("full_poly test passed")

if __name__ == "__main__":
    test_poly_commitment()
    test_full_poly()
        
        
        
    