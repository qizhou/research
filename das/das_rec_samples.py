import random, time
import cProfile

from py_ecc import optimized_bls12_381 as b
from imported.kzg_proofs import get_root_of_unity, list_to_reverse_bit_order
from imported.fft import fft
from imported.poly_utils import PrimeField

profiling = True

ALG_COEFF_NAIVE = 1
ALG_SAMPLE_NAIVE = 2
ALG_SAMPLE_COSET = 3
ALG_SAMPLE_COSET_CACHE = 4
algorithms = {ALG_SAMPLE_COSET_CACHE}

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
def evaluate_polynomial_in_lagrange_interp_form_with_coset(self, ys, xs, rus, nxs):
    # rus - roots of unity of coset order

    n = len(rus)
    ni = self.inv(n)

    hns = [self.exp(x, n) for x in xs[::n]]
    hn1s = [self.exp(x, n - 1) for x in xs[::n]]

    # Generate master numerator polynomial, eg. (x - x1) * (x - x2) * ... * (x - xn)
    root = self.zpoly(hns)

    # evaluate y * denominators
    ygs = []
    for i in range(len(hns)):
        di = 1
        for j in range(len(hns)):
            if i == j:
                continue
            di = self.mul(di, (hns[i] - hns[j]))
        d = self.div(ni, di)
        d = self.div(d, hn1s[i])

        for j in range(n):
            ygs.append(self.mul(self.mul(ys[i*n+j], d), rus[j]))

    nys = []
    # batch inverse the single denominators for each basis
    invdenoms = self.multi_inv([nx - x for nx in nxs for x in xs])
    for i in range(len(nxs)):
        v = sum(x * y for x, y in zip(invdenoms[i*len(xs):(i+1)*len(xs)], ygs))
        ny = self.mul(self.eval_poly_at(root, self.exp(nxs[i], n)), v)
        nys.append(ny)

    return nys

if ALG_SAMPLE_COSET in algorithms:
    start_time = time.monotonic()
    if profiling:
        pr = cProfile.Profile()
        pr.enable()
    nys_rec = evaluate_polynomial_in_lagrange_interp_form_with_coset(pf, ys, xs, x_row[0:n_elements_ps],  nxs)
    assert nys == nys_rec
    print("All sample recovery used time: {} s".format(time.monotonic() - start_time))
    if profiling:
        pr.disable()
        pr.print_stats(sort="calls")

# reconstruct the rest samples using coset information
def inv_omega_diff(self, oi1, ru_list, idx1, idx2):
    if idx1 > idx2:
        return self.mul(ru_list[-idx2], oi1[idx1 - idx2 - 1])
    else:
        return self.mul(ru_list[-idx1], -oi1[idx2 - idx1 - 1])

def evaluate_polynomial_in_lagrange_interp_form_with_coset_and_cache(self, ys, ru_list, xidx, rus, nxidx):
    # rus - roots of unity of coset order

    # pre-compuate \omega^i - 1
    oi1 = [self.inv(ru_list[i] - 1) for i in range(1, len(ru_list))]

    n = len(rus)
    ni = self.inv(n)

    xs = [ru_list[i] for i in xidx]
    nxs = [ru_list[i] for i in nxidx]
    hns = [self.exp(x, n) for x in xs[::n]]
    hn1s = [self.exp(x, n - 1) for x in xs[::n]]

    # Generate master numerator polynomial, eg. (x - x1) * (x - x2) * ... * (x - xn)
    root = self.zpoly(hns)

    # evaluate y * denominators (without omega_j)
    ygs = []
    for i in range(len(hns)):
        di = 1
        for j in range(len(hns)):
            if i == j:
                continue
            di = self.mul(di, (hns[i] - hns[j]))
        d = self.div(ni, di)
        d = self.div(d, hn1s[i])

        for j in range(n):
            ygs.append(self.mul(self.mul(ys[i*n+j], d), rus[j]))

    nys = []
    # batch inverse the single denominators for each basis
    denoms = [inv_omega_diff(self, oi1, ru_list, i, j) for i in nxidx for j in xidx]
    for i in range(len(nxs)):
        v = sum(x * y for x, y in zip(denoms[i*len(xs):(i+1)*len(xs)], ygs))
        ny = self.mul(self.eval_poly_at(root, self.exp(nxs[i], n)), v)
        nys.append(ny)

    return nys

if ALG_SAMPLE_COSET_CACHE in algorithms:
    start_time = time.monotonic()
    if profiling:
        pr = cProfile.Profile()
        pr.enable()
    xidx = [x for i in selected for x in rbo[i*n_elements_ps:(i+1)*n_elements_ps]]
    nxidx = [x for i in missing for x in rbo[i*n_elements_ps:(i+1)*n_elements_ps]]
    ru_list = [pf.exp(root_of_unity, i) for i in range(n_elements)]
    nys_rec = evaluate_polynomial_in_lagrange_interp_form_with_coset_and_cache(pf, ys, ru_list, xidx, x_row[0:n_elements_ps], nxidx)
    assert nys == nys_rec
    print("All sample recovery used time: {} s".format(time.monotonic() - start_time))
    if profiling:
        pr.disable()
        pr.print_stats(sort="calls")