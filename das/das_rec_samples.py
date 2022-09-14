import random, time
import cProfile

from py_ecc import optimized_bls12_381 as b
from imported.kzg_proofs import get_root_of_unity, list_to_reverse_bit_order
from imported.fft import fft
from imported.poly_utils import PrimeField
from das_rec_utils import eval_poly_in_eval_form_with_coset, eval_poly_in_eval_form_with_coset_and_cache, inv_omega_diff

profiling = False

ALG_COEFF_NAIVE = 1
ALG_SAMPLE_NAIVE = 2
ALG_SAMPLE_COSET = 3
ALG_SAMPLE_COSET_CACHE = 4
ALG_SAMPLE_COSET_FFT = 5
algorithms = {1,2,3,4,5}

# number of samples after encoding
n_samples = 512

# number of field elements per sample
n_elements_ps = 16

# total field elements
n_elements = n_samples * n_elements_ps

# number of data blobs from users
n_blobs = n_elements // 2

root_of_unity = get_root_of_unity(n_elements)
root_of_unity2 = get_root_of_unity(n_blobs)
# order of FQ
modulus = b.curve_order
pf = PrimeField(modulus, 1)

# unencoded data
blobs = [random.randint(0, modulus - 1) for i in range(n_blobs)]

# polynomial coefficients
coeffs = fft(list_to_reverse_bit_order(blobs), modulus, root_of_unity2, True)

# encoded row data
y_row_raw = fft(coeffs + [0] * n_blobs, modulus, root_of_unity, False)
y_row = list_to_reverse_bit_order(y_row_raw)
assert y_row[0:n_blobs] == blobs

