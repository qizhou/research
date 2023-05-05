import random
import time

from fft import fft
from poly_utils import PrimeField


# a simple code to demonstrate f(x) = p(x) q(x) using fft
# degrees of p(x) and q(x)
d_p = 254 * 8
d_q = 190 * 8

modulus = 52435875175126190479447740508185965837690552500527637822603658699938581184513
pf = PrimeField(modulus)
# root of unity
N = 512 * 8
assert d_p + d_q + 1 <= N
ru = pf.exp(7, (modulus-1) // N)

poly_p = [random.randint(0, modulus - 1) for i in range(d_p + 1)]
poly_q = [random.randint(0, modulus - 1) for i in range(d_q + 1)]

start = time.time()
evals_p = fft(poly_p, modulus, ru)
evals_q = fft(poly_q, modulus, ru)
evals_f = [pf.mul(x, y) for x, y in zip(evals_p, evals_q)]
poly_f = fft(evals_f, modulus, ru, inv=True)
print("fft used time", time.time() - start)

start = time.time()
poly_f1 = pf.mul_polys(poly_p, poly_q)
poly_f1 = poly_f1 + [0] * (N - len(poly_f1)) # padding zeros
print("direct used time", time.time() - start)
assert poly_f == poly_f1

