pragma circom 2.0.6;

template poly_eval(n) {
    signal input coeffs[n];
    signal input x;
    signal xn[n];
    signal sum[n];
    signal output y;
    xn[0] <== 1;
    sum[0] <== coeffs[0];
    for (var i = 1; i < n; i++) {
        xn[i] <== xn[i-1] * x;
        sum[i] <== xn[i] * coeffs[i] + sum[i-1];
    }
    y <== sum[n-1];
}

template hashimoto(cache_entries, rounds, size, ru) {
    signal input cache[cache_entries];
    signal input key;
    signal mix[rounds + 1][size];
    signal v2[rounds];
    signal v4[rounds];
    signal output v5[rounds];
    signal vv[rounds];
    signal output out[size];
    component poly_evaler[rounds][size];

    mix[0][0] <== key;
    for (var i = 1; i < size; i++) {
        mix[0][i] <== 0;
    }

    for (var i = 0; i < rounds; i++) {
        // access index with permutation poly
        var k = i % size;
        v2[i] <== mix[i][k] * mix[i][k];
        v4[i] <== v2[i] * v2[i];
        v5[i] <== v4[i] * mix[i][k];
        vv[i] <-- ru ** v5[i];

        for (var j = 0; j < size; j++) {
            poly_evaler[i][j] = poly_eval(cache_entries);
            poly_evaler[i][j].coeffs <== cache;
            poly_evaler[i][j].x <== vv[i] * ru ** j;
            mix[i+1][j] <== mix[i][j] + poly_evaler[i][j].y;
        }
    }
    out <== mix[rounds];
}

// 1024 ru for BN128
component main = hashimoto(32, 2, 16, 3161067157621608152362653341354432744960400845131437947728257924963983317266);