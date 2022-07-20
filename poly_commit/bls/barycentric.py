from ec import (G1FromBytes, G1Generator, G1Infinity, G2FromBytes, G2Generator,
                G2Infinity, JacobianPoint, default_ec, default_ec_twist,
                sign_Fq2, twist, untwist, y_for_x)
from fields import Fq
from pairing import ate_pairing

from functools import reduce

g1 = G1Generator()

order = 13

nroots = 3
primitive = 2
roots = [Fq(order, primitive) ** (i * (order - 1) // nroots)  for i in range(nroots)]

x = Fq(order, 4)
y = reduce(lambda x, y: x * y, [x - r for r in roots])
print(y, x ** nroots - Fq(order, 1))


order = default_ec.n
nroots = 8
primitive = 7
roots = [Fq(order, primitive) ** (i * (order - 1) // nroots)  for i in range(nroots)]

x = Fq(order, 14)
y = reduce(lambda x, y: x * y, [x - r for r in roots])
print(y, x ** nroots - Fq(order, 1))
