from poly_utils import PrimeField
import random
from fft import fft
from merkle_tree import merkelize, mk_branch, verify_branch

check_z_poly = False

def shift_poly(poly, modulus, factor):
    factor_power = 1
    inv_factor = pow(factor, modulus - 2, modulus)
    o = []
    for p in poly:
        o.append(p * factor_power % modulus)
        factor_power = factor_power * inv_factor % modulus
    return o

# number of P(x) values
n = 1024
extension_factor = 16

modulus = 2**256 - 2**32 * 351 + 1
f = PrimeField(modulus)

precision = n * extension_factor
G2 = f.exp(7, (modulus-1)//precision)
skips = precision // n
G1 = f.exp(G2, skips)

v = [random.randint(0, 9) for i in range(n)]
p_poly = fft(v, modulus, G1, inv=True)
# evaluations of P(x) over G2
p_evals = fft(p_poly, modulus, G2)
# evaluations of C(P(x))

c_poly = f.zpoly([x for x in range(10)])
cp_evals = [f.eval_poly_at(c_poly, x) for x in p_evals]
cp_poly = fft(cp_evals, modulus, G2, inv=True)

# Find D(x) over large group defined by G2 such that
# C(P(x)) = Z(x) D(x), where Z(x) = x^n - 1 is known by both prover and verifier.
# Since C(P(x)) is at most degree 10 * n, randomly sample x at G2
# and check C(P(x)) = Z(x) D(x) at x meaning that
# - if they are not the same, they only differs at 10 * n points,
#   and thus, the chance they differs, while the evaluations at x is the same is 10 * n / order of G2.
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

# Need to commit the Merkle tree of D(x) and P(x).
tree_p = merkelize(p_evals)
tree_d = merkelize(d_evals)

# Random sampling with low-degree proof
x_idx = random.randint(0, precision - 1)
proof_p = mk_branch(tree_p, x_idx)
proof_d = mk_branch(tree_d, x_idx)
# TODO: Low-degree proof on D(x)
# proof = x_idx + proof_p + proof_d + low-degree proof

## Verifier
x = f.exp(G2, x_idx)
# TODO: Low-degree verification on D(x)

# Merkle tree check
p_x = p_evals[x_idx]
verify_branch(tree_p[1], x_idx, proof_p)
d_x = d_evals[x_idx]
verify_branch(tree_d[1], x_idx, proof_d)

# Constraint check
cp_x = f.eval_poly_at(c_poly, p_x)
zd_x = f.mul(f.sub(f.exp(x, n), 1), d_x)
assert cp_x == zd_x

