pragma circom 2.0.6;

// def minroot_decode(inp, steps):
//     inp = inp[:]
//     for i in reversed(range(steps-1)):
//         t = pow(inp[0], power, modulus)
//         inp[0] = inp[-1]
//         inp[1] = (inp[1] - i) % modulus
//         inp[2:len(inp)] = inp[1:len(inp) - 1]
//         inp[1] = (t - inp[0]) % modulus
//     return inp
template MinRoot_Decode(nInputs, nrounds) {
    signal input x_in[nInputs];
    signal output x_out[nInputs];

    var t;
    signal t2[nrounds];
    signal t4[nrounds];
    signal t5[nrounds];
    signal x[nrounds][nInputs];

    for (var i=0; i<nrounds; i++) {
        t = (i==0) ? x_in[0] : x[i-1][0];
        t2[i] <== t*t;
        t4[i] <== t2[i]*t2[i];
        t5[i] <== t4[i]*t;
        x[i][0] <== (i==0) ? x_in[nInputs-1] : x[i-1][nInputs-1];
        x[i][1] <== t5[i] - x[i][0];
        x[i][2] <== ((i==0)? x_in[1] : x[i-1][1]) - nrounds + i + 1;
        for (var j=3; j<nInputs; j++) {
            x[i][j] <== (i==0)? x_in[j-1] : x[i-1][j-1];
        }
    }
    x_out <== x[nrounds-1];
}

// template VerifySample(nInputs, nrounds) {
//     signal input x_in[nInputs];
//     signal input idx;
//     signal output x_out;

//     component decoder = MinRootExtended(nInputs, nrounds);

//     decoder.x_in <== x_in;
//     x_out <-- decoder.x_out[idx];
//     // TODO: verify commitment
// }


component main = MinRoot_Decode(3, 16);