# randomly select n // 2 data that are available
selected = [i for i in range(n_samples)]
random.shuffle(selected)
missing = selected[n_samples // 2:]
selected = selected[0:n_samples // 2]

# lagrange interploation with available samples (not optimized)
rbo = list_to_reverse_bit_order([i for i in range(n_elements)])
x_row = [pf.exp(root_of_unity, x) for x in rbo]
xs = [x for i in selected for x in x_row[i*n_elements_ps:(i+1)*n_elements_ps]]
ys = [x for i in selected for x in y_row[i*n_elements_ps:(i+1)*n_elements_ps]]

if ALG_COEFF_NAIVE in algorithms:
    start_time = time.monotonic()
    if profiling:
        pr = cProfile.Profile()
        pr.enable()
    coeffs_rec = pf.lagrange_interp(xs, ys)
    assert coeffs == coeffs_rec
    print("Coefficient recovery used time: {} s".format(time.monotonic() - start_time))
    if profiling:
        pr.disable()
        pr.print_stats(sort="calls")

# reconstruct the rest samples natively (note that recovering (at most) half of the rest is enough)
nxs = [x for i in missing for x in x_row[i*n_elements_ps:(i+1)*n_elements_ps]]
nys = [x for i in missing for x in y_row[i*n_elements_ps:(i+1)*n_elements_ps]]

if ALG_SAMPLE_NAIVE in algorithms:
    start_time = time.monotonic()
    if profiling:
        pr = cProfile.Profile()
        pr.enable()
    nys_rec = pf.evaluate_polynomial_in_lagrange_interp_form(ys, xs, nxs)
    assert nys == nys_rec
    print("All sample recovery used time: {} s".format(time.monotonic() - start_time))
    if profiling:
        pr.disable()
        pr.print_stats(sort="calls")

# reconstruct the rest samples using coset information
if ALG_SAMPLE_COSET in algorithms:
    start_time = time.monotonic()
    if profiling:
        pr = cProfile.Profile()
        pr.enable()
    nys_rec = eval_poly_in_eval_form_with_coset(pf, ys, xs, x_row[0:n_elements_ps],  nxs)
    assert nys == nys_rec
    print("All sample recovery used time: {} s".format(time.monotonic() - start_time))
    if profiling:
        pr.disable()
        pr.print_stats(sort="calls")

# reconstruct the rest samples using coset information
if ALG_SAMPLE_COSET_CACHE in algorithms:
    start_time = time.monotonic()
    if profiling:
        pr = cProfile.Profile()
        pr.enable()
    xidx = [x for i in selected for x in rbo[i*n_elements_ps:(i+1)*n_elements_ps]]
    nxidx = [x for i in missing for x in rbo[i*n_elements_ps:(i+1)*n_elements_ps]]
    ru_list = [pf.exp(root_of_unity, i) for i in range(n_elements)]
    nys_rec = eval_poly_in_eval_form_with_coset_and_cache(pf, ys, ru_list, xidx, x_row[0:n_elements_ps], nxidx)
    assert nys == nys_rec
    print("All sample recovery used time: {} s".format(time.monotonic() - start_time))
    if profiling:
        pr.disable()
        pr.print_stats(sort="calls")

# reconstruct the rest samples using coset fft
def eval_poly_in_eval_form_with_fft(self, ys, ru_list, xidx, rus, nxidx):
    # rus - roots of unity of coset order

    # pre-compuate \omega^i - 1
    oi1 = [self.inv(ru_list[i] - 1) for i in range(1, len(ru_list))]

    # order of coset
    n = len(rus)
    # number of input samples
    m_in = len(xidx) // n
    m_out = len(nxidx) // n

    ru_coset = ru_list[len(ru_list) // n]
    rbo_coset = list_to_reverse_bit_order([i for i in range(n)])

    xs = [ru_list[i] for i in xidx]
    nxs = [ru_list[i] for i in nxidx]
    hns = [self.exp(x, n) for x in xs[::n]]
    hidx = [x for x in xidx[::n]]
    nhidx = [x for x in nxidx[::n]]

    # Generate master numerator polynomial, eg. (x - x1) * (x - x2) * ... * (x - xn)
    root = self.zpoly(hns)

    # evaluate g_i
    gs = []
    for i in range(m_in):
        gi = 1
        for j in range(m_in):
            if i == j:
                continue
            gi = self.mul(gi, (hns[i] - hns[j]))
        g = self.inv(gi)
        gs.append(g)

    # evaluate f^(i,j)_l
    fs = []
    for i in range(m_in):
        coeff = fft([ys[i*n+k] for k in rbo_coset], modulus, ru_coset, True)
        # div h_i
        coeff = [self.mul(c, ru_list[-hidx[i] * k]) for k, c in enumerate(coeff)]
        for j in range(m_out):
            # mul h_j
            coeff1 = [self.mul(c, ru_list[nhidx[j] * k]) for k, c in enumerate(coeff)]
            f = fft(coeff1, modulus, ru_coset, False)
            fs.extend([f[k] for k in rbo_coset])

    nys = []
    for i in range(m_out):
        mx = self.eval_poly_at(root, self.exp(nxs[i*n], n))
        # 1 / Z_{alpha_i}(h_k)
        denom = [inv_omega_diff(self, oi1, ru_list, nhidx[i] * n, hidx[j] * n) for j in range(m_in)]
        for j in range(n):
            ny = sum(g * f * d for g, f, d in zip(gs, fs[i*n+j::n*m_out], denom))
            ny = self.mul(mx, ny)
            nys.append(ny)

    return nys

if ALG_SAMPLE_COSET_FFT in algorithms:
    start_time = time.monotonic()
    if profiling:
        pr = cProfile.Profile()
        pr.enable()
    xidx = [x for i in selected for x in rbo[i*n_elements_ps:(i+1)*n_elements_ps]]
    nxidx = [x for i in missing for x in rbo[i*n_elements_ps:(i+1)*n_elements_ps]]
    ru_list = [pf.exp(root_of_unity, i) for i in range(n_elements)]
    nys_rec = eval_poly_in_eval_form_with_fft(pf, ys, ru_list, xidx, x_row[0:n_elements_ps], nxidx)
    assert nys == nys_rec
    print("All sample recovery used time: {} s".format(time.monotonic() - start_time))
    if profiling:
        pr.disable()
        pr.print_stats(sort="calls")