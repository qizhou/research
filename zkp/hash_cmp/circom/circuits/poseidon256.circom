pragma circom 2.0.6;
include "../node_modules/circomlib/circuits/poseidon.circom";

// each input is a finite field and we use 128 bits for each
component main = Poseidon(2);
