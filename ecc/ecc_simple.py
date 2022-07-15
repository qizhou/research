# y^2 = x^3 + a x + b

def egcd(a, b):
    # extended gcd
    # (g, c, d) = gcd(a, b), where a * c + b * d = g
    # In FF case, we find a * c + m * d = 1 (note m is prime, so g is always 1)
    # i.e., a * c = 1 - m * d => a * c = 1 in F_m 
    if a == 0:
        # TODO: assert?
        return (b, 0, 1)
        
    d1, x1, y1 = egcd(b % a, a)
    return (d1, y1 - (b // a) * x1, x1)

# FiniteField operations

def ff_neg(x, m):
    return (-x) % m
    
def ff_add(x, y, m):
    return (x + y) % m

def ff_sub(x, y, m):
    return (x - y) % m

def ff_inv(x, m):
    (g, c, d) = egcd(x, m)
    return c % m

def ff_mul(x, y, m):
    return (x * y) % m

def ff_div(x, y, m):
    assert y != 0
    return ff_mul(x, ff_inv(y, m), m)

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self) -> str:
        return "(x = {}, y = {})".format(self.x, self.y)

    def identity():
        return Point(0, 0) # do not work for y^2 = x^3

    def isIdentity(self):
        return self.x == 0 and self.y == 0

class Curve:
    def __init__(self, a, b, m):
        self.a = a
        self.b = b
        self.m = m

    def isOnCurve(self, p):
        if p.isIdentity():
            return True

        x3 = ff_mul(ff_mul(p.x, p.x, self.m), p.x, self.m)
        ax = ff_mul(self.a, p.x, self.m)
        rhs = ff_add(ff_add(x3, ax, self.m), self.b, self.m)
        y2 = ff_mul(p.y, p.y, self.m)
        return rhs == y2

    def add(self, p, q):
        assert self.isOnCurve(p)
        assert self.isOnCurve(q)

        if p.isIdentity():
            return q
        elif q.isIdentity():
            return p

        if p.x == q.x:
            if p.y == q.y:
                return self.double(p)
            else:
                return Point.identity()

        l = ff_div(ff_sub(p.y, q.y, self.m), ff_sub(p.x, q.x, self.m), self.m)
        u = ff_sub(p.y, ff_mul(l, p.x, self.m), self.m)
        x = ff_sub(ff_sub(ff_mul(l, l, self.m), p.x, self.m), q.x, self.m)
        y = ff_neg(ff_add(ff_mul(l, x, self.m), u, self.m), self.m)
        return Point(x, y)

    def double(self, p):
        if p.isIdentity():
            return p

        l = ff_div(ff_add(ff_mul(3, ff_mul(p.x, p.x, self.m), self.m), self.a, self.m), ff_mul(2, p.y, self.m), self.m)
        u = ff_sub(p.y, ff_mul(l, p.x, self.m), self.m)
        x = ff_sub(ff_mul(l, l, self.m), ff_mul(2, p.x, self.m), self.m)
        y = ff_neg(ff_add(ff_mul(l, x, self.m), u, self.m), self.m)
        return Point(x, y)

    def ntimes(self, p, n):
        # evaulate p + p + ... + p (n p's)
        assert n > 0
        s = None
        x = p
        while n != 0:
            if (n % 2) == 1:
                if s is None:
                    s = x
                else:
                    s = self.add(s, x)
            n = n // 2
            x = self.double(x)
        return s

    def npow(self, p, n, i, order):
        # evaluate n^i p
        
        # evaulate n^i with order
        s = 1
        x = n
        while i != 0:
            if (i % 2) == 1:
                s = (s * x) % order
            i = i // 2
            x = (x * x) % order
        return self.ntimes(p, s)


def ff_test():
    m = 13
    for i in range(1, 13):
        print("1/{} is {}".format(i, ff_inv(i, m)))

def curve_test():
    c = Curve(0, 5, 13)  # y^2 = x^3 + 5 over F_13
    print(Point(2, 0), c.isOnCurve(Point(2, 0)))
    print(Point(4, 2), c.isOnCurve(Point(4, 2)))
    p = c.add(Point(2, 0), Point(4, 2))
    print(p, c.isOnCurve(p))
    p2 = c.double(p)
    print(p2, c.isOnCurve(p2))

    c = Curve(4, 3, 11)  # y^2 = x^3 + 4x + 3 over F_13
    print(Point(0, 5), c.isOnCurve(Point(0, 5)))
    print(Point(3, 3), c.isOnCurve(Point(3, 3)))
    p = c.add(Point(0, 5), Point(3, 3))
    print(p, c.isOnCurve(p))
    p2 = c.double(p)
    print(p2, c.isOnCurve(p2))
    p4 = c.double(p)
    print(p4, c.isOnCurve(p4))

    c = Curve(5, 7, 23)
    print(Point(2, 5), c.isOnCurve(Point(2, 5)))
    print(Point(12, 1), c.isOnCurve(Point(12, 1)))
    print(c.add(Point(2, 5), Point(12, 1)))

def generator_test():
    c = Curve(4, 3, 11)  # y^2 = x^3 + 4x + 3 over F_13
    g = Point(0, 5)
    print(c.add(Point(5, 7), Point(0, 5)))
    print(c.double(Point(5, 7)))
    for i in range(1, 13):
        print("{} G = {}, on curve = {}".format(i, c.ntimes(g, i), c.isOnCurve(c.ntimes(g, i))))

def generator_test1():
    c = Curve(1, 1, 101)
    g = Point(47, 12)
    assert c.isOnCurve(g)
    x = Point.identity()
    for i in range(1, 106):
        x = c.add(x, g)
        print("{} G = {}, on curve = {}".format(i, x, c.isOnCurve(x)))

def secp_256_test():
    c = Curve(-3, 41058363725152142129326129780047268409114441015993725554835256314039467401291, 115792089210356248762697446949407573530086143415290314195533631308867097853951)
    # order 115792089210356248762697446949407573529996955224135760342422259061068512044369
    g = Point(48439561293906451759052585252797914202762949526041747995844080717082404635286, 36134250956749795798585127919587881956611106672985015071877198253568414405109)
    print(c.isOnCurve(g))

def trusted_setup_test():
    # use secp256 curve
    c = Curve(-3, 41058363725152142129326129780047268409114441015993725554835256314039467401291, 115792089210356248762697446949407573530086143415290314195533631308867097853951)
    order = 115792089210356248762697446949407573529996955224135760342422259061068512044369
    g = Point(48439561293906451759052585252797914202762949526041747995844080717082404635286, 36134250956749795798585127919587881956611106672985015071877198253568414405109)
    # random secret
    s = 89128395972649298573498716256466745
    print(c.npow(g, s, 1, order))
    print(c.npow(g, s, 2, order))
    print(c.npow(g, s, 3, order))
    print(c.npow(g, s, 4, order))

    
    
ff_test()
curve_test()
generator_test()
generator_test1()
secp_256_test()
trusted_setup_test()