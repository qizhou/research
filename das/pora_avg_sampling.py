import random

m = 10000000 # number of trials
p = 0.8
n = 16
l = 0 # number of access
s = 0 # number of success

for i in range(m):
  for j in range(n):
    l = l + 1
    if random.random() >= p:
      break
    if j == n - 1:
      s = s + 1

print("average random access per success candiate {}, expected {}".format(l / s, sum([1/p**(i+1.0) for i in range(n)])))
