# a simple code to test the performance of mimc
import random
import time

n = 10000

m = 2 ** 256 - 351 * 2 ** 32 + 1
rm = (2 * m - 1) // 3
xs = [random.randint(0, m - 1) for i in range(n)]

t = time.time()
x3s = [x ** 3 % m for x in xs]
print("Forward computation takes: %.4fs" % (time.time() - t))

t = time.time()
xs1 = [pow(x3, rm, m) % m for x3 in x3s]
print("Backward computation takes: %.4fs" % (time.time() - t))


# use VeeDo's setup
m = 0x30000003000000010000000000000001
rm = (2 * m - 1) // 3
xs = [random.randint(0, m - 1) for i in range(n)]

t = time.time()
x3s = [x ** 3 % m for x in xs]
print("Forward computation takes: %.4fs" % (time.time() - t))

t = time.time()
xs1 = [pow(x3, rm, m) % m for x3 in x3s]
print("Backward computation takes: %.4fs" % (time.time() - t))