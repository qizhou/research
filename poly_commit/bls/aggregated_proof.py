# Aggregated proof used in EIP-4804
# Given the full data blobs and their commitments, verify the correctness of the commitment using single pairing operation
# Instead of calculating each commitments individually (efficient when the list of data is long)

from ec import G1Generator, default_ec, G2Generator
from fields import Fq
import random
from evaluation_form import eval_poly_in_eval_form, fq_sum, single_proof_in_eval_form
from pairing import ate_pairing

# number of independent data blobs
l = 4
# number of data points
nroots = 8

order = default_ec.n

g1 = G1Generator()
g2 = G2Generator()

# secret of trusted setup
secret = Fq(order, 87362938561938363821)

data_vec = [[Fq(order, random.randint(0, order - 1)) for i in range(nroots)] for j in range(l)]


primitive = 7
roots = [Fq(order, primitive) ** (i * (order - 1) // nroots)  for i in range(nroots)]
# Lagrange trust setup
sec_roots = [(secret ** nroots - Fq(order, 1)) * w / Fq(order, nroots) / (secret - w) * g1 for w in roots]

commits = [sum(s * y for s, y in zip(sec_roots, vec)) for vec in data_vec]

r = Fq(order, 3865987293472983748932) # should be hash of commits and y's
aggr_vec = [fq_sum([data_vec[j][i] * (r ** j) for j in range(l)]) for i in range(nroots)]
x = Fq(order, 21351839872934792837489329) # should be hash of commits * r^i, 
commit = sum([c * (r ** i) for c, i in zip(commits, range(l))])
assert commit == sum(s * y for s, y in zip(sec_roots, aggr_vec))
y = eval_poly_in_eval_form(x, aggr_vec, roots)

# Check if y and x is on the curve via (C - y) = q(x) * (s - x)
cy = commit + (y * g1).negate()
qs = single_proof_in_eval_form(sec_roots, aggr_vec, roots, x, y)
sx = (x - secret) * g2 # can be done in trusted setup
pair0 = ate_pairing(cy, g2)
print(pair0)

pair1 = ate_pairing(qs, sx)
print(pair1)