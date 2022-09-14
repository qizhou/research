import random, time
import cProfile

from py_ecc import optimized_bls12_381 as b
from imported.kzg_proofs import get_root_of_unity, list_to_reverse_bit_order
from imported.fft import fft
from imported.poly_utils import PrimeField

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
row_raw = fft(coeffs + [0] * n_blobs, modulus, root_of_unity, False)
row = list_to_reverse_bit_order(row_raw)
assert row[0:n_blobs] == blobs

# randomly select n // 2 data that are available
selected = [i for i in range(n_samples)]
random.shuffle(selected)
selected = selected[0:n_samples // 2]

# lagrange interploation with available samples (not optimized)
rbo = list_to_reverse_bit_order([i for i in range(n_elements)])
xs = [pf.exp(root_of_unity, x) for i in selected for x in rbo[i*n_elements_ps:(i+1)*n_elements_ps]]
ys = [x for i in selected for x in row[i*n_elements_ps:(i+1)*n_elements_ps]]

start_time = time.monotonic()
pr = cProfile.Profile()
pr.enable()
coeffs_rec = pf.lagrange_interp(xs, ys)
assert coeffs == coeffs_rec
print("used time: {} s".format(time.monotonic() - start_time))
pr.disable()
pr.print_stats(sort="calls")

