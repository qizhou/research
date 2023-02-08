import random
import time

print("Use max 256 bit modulus")
modulus = 2**256 - 2**32 * 351 + 1
power = 3

# BLS12-381
# print("Use BLS12-381 curve modulus")
# modulus = 0x1a0111ea397fe69a4b1ba7b6434bacd764774b84f38512bf6730d2a0f6b0f6241eabfffeb153ffffb9feffffffffaaab
# power = 5

assert ((power - 1) * modulus - (power - 2)) % power == 0
encode_power = ((power - 1) * modulus - (power - 2)) // power

def mimc_encode(inp, steps):
    for i in reversed(range(steps-1)):
        t = pow((inp[0] + inp[1]) % modulus, encode_power, modulus)
        inp[1] = (inp[0] + i) % modulus
        inp[0] = t
    return inp

def mimc_decode(inp, steps):
    for i in range(steps-1):
        t = pow(inp[0], power, modulus)
        inp[0] = (inp[1] - i) % modulus
        inp[1] = (t - inp[0]) % modulus
    return inp

n = 20000

t = time.time()
input = [random.randint(0, modulus - 1) for i in range(2)]
output = mimc_encode(input, n)
used_time0 = (time.time() - t)
print("Encode computation takes: %.4fs" % used_time0)

t = time.time()
assert input == mimc_decode(output, n)
used_time1 = (time.time() - t)
print("Decode computation takes: %.4fs, diff %d x" % (used_time1, used_time0 / used_time1))