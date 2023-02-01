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

# evaluations of C(P(x), P(x*g1), P(x*g1*g1), K(x)) = P(x *g1 *g1) - P(x*g1) - P(x)= 0
# except for x = -g1 and -2 * g1

# c_poly = ...
cp_evals = [(p_evals[(i+2*extension_factor) % precision] - p_evals[(i+extension_factor) % precision] - p_evals[i]) % modulus for i in range(precision)]
cp_poly = fft(cp_evals, modulus, G2, inv=True)

# Find D(x) over large group defined by G2 such that
# C(P(x), P(g x), P(g^2 x)) = Z(x) D(x), where Z(x) = (x^n - 1)/(x-G1)/(x-2*G1) is known by both prover and verifier.
# Since C(P(x)) is at most degree n, randomly sample x at G2
# and check C(P(x)) = Z(x) D(x) at x meaning that
# - if they are not the same, they only differs at  n points,
#   and thus, the chance they differs, while the evaluations at x is the same is n / order of G2.
print("D(x) generating")
xs = f.get_power_cycle(G2)
z_poly_evals = [xs[(i * n) % precision] - 1 for i in range(precision)]
inv_z_poly_evals = f.multi_inv(z_poly_evals)
z_den_evaluations = [(xs[i] - (-G1)) * (xs[i] - (- 2 * G1)) % modulus for i in range(precision)]

d_evals = [cp * iz * zd % modulus for cp, iz, zd in zip(cp_evals, inv_z_poly_evals, z_den_evaluations)]
print("D(x) generated")

# Find B(x) such that
# C(P(x)) = P(x) - I(x) = Z(x) B(x), where Z2(x) = (x-G1) * (x- 2 * G1) * (x + G1),
# I(x) = lagrange_interp of (G1, 1), (2G1, 1), (-G1, output)
print("B(x) generating")

z2_poly = f.zpoly([G1, 2*G1, -G1])
z2_evals = fft(z2_poly, modulus, G2)
iz2_evals = f.multi_inv(z2_evals)
i_poly = f.lagrange_interp([G1, 2*G1, -G1], [v[0], v[1], v[-1]])
i_evals = fft(i_poly, modulus, G2)

b_evals = [((p - i) * iz2) % modulus for p, i, iz2 in zip(p_evals, i_evals, iz2_evals)]
print("B(x) generated")

# if check_z_poly:
#     # Find D(x) using polynomial division (slower?)
#     d_poly1 = f.div_polys(cp_poly, [modulus - 1] + [0] * (n - 1) + [1])
#     d_evals1 = fft(d_poly1, modulus, G2)
#     r_poly = f.mod_polys(cp_poly, [modulus - 1] + [0] * (n - 1) + [1])
#     # only G1 points are not different
#     print([x == y for x, y in zip(d_evals, d_evals1)].count(False))
#     print(n)
#     assert [x == y for x, y in zip(d_evals, d_evals1)].count(False) <= n

# Commit the Merkle tree of D(x) and P(x).
tree_p = merkelize(p_evals)
tree_d = merkelize(d_evals)
tree_b = merkelize(b_evals)

# Random sampling with low-degree proof
x_idx = random.randint(0, precision)
x_idx1 = (x_idx + extension_factor) % precision
x_idx2 = (x_idx + 2 * extension_factor) % precision
proof_p = mk_multi_branch(tree_p, [x_idx, x_idx1, x_idx2])
proof_d = mk_multi_branch(tree_d, [x_idx, x_idx1, x_idx2])
proof_b = mk_branch(tree_b, x_idx)
# TODO: Low-degree proof on D(x), B(x)


## Verifier
x = f.exp(G2, x_idx)
# TODO: Low-degree verification on D(x), B(x)

# Merkle tree check
p_x = p_evals[x_idx]
p_x1 = p_evals[x_idx + extension_factor]
p_x2 = p_evals[x_idx + 2 * extension_factor]
verify_multi_branch(tree_p[1], [x_idx, x_idx + extension_factor, x_idx + 2 * extension_factor], proof_p)
d_x = d_evals[x_idx]
d_x1 = d_evals[x_idx + extension_factor]
d_x2 = d_evals[x_idx + 2 * extension_factor]
verify_multi_branch(tree_d[1], [x_idx, x_idx + extension_factor, x_idx + 2 * extension_factor], proof_d)
b_x = b_evals[x_idx]
verify_branch(tree_b[1], x_idx, proof_b)

# Constraint check
cp_x = (p_x2 - p_x1 - p_x) % modulus
zvalue = f.div(f.div(f.exp(x, n) - 1, x - (-G1)), x- (-2 * G1))
zd_x = f.mul(zvalue, d_x)
assert cp_x == zd_x

# Boundary check
bp_x = f.sub(p_x, f.eval_poly_at(i_poly, x))
z2value = f.mul(f.mul(x - G1, x - 2 * G1), x + G1)
zb_x = f.mul(z2value, b_x)
assert bp_x == zb_x


print("STARK verification passed")

