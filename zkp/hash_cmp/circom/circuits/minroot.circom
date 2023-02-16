pragma circom 2.0.6;

template MinRoot(nrounds) {
    signal input x_in, y_in;
    signal output x_out, y_out;

    var t;
    signal t2[nrounds];
    signal t4[nrounds];
    signal t6[nrounds];
    signal t7[nrounds];
    signal y[nrounds];

    for (var i=0; i<nrounds; i++) {
        t = (i==0) ? (x_in + y_in) : t7[i - 1] + y[i - 1];
        t2[i] <== t*t;
        t4[i] <== t2[i]*t2[i];
        t6[i] <== t4[i]*t2[i];
        t7[i] <== t6[i]*t;
        y[i] <== (i==0) ? x_in : t7[i - 1] + i;
    }
    x_out <== t7[nrounds-1];
    y_out <== y[nrounds-1];
}

template MinRootExtended(nInputs, nrounds) {
    signal input x_in[nInputs];
    signal output x_out[nInputs];

    var t;
    signal t2[nrounds];
    signal t4[nrounds];
    signal t6[nrounds];
    signal t7[nrounds];
    signal x[nrounds][nInputs];

    for (var i=0; i<nrounds; i++) {
        t = (i==0) ? (x_in[0] + x_in[1]) : x[i-1][0] + x[i-1][1];
        t2[i] <== t*t;
        t4[i] <== t2[i]*t2[i];
        t6[i] <== t4[i]*t2[i];
        t7[i] <== t6[i]*t;
        x[i][0] <== t7[i];
        x[i][1] <== (i==0) ? x_in[2] : x[i-1][2] + i;
        for (var j=2; j<nInputs-1; j++) {
            x[i][j] <== (i==0) ? x_in[j+1] : x[i-1][j+1];
        }
        x[i][nInputs-1] <== (i==0) ? x_in[0] : x[i-1][0];
    }

    x_out <== x[nrounds - 1];
}

template VerifySample(nInputs, nrounds) {
    signal input x_in[nInputs];
    signal input idx;
    signal output x_out;

    component decoder = MinRootExtended(nInputs, nrounds);

    decoder.x_in <== x_in;
    x_out <-- decoder.x_out[idx];
    // TODO: verify commitment
}

// component main = MinRoot(1024*4);
component main = VerifySample(32, 4*1024);
