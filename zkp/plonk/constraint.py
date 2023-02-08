# Constraint utility for PLONK gates like
# Ql(i) * ai + Qr(i) * bi + Qo(i) * ci + Qm(i) * ai * bi + Qci == 0

from poly_utils import PrimeField

def add_add_constraint(pf, Ql, Qr, Qm, Qo, Qc):
    # add ai + bi = ci
    Ql.append(1)
    Qr.append(1)
    Qm.append(0)
    Qo.append(pf.modulus - 1)
    Qc.append(0)

def add_mul_constraint(pf, Ql, Qr, Qm, Qo, Qc):
    # add ai * bi = ci
    Ql.append(0)
    Qr.append(0)
    Qm.append(1)
    Qo.append(pf.modulus - 1)
    Qc.append(0)

def add_const_constraint(pf, Ql, Qr, Qm, Qo, Qc, const):
    # add ci = const_i
    Ql.append(0)
    Qr.append(0)
    Qm.append(0)
    Qo.append(1)
    Qc.append(-const % pf.modulus)

def is_poly_satisfied(pf, Qli, Qri, Qmi, Qoi, Qci, ai, bi, ci):
    return (Qli * ai + Qri * bi + Qmi * ai * bi + Qoi * ci + Qci) % pf.modulus == 0

def is_system_satisfied(pf, Ql, Qr, Qm, Qo, Qc, a, b, c):
    for Qli, Qri, Qmi, Qoi, Qci, ai, bi, ci in zip(Ql, Qr, Qm, Qo, Qc, a, b, c):
        if not is_poly_satisfied(pf, Qli, Qri, Qmi, Qoi, Qci, ai, bi, ci):
            return False
    return True

class PlonkSystem(PrimeField):
    def __init__(self, modulus):
        super().__init__(modulus)
        self.Ql = []
        self.Qr = []
        self.Qm = []
        self.Qo = []
        self.Qc = []
        self.a = []
        self.b = []
        self.c = []

    def add_add_constraint(self):
        add_add_constraint(self, self.Ql, self.Qr, self.Qm, self.Qo, self.Qc)

    def add_mul_constraint(self):
        add_mul_constraint(self,  self.Ql, self.Qr, self.Qm, self.Qo, self.Qc)

    def add_const_constraint(self, const):
        add_const_constraint(self, self.Ql, self.Qr, self.Qm, self.Qo, self.Qc, const)

    def is_satisfied(self, a, b, c):
        return is_system_satisfied(self, self.Ql, self.Qr, self.Qm, self.Qo, self.Qc, a, b, c)

def test_constraint():
    # Simple test for x * x * x + x + 5 == 35

    s = PlonkSystem(37)

    # c0 = a0 * b0 (with a0, b0 = x)
    s.add_mul_constraint()
    # c1 = a1 * b1 (with a1 = c0, b1 = x, and c1 = x ** 3)
    s.add_mul_constraint()
    # c2 = a2 + b2 (with a2 = c1, b2 = x, and c2 = x ** 3 + x)
    s.add_add_constraint()
    # c3 = 5
    s.add_const_constraint(5)
    # c4 = 35
    s.add_const_constraint(35)
    # c5 = a5 + b5 (with a5 = c2, b5 = c3, c5 = c4)
    s.add_add_constraint()

    # witness
    x = 3
    anyv = 0
    a = [x, x * x, x * x * x, anyv, anyv, x * x * x + x]
    b = [x, x, x, anyv, anyv, 5]
    c = [x * x, x * x * x, x * x * x + x, 5, 35, 35]
    assert s.is_satisfied(a, b, c)
    print("Constraint test passed")    


if __name__ == "__main__":
    test_constraint()
