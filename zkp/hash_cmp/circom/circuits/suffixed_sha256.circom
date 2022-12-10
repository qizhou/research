pragma circom 2.0.6;
include "../node_modules/circomlib/circuits/sha256/sha256_2.circom";

// a prover wants to prove that it knows the preimage of hash(private + suffix),
// where private is not revealed, and suffix is public.
template Suffixed_sha256() {
    signal input a;
    signal input b;
    signal output out_a;
    signal output out_b;

    component sha256_2 = Sha256_2();
    sha256_2.a <== a;
    sha256_2.b <== b;
    out_a <== sha256_2.out;
    out_b <== b;
}

component main = Suffixed_sha256();
