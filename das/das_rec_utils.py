def eval_poly_in_eval_form_with_coset(self, ys, xs, rus, nxs):
    # rus - roots of unity of coset order

    n = len(rus)
    ni = self.inv(n)

    hns = [self.exp(x, n) for x in xs[::n]]
    hn1s = [self.exp(x, n - 1) for x in xs[::n]]

    # Generate master numerator polynomial, eg. (x - x1) * (x - x2) * ... * (x - xn)
    root = self.zpoly(hns)

    # evaluate y * denominators
    ygs = []
    for i in range(len(hns)):
        di = 1
        for j in range(len(hns)):
            if i == j:
                continue
            di = self.mul(di, (hns[i] - hns[j]))
        d = self.div(ni, di)
        d = self.div(d, hn1s[i])

        for j in range(n):
            ygs.append(self.mul(self.mul(ys[i*n+j], d), rus[j]))

    nys = []
    # batch inverse the single denominators for each basis
    invdenoms = self.multi_inv([nx - x for nx in nxs for x in xs])
    for i in range(len(nxs)):
        v = sum(x * y for x, y in zip(invdenoms[i*len(xs):(i+1)*len(xs)], ygs))
        ny = self.mul(self.eval_poly_at(root, self.exp(nxs[i], n)), v)
        nys.append(ny)

    return nys


def inv_omega_diff(self, oi1, ru_list, idx1, idx2):
    if idx1 > idx2:
        return self.mul(ru_list[-idx2], oi1[idx1 - idx2 - 1])
    else:
        return self.mul(ru_list[-idx1], -oi1[idx2 - idx1 - 1])


def eval_poly_in_eval_form_with_coset_and_cache(self, ys, ru_list, xidx, rus, nxidx):
    # rus - roots of unity of coset order

    # pre-compuate \omega^i - 1
    oi1 = [self.inv(ru_list[i] - 1) for i in range(1, len(ru_list))]

    n = len(rus)
    ni = self.inv(n)

    xs = [ru_list[i] for i in xidx]
    nxs = [ru_list[i] for i in nxidx]
    hns = [self.exp(x, n) for x in xs[::n]]
    hn1s = [self.exp(x, n - 1) for x in xs[::n]]

    # Generate master numerator polynomial, eg. (x - x1) * (x - x2) * ... * (x - xn)
    root = self.zpoly(hns)

    # evaluate y * denominators (without omega_j)
    ygs = []
    for i in range(len(hns)):
        di = 1
        for j in range(len(hns)):
            if i == j:
                continue
            di = self.mul(di, (hns[i] - hns[j]))
        d = self.div(ni, di)
        d = self.div(d, hn1s[i])

        for j in range(n):
            ygs.append(self.mul(self.mul(ys[i*n+j], d), rus[j]))

    nys = []
    # batch inverse the single denominators for each basis
    denoms = [inv_omega_diff(self, oi1, ru_list, i, j) for i in nxidx for j in xidx]
    for i in range(len(nxs)):
        v = sum(x * y for x, y in zip(denoms[i*len(xs):(i+1)*len(xs)], ygs))
        ny = self.mul(self.eval_poly_at(root, self.exp(nxs[i], n)), v)
        nys.append(ny)

    return nys

