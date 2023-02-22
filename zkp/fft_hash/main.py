from poly_utils import PrimeField
import random
from fft import fft

M = 32
N = 1024
size = 16  # encode size
rounds = 2
seed = 123456

modulus = 21888242871839275222246405745257275088548364400416034343698204186575808495617
f = PrimeField(modulus)
nonresidue = 5

ru = f.exp(nonresidue, (modulus-1)//N)

cache = [pow(7, i, modulus) for i in range(M)]

data = fft(cache, modulus, ru)

mix = [0] * size
mix[0] = seed

for i in range(rounds):
    n = pow(mix[i%len(mix)], 5, modulus)
    for j in range(size):
        mix[j] = (mix[j] + data[(n+j)%len(data)]) % modulus
        assert data[(n+j)%len(data)] == f.eval_poly_at(cache, pow(ru, (n + j)%len(data)))
print(mix)
    
