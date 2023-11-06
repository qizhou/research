import hashlib

seed = b"abc"
length = 32
shuffle = [i + 1 for i in range(32)]

for i in range(length):
    seed = hashlib.sha256(seed).digest()
    x = int.from_bytes(seed, "big") % (length - i) + i
    shuffle[i], shuffle[x] = shuffle[x], shuffle[i]

print(shuffle)