# minroot used to verify circom code

import json

# print("Use BN128 256 bit modulus")
# modulus = 21888242871839275222246405745257275088548364400416034343698204186575808495617
# power = 5
# encode_power = (power - 1) * modulus - (power - 2) // power

print("Use BLS12-381 modulus")
modulus = 52435875175126190479447740508185965837690552500527637822603658699938581184513
power = 5
encode_power = (2 * modulus - 1) // power


def minroot_forward(x, y, rounds):
    for i in range(rounds):
        t = pow(x + y, encode_power , modulus)
        y = (x + i) % modulus
        x = t
    return x, y

def minroot_backward(x, y, rounds):
    for i in reversed(range(rounds)):
        t = pow(x, power, modulus)
        x = (y - i) % modulus
        y = (t - x) % modulus
    return x, y

def minroot_encode(inp, steps):
    inp = inp[:]
    for i in range(steps):
        t = pow((inp[0] + inp[1]) % modulus, encode_power, modulus)
        inp[1:len(inp)-1] = inp[2:len(inp)]
        inp[-1] = inp[0]
        inp[1] = (inp[1] + i) % modulus
        inp[0] = t

    return inp

def minroot_encode_layered(inp, nlayers):
    x = inp[:]
    y = [0] * len(inp)
    for i in range(nlayers):
        y[1] = pow((x[0] + x[1]) % modulus, encode_power, modulus)
        for j in range(2, len(inp)):
            y[j] = pow((y[j-1] + x[j] + j - 2 + (i * len(inp))) % modulus, encode_power, modulus)
        y[0] = pow((y[-1] + x[0] + (i * len(inp)) + len(inp) - 2) % modulus, encode_power, modulus)
        y[1] += ((i + 1) * len(inp)) - 1
        x = y
    return x


# Exact equation in paper
def minroot_encode_layered1(inp, nlayers):
    x = inp[:]
    k = len(inp)
    y = [0] * len(inp)
    for i in range(1, nlayers + 1):
        y[1] = pow((x[0] + x[1]) % modulus, encode_power, modulus) + i * k - 1
        y[2] = pow((y[1] + x[2] + 1 - k) % modulus, encode_power, modulus)
        for j in range(3, len(inp)):
            y[j] = pow((y[j-1] + x[j] + j-2+(i-1)*k) % modulus, encode_power, modulus)
        y[0] = pow((y[-1] + x[0] + i*k-2) % modulus, encode_power, modulus)
        x = y
    return x


def minroot_decode(inp, steps):
    inp = inp[:]
    for i in reversed(range(steps)):
        t = pow(inp[0], power, modulus)
        inp[0] = inp[-1]
        inp[1] = (inp[1] - i) % modulus
        inp[2:len(inp)] = inp[1:len(inp) - 1]
        inp[1] = (t - inp[0]) % modulus
    return inp

x, y = minroot_forward(123, 456, 16)
print(x, y)
assert minroot_backward(x, y, 16) == (123, 456)
print("minroot forward/backward verification passed")

x = minroot_encode([123, 456, 789], 16)
print(x)
assert minroot_decode(x, 16) == [123, 456, 789]
print("minroot encode/decode verification passed")

x = minroot_encode([i+1 for i in range(32)], 1024)
print(json.dumps([str(y) for y in x]))
assert minroot_decode(x, 1024) == [i+1 for i in range(32)]
print("minroot encode/decode 32-ary verification passed")

x0 = minroot_encode([123, 456, 789, 555], 16)
x1 = minroot_encode_layered([123, 456, 789, 555], 4)
x2 = minroot_encode_layered1([123, 456, 789, 555], 4)
assert x0 == x1
assert x0 == x2
print("minroot layered verification passed")