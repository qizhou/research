# A simple STARK code to demonstrate fibonacci seq check
from poly_utils import PrimeField
import random
from fft import fft
from merkle_tree import merkelize, mk_branch, verify_branch, mk_multi_branch, verify_multi_branch

check_z_poly = True

def shift_poly(poly, modulus, factor):
    factor_power = 1
    inv_factor = pow(factor, modulus - 2, modulus)
    o = []
    for p in poly:
        o.append(p * factor_power % modulus)
        factor_power = factor_power * inv_factor % modulus
    return o

# number of P(x) values
n = 128
extension_factor = 32

modulus = 2**256 - 2**32 * 351 + 1
f = PrimeField(modulus)

precision = n * extension_factor
G2 = f.exp(7, (modulus-1)//precision)
skips = precision // n
G1 = f.exp(G2, skips)

# computational trace
v = [0] * n
v[0] = 1
v[1] = 1
for i in range(2, n):
    v[i] = v[i-1] + v[i-2]

p_poly = fft(v, modulus, G1, inv=True)
# evaluations of P(x) over G2
p_evals = fft(p_poly, modulus, G2)

# evaluations of C(P(x), P(x*g1), P(x*g1*g1), K(x)) = P(x *g1 *g1) - P(x*g1) - P(x) - K(x) = 0
# Note that K(x) = 0 except K(-2 * g1) = v[0] - v[-1] - v[-2]; K(-g1) = v[1] - v[0] - v[-1]

k_evals_g1 = [0] * n
k_evals_g1[-2] = (v[0] - v[-1] - v[-2]) % modulus
k_evals_g1[-1] = (v[1] - v[0] - v[-1]) % modulus
k_poly = fft(k_evals_g1, modulus, G1, inv=True)
k_evals = fft(k_poly, modulus, G2)

# c_poly = ...
cp_evals = [(p_evals[(i+2*extension_factor) % precision] - p_evals[(i+extension_factor) % precision] - p_evals[i] - k_evals[i]) % modulus for i in range(precision)]
cp_poly = fft(cp_evals, modulus, G2, inv=True)

# Find D(x) over large group defined by G2 such that
# C(P(x), P(g x), P(g^2 x), K(x)) = Z(x) D(x), where Z(x) = (x^n - 1) is known by both prover and verifier.
# Since C(P(x)) is at most degree n, randomly sample x at G2
# and check C(P(x)) = Z(x) D(x) at x meaning that
# - if they are not the same, they only differs at  n points,
#   and thus, the chance they differs, while the evaluations at x is the same is n / order of G2.
print("D(x) generating")
shift = 7
shift_inv = f.inv(shift)

shifted_cp_poly = shift_poly(cp_poly, modulus, shift)
shifted_cp_evals = fft(shifted_cp_poly, modulus, G2)
shifted_z_poly = shift_poly([modulus - 1] + [0] * (n - 1) + [1], modulus, shift)
shifted_z_poly_evals = fft(shifted_z_poly, modulus, G2)
shifted_d_evals = [f.div(x, y) for x, y in zip(shifted_cp_evals, shifted_z_poly_evals)]
shifted_d_poly = fft(shifted_d_evals, modulus, G2, inv=True)
d_poly = shift_poly(shifted_d_poly, modulus, shift_inv)
d_evals = fft(d_poly, modulus, G2)
print("D(x) generated")

if check_z_poly:
    # Find D(x) using polynomial division (slower?)
    d_poly1 = f.div_polys(cp_poly, [modulus - 1] + [0] * (n - 1) + [1])
    d_evals1 = fft(d_poly1, modulus, G2)
    r_poly = f.mod_polys(cp_poly, [modulus - 1] + [0] * (n - 1) + [1])
    assert d_evals == d_evals1

# Commit the Merkle tree of D(x) and P(x).
tree_p = merkelize(p_evals)
tree_d = merkelize(d_evals)
tree_k = merkelize(p_evals)

# Random sampling with low-degree proof
x_idx = random.randint(0, precision)
x_idx1 = (x_idx + extension_factor) % precision
x_idx2 = (x_idx + 2 * extension_factor) % precision
proof_p = mk_multi_branch(tree_p, [x_idx, x_idx1, x_idx2])
proof_d = mk_multi_branch(tree_d, [x_idx, x_idx1, x_idx2])
# TODO: should we compute k_evals directly (given v[0] and v[1])
proof_k = mk_branch(tree_k, x_idx)
# TODO: Low-degree proof on D(x)
# TODO: proof on v[0] and v[1]

## Verifier
x = f.exp(G2, x_idx)
# TODO: Low-degree verification on D(x)

# Merkle tree check
p_x = p_evals[x_idx]
p_x1 = p_evals[x_idx + extension_factor]
p_x2 = p_evals[x_idx + 2 * extension_factor]
verify_multi_branch(tree_p[1], [x_idx, x_idx + extension_factor, x_idx + 2 * extension_factor], proof_p)
d_x = d_evals[x_idx]
d_x1 = d_evals[x_idx + extension_factor]
d_x2 = d_evals[x_idx + 2 * extension_factor]
verify_multi_branch(tree_d[1], [x_idx, x_idx + extension_factor, x_idx + 2 * extension_factor], proof_d)
k_x = k_evals[x_idx]
verify_branch(tree_k[1], x_idx, proof_k)

# Constraint check
cp_x = (p_x2 - p_x1 - p_x - k_x) % modulus
zd_x = f.mul(f.sub(f.exp(x, n), 1), d_x)
assert cp_x == zd_x
print("STARK verification passed")

