pragma circom 2.0.6;

// MinRoot backward uses power of 5
// python code
// def minroot_backward(x, y, rounds):
//    for i in reversed(range(rounds)):
//         t = pow(x, power, modulus)
//         x = (y - i) % modulus
//         y = (t - x) % modulus
//     return x, y
template MinRoot_Backward(nrounds) {
    signal input x_in, y_in;
    signal output x_out, y_out;

    var t;
    signal t2[nrounds];
    signal t4[nrounds];
    signal t5[nrounds];
    signal x[nrounds];
    signal y[nrounds];

    for (var i=0; i<nrounds; i++) {
        t = (i==0) ? x_in : x[i - 1];
        t2[i] <== t*t;
        t4[i] <== t2[i]*t2[i];
        t5[i] <== t4[i]*t;
        x[i] <== ((i==0) ? y_in : y[i - 1]) - nrounds + i + 1;
        y[i] <== t5[i] - x[i];
    }
    x_out <== x[nrounds-1];
    y_out <== y[nrounds-1];
}

component main = MinRoot_Backward(16);
// component main = VerifySample(32, 4*1024);
