from fields import Fq
from functools import reduce

def fq_sum(vec):
    return reduce(lambda x, y: x+y, vec)

def eval_poly_in_eval_form(x, mus, roots):
    # Given data points of (mu_i, roots_i), where roots are roots of unity, return x based on barycentric formula
    order = x.Q
    nroots = len(roots)
    assert len(mus) == nroots
    return (x ** nroots - Fq(order, 1)) / nroots * fq_sum([mu * root / (x - root) for mu, root in zip(mus, roots)])

def commitment_in_eval_form(lagrange_setup, mus):
    return sum(mu * l for mu, l in zip(mus, lagrange_setup))

def single_proof_in_eval_form(lagrange_setup, mus, roots, x, y):
    # Obtain the proof polynomial evaluated at a trusted setup secret
    return sum([(mu - y) / (root - x) * l for mu, root, l in zip(mus, roots, lagrange_setup)])
