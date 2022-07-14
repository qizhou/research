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
    return x % m
    
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

class Curve:
    def __init__(self, a, b, m):
        self.a = a
        self.b = b
        self.m = m

    def isOnCurve(self, p):
        x3 = ff_mul(ff_mul(p.x, p.x, self.m), p.x, self.m)
        ax = ff_mul(self.a, p.x, self.m)
        rhs = ff_add(ff_add(x3, ax, self.m), self.b, self.m)
        y2 = ff_mul(p.y, p.y, self.m)
        return rhs == y2

    def add(self, p, q):
        assert self.isOnCurve(p)
        assert self.isOnCurve(q)

        l = ff_div(ff_sub(p.y, q.y, self.m), ff_sub(p.x, q.x, self.m), self.m)
        u = ff_sub(p.y, ff_mul(l, p.x, self.m), self.m)
        x = ff_sub(ff_sub(ff_mul(l, l, self.m), p.x, self.m), q.x, self.m)
        y = ff_neg(ff_add(ff_mul(l, x, self.m), u, self.m), self.m)
        return Point(x, y)

    def double(self, p):
        l = ff_div(ff_add(ff_mul(3, ff_mul(p.x, p.x, self.m), self.m), self.a, self.m), ff_mul(2, p.y, self.m), self.m)
        u = ff_sub(p.y, ff_mul(l, p.x, self.m), self.m)
        x = ff_sub(ff_mul(l, l, self.m), ff_mul(2, p.x, self.m), self.m)
        y = ff_neg(ff_add(ff_mul(l, x, self.m), u, self.m), self.m)
        return Point(x, y)

    def ntimes(self, p, n):
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

# def generator_test():
#     c = Curve(4, 3, 11)  # y^2 = x^3 + 4x + 3 over F_13
#     g = Point(0, 5)
#     print(c.add(Point(5, 7), Point(0, 5)))
#     print(c.double(Point(5, 7)))
#     for i in range(1, 11):
#         print("{} G = {}, on curve = {}".format(i, c.ntimes(g, i), c.isOnCurve(c.ntimes(g, i))))
    
    
ff_test()
curve_test()
generator_test()