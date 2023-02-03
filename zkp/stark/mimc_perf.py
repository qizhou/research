import random
import time

modulus = 2**256 - 2**32 * 351 + 1
MIMC_constants = [(i**7) ^ 42 for i in range(64)] # MiMC round constants

def mimc_encode(inp, steps, round_constants):
    for i in reversed(range(steps-1)):
        inp = (pow((inp - round_constants[i % len(round_constants)]) % modulus, (2 * modulus - 1) // 3, modulus)) % modulus
    return inp

def mimc_decode(inp, steps, round_constants):
    for i in range(steps-1):
        inp = (pow(inp, 3, modulus) + round_constants[i % len(round_constants)]) % modulus
    return inp

n = 20000

t = time.time()
input = random.randint(0, modulus - 1)
output = mimc_encode(input, n, MIMC_constants)
used_time0 = (time.time() - t)
print("Encode computation takes: %.4fs" % used_time0)

t = time.time()
assert input == mimc_decode(output, n, MIMC_constants)
used_time1 = (time.time() - t)
print("Decode computation takes: %.4fs, diff %d x" % (used_time1, used_time0 / used_time1))