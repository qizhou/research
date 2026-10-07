import math
import random

init_v = 1

win_inc = 2
loss_dec = 0

# win rate
p = 0.7

# kelly optimal
f = p / (1 - loss_dec) - (1 - p) / (win_inc - 1)
print(f"f = {f*100:.2f}%")

trials = 1000
n = 300

# bet size ratio
for r in [x / 10 for x in range(1, 10)]:
    results = []
    for _ in range(trials):
        v = init_v

        for _ in range(n):
            v = v * (1 - r) + v * r * (win_inc if random.random() <= p else loss_dec)

            if v == 0:
                break
        results.append(v)

    results.sort()
    print(f"r = {r*100:.2f}%, avg_return = {sum(results) / trials}, median_return = {results[trials//2]}, rate = {math.pow(results[trials//2] / init_v, 1 / n)}")