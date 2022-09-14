# rus - roots of unity of coset order

from imported.poly_utils import PrimeField
from py_ecc import optimized_bls12_381 as b
from imported.kzg_proofs import get_root_of_unity, list_to_reverse_bit_order
from imported.fft import fft
from das_rec_utils import inv_omega_diff



# order of FQ
modulus = b.curve_order

pf = PrimeField(modulus, 1)

# order all data
m = 16
ru = get_root_of_unity(m)
ru_list = [pf.exp(ru, i) for i in range(m)]

# order of coset
n = 4
rus_coset = get_root_of_unity(m // n)

rbo = list_to_reverse_bit_order([i for i in range(m)])
x_row = [ru_list[i] for i in rbo]
ys = [123456 + i for i in range(m//2)]

coeff = pf.lagrange_interp(x_row[0:m//2], ys)
y_row = ys[:]
y_row.extend(pf.eval_poly_at(coeff, x) for x in x_row[m//2:])

xidx = rbo[0:m//2]
nxidx = rbo[m//2:]

# pre-compuate \omega^i - 1
oi1 = [pf.inv(ru_list[i] - 1) for i in range(1, len(ru_list))]

# number of input samples
m_in = len(xidx) // n
m_out = len(nxidx) // n

ru_coset = ru_list[m // n]
rbo_coset = list_to_reverse_bit_order([i for i in range(n)])

xs = [ru_list[i] for i in xidx]
nxs = [ru_list[i] for i in nxidx]
hns = [pf.exp(x, n) for x in xs[::n]]
hidx = [x for x in xidx[::n]]
nhidx = [x for x in nxidx[::n]]

# Generate master numerator polynomial, eg. (x - x1) * (x - x2) * ... * (x - xn)
root = pf.zpoly(hns)

# evaluate g_i
gs = []
for i in range(m_in):
    gi = 1
    for j in range(m_in):
        if i == j:
            continue
        gi = pf.mul(gi, (hns[i] - hns[j]))
    g = pf.inv(gi)
    gs.append(g)

# evaluate f^(i,j)_l
fs = []
for i in range(m_in):
    coeff = fft([ys[i*n+k] for k in rbo_coset], modulus, ru_coset, True)
    # div h_i
    coeff = [pf.mul(c, ru_list[-hidx[i] * k]) for k, c in enumerate(coeff)]
    coeff_cmp = pf.lagrange_interp(xs[i*n:(i+1)*n], ys[i*n:(i+1)*n])
    assert coeff == coeff_cmp
    for j in range(m_out):
        # mul h_j
        coeff1 = [pf.mul(c, ru_list[nhidx[j] * k]) for k, c in enumerate(coeff)]
        f = fft(coeff1, modulus, ru_coset, False)
        f = [f[k] for k in rbo_coset]
        f_cmp = [pf.eval_poly_at(coeff, x) for x in nxs[j*n:(j+1)*n]]
        assert f == f_cmp
        fs.extend(f)

nys = []
for i in range(m_out):
    mx = pf.eval_poly_at(root, pf.exp(nxs[i*n], n))
    # 1 / Z_{alpha_i}(h_k)
    denom = [inv_omega_diff(pf, oi1, ru_list, nhidx[i] * n, hidx[j] * n) for j in range(m_in)]
    for j in range(n):
        ny = sum(g * f * d for g, f, d in zip(gs, fs[i*n+j::n*m_out], denom))
        ny = pf.mul(mx, ny)
        nys.append(ny)

assert nys == y_row[m // 2:]
