# A simple plonk/PCS example code following
# zk-learning.org lecture 5

import random

from fft import fft
from pairing import ate_pairing
from poly_commit import PolyCommitment, ec_lincomb


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
    # vanishing poly (x^4 - 1)
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
    # assert t(1)= 1
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


def test_simple_plonk():
    # The trace of the plonk is
    # w^-1 w^-2 w^-3   | 5, 6, 1
    # ------------------------
    # w^0  w^1  w^2    | 5, 6, 11
    # w^3  w^4  w^5    | 6, 1, 7
    # w^6  w^7  w^8    | 11, 7, 77

    # selector
    S = [1, 1, 0]

    # assignments
    # T(w^-1) = T(w^0)
    # T(w^-2) = T(w^1) = T(w^3)
    # T(w^-3) = T(w^4)
    # T(w^-4) = T(w^8)
    # T(w^2) = T(w^6)
    # T(w^5) = T(w^7)
    order = 16
    pc = PolyCommitment()
    g = pc.pf.exp(7, (pc.pf.modulus-1) // order)
    assign_list = [
        [order - 1, 0],
        [order - 2, 1, 3],
        [order - 3, 4],
        [2, 6],
        [5, 7],
        [order - 4, 8]
    ]
    seq0 = [i for i in range(order)]
    seq1 = seq0[:]
    # TODO: check unassigned and make them to zero (so that T(x) is unique)
    for a in assign_list:
        for x in a:
            # make sure it is not assigned before
            assert seq1[x] == x
        for i in range(len(a)):
            seq1[a[i]] = a[i-1]
    # circuit setup (seq0 can be optimized)
    setup = (pc.getCommitment(seq0, g), pc.getCommitment(seq1, g))

    # input and trace
    input = [5, 6, 1, 77]
    T = [5, 6, 11, 6, 1, 7, 11, 7, 77, 0, 0, 0, 77, 1, 6, 5]

    # sanity check
    assert len(T) == order
    # check input (zero test on input subgroup)
    assert T[-len(input):] == [x for x in reversed(input)]
    # check assignment
    for a in assign_list:
        x = T[a[0]]
        for i in a:
            assert T[i] == x
    # check selector (zero test on selector subgroup)
    for i in range(len(S)):
        assert S[i] * (T[i*3] + T[i*3+1]) + (1 - S[i]) * T[i*3] * T[i*3+1] == T[i*3+2]
    
    # TODO: query and verify
    print("test_simple_plonk passed")

if __name__ == "__main__":
    test_batch()
    test_zero()
    test_prod_one()
    test_permutation()
    test_prescribed_permutation()
    test_simple_plonk()
   