import random
import time

print("Use max 256 bit modulus")
modulus = 2**256 - 2**32 * 351 + 1
power = 3

m = 64

# BLS12-381
# print("Use BLS12-381 curve modulus")
# modulus = 0x1a0111ea397fe69a4b1ba7b6434bacd764774b84f38512bf6730d2a0f6b0f6241eabfffeb153ffffb9feffffffffaaab
# power = 5

assert ((power - 1) * modulus - (power - 2)) % power == 0
encode_power = ((power - 1) * modulus - (power - 2)) // power

def minroot_encode(inp, steps):
    inp = inp[:]
    for i in reversed(range(steps-1)):
        t = pow((inp[0] + inp[1]) % modulus, encode_power, modulus)
        inp[1:len(inp)-1] = inp[2:len(inp)]
        inp[-1] = inp[0]
        inp[1] = (inp[1] + i) % modulus
        inp[0] = t

    return inp

def minroot_decode(inp, steps):
    inp = inp[:]
    for i in range(steps-1):
        t = pow(inp[0], power, modulus)
        inp[1] = (inp[1] - i) % modulus
        inp[0] = inp[-1]
        inp[2:len(inp)] = inp[1:len(inp) - 1]
        inp[1] = (t - inp[0]) % modulus
    return inp

def minroot_decode_opt(inp, steps):
    inp = inp[:]
    m = len(inp)
    for i in range(steps-1):
        j = -i % m 
        jn1 = (j - 1) % m
        jp1 = (j + 1) % m
        t = pow(inp[j], power, modulus)
        inp[jp1] = (inp[jp1] - i) % modulus
        inp[j] = (t - inp[jn1]) % modulus
    
    j = (-(steps - 1)) % m
    out = [0] * len(inp)
    out[j:] = inp[0:j]
    out[:j] = inp[j:]

    return out

def minroot2_encode(inp, steps):
    inp = inp[:]
    for i in reversed(range(steps-1)):
        t = pow((inp[0] + inp[1]) % modulus, encode_power, modulus)
        inp[1] = (inp[0] + i) % modulus
        inp[0] = t
    return inp

def minroot3_encode(inp, steps):
    a, b, c = inp
    for i in reversed(range(steps-1)):
        t = pow((a + b) % modulus, encode_power, modulus)
        b = (c + i) % modulus
        c = a
        a = t
    return [a, b, c]

def minroot2_decode(inp, steps):
    inp = inp[:]
    for i in range(steps-1):
        t = pow(inp[0], power, modulus)
        inp[0] = (inp[1] - i) % modulus
        inp[1] = (t - inp[0]) % modulus
    return inp

def minroot3_decode(inp, steps):
    a, b, c = inp
    for i in range(steps-1):
        t = pow(a, power, modulus)
        a = c
        c = (b - i) % modulus
        b = (t - a) % modulus
    return [a, b, c]

def verf_test():
    n = 2000

    input = [random.randint(0, modulus - 1) for i in range(2)]
    output = minroot_encode(input, n)
    assert output == minroot2_encode(input, n)

    assert input == minroot_decode(output, n)
    assert input == minroot2_decode(output, n)
    print("Verification 2-ary pass")

    input = [random.randint(0, modulus - 1) for i in range(3)]
    output = minroot_encode(input, n)
    assert output == minroot3_encode(input, n)

    assert input == minroot_decode(output, n)
    assert input == minroot3_decode(output, n)
    print("Verification 3-ary pass")

def perf_test():
    n = 20000

    t = time.time()
    input = [random.randint(0, modulus - 1) for i in range(m)]
    output = minroot_encode(input, n)
    used_time0 = (time.time() - t)
    print("Encode computation takes: %.4fs" % used_time0)

    t = time.time()
    assert input == minroot_decode(output, n)
    used_time1 = (time.time() - t)
    print("Decode computation takes: %.4fs, diff %d x" % (used_time1, used_time0 / used_time1))

def opt_test():
    n = 20000
    t = time.time()
    input = [random.randint(0, modulus - 1) for i in range(m)]
    output = minroot_encode(input, n)
    used_time0 = (time.time() - t)
    print("Encode computation takes: %.4fs" % used_time0)

    t = time.time()
    decode_input = minroot_decode_opt(output, n)
    assert input == decode_input
    used_time1 = (time.time() - t)
    print("Decode computation takes: %.4fs, diff %d x" % (used_time1, used_time0 / used_time1))

verf_test()
perf_test()
opt_test()

