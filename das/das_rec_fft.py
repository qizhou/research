import random, time
import cProfile

from py_ecc import optimized_bls12_381 as b
from imported.kzg_proofs import get_root_of_unity, list_to_reverse_bit_order
from imported.fft import fft, expand_root_of_unity
from imported.poly_utils import PrimeField
from das_rec_utils import eval_poly_in_eval_form_with_coset, eval_poly_in_eval_form_with_coset_and_cache, inv_omega_diff
from recovery import erasure_code_recover

profiling = False

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

# reconstruct the rest samples natively (note that recovering (at most) half of the rest is enough)
nxs = [x for i in missing for x in x_row[i*n_elements_ps:(i+1)*n_elements_ps]]
nys = [x for i in missing for x in y_row[i*n_elements_ps:(i+1)*n_elements_ps]]

# reconstruct the rest samples using coset fft
def rec_poly_with_coset_fft(self, ys, ru_list, xidx, rus, nxidx, nys):
    # ys - received samples with each sample in reverse bit order
    # rus - roots of unity of coset order

    # pre-compuate \omega^i - 1
    # oi1 = [self.inv(ru_list[i] - 1) for i in range(1, len(ru_list))]
    # xs = [w^i], i in xidx

    # order of coset (number of data points in a sample)
    n = len(rus)
    # number of input samples
    m_in = len(xidx) // n
    m_out = len(nxidx) // n

    ru_coset = ru_list[len(ru_list) // n]
    rbo_coset = list_to_reverse_bit_order([i for i in range(n)])

    # xs = [ru_list[i] for i in xidx]
    # nxs = [ru_list[i] for i in nxidx]
    hidx = [x for x in xidx[::n]]
    nhidx = [x for x in nxidx[::n]]

    # evaluate the coefficents the reduced polynomial
    t = time.time()
    fs = []
    for i in range(m_in):
        coeff = fft([ys[i*n+k] for k in rbo_coset], modulus, ru_coset, True)
        # div h_i
        coeff = [self.mul(c, ru_list[-hidx[i] * k]) for k, c in enumerate(coeff)]
        fs.extend(coeff)
    print("Coeff cost: ", time.time() - t)
            
    datas = []
    z = None
    # cached zvals
    zvals = None
    inv_zvals = None
    rus = ru_list[n]
    rootz = expand_root_of_unity(rus, modulus)
    for i in range(n):
        ys0 = [None] * m_in * 2
        for j, y in zip(xidx[0::n], fs[i::n]):
            ys0[j] = y
        
        data, z, zvals, inv_zvals = erasure_code_recover(
            ys0, modulus, ru_list[n], z, zvals, inv_zvals, rootz=rootz
        )
        datas.extend(data)

    nys = []
    m = len(datas) // n
    for i in range(m_out):
        coeff = datas[nhidx[i]::m]
        coeff = [self.mul(c, ru_list[nhidx[i] * k]) for k, c in enumerate(coeff)]
        ny = fft(coeff, modulus, ru_coset)
        ny = [ny[i] for i in rbo_coset]
        nys.extend(ny)

    return nys

ru_list = [pf.exp(root_of_unity, i) for i in range(n_elements)]
xidx = [x for i in selected for x in rbo[i*n_elements_ps:(i+1)*n_elements_ps]]
nxidx = [x for i in missing for x in rbo[i*n_elements_ps:(i+1)*n_elements_ps]]
start_time = time.monotonic()
if profiling:
    pr = cProfile.Profile()
    pr.enable()
nys_rec = rec_poly_with_coset_fft(pf, ys, ru_list, xidx, x_row[0:n_elements_ps], nxidx, nys)
assert nys == nys_rec
print("All sample recovery used time: {} s".format(time.monotonic() - start_time))
if profiling:
    pr.disable()
    pr.print_stats(sort="calls")
