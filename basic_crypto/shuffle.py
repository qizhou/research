import hashlib

seed = input("input seed")
seed1 = input("input seed again")
if seed != seed1:
    print("incorrect seed")
seed = bytes(seed, "ascii")

length = 24
shuffle = [i + 1 for i in range(length)]

for i in range(length):
    seed = hashlib.sha256(seed).digest()
    x = int.from_bytes(seed, "big") % (length - i) + i
    shuffle[i], shuffle[x] = shuffle[x], shuffle[i]

print([(i + 1, x) for i, x in enumerate(shuffle)])
unshuffle = [0] * length
for i, x in enumerate(shuffle):
    unshuffle[x-1] = i + 1
print([(i + 1, x) for i, x in enumerate(unshuffle)])