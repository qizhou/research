pragma circom 2.0.6;
include "../node_modules/circomlib/circuits/poseidon.circom";

// Generate the DAG cache (layer 0) of Ethash with a sequential hash
template Ethash_cache0(cache_entries) {
    signal input seed;
    signal output out[cache_entries];
    component hasher[cache_entries];

    for (var i = 0; i < cache_entries; i++) {
        hasher[i] = Poseidon(1);
    }

    hasher[0].inputs[0] <== seed;
    out[0] <== hasher[0].out;
    for (var i = 1; i < cache_entries; i++) {
        hasher[i].inputs[0] <== out[i - 1];
        out[i] <== hasher[i].out;
    }
}

template Ethash_simple_mixer(cache_entries, cache_rounds) {
    signal input seed;
    signal input cache[cache_entries];
    signal output out;
    signal mix[cache_rounds + 1];


    mix[0] <== seed;    
    for (var i = 1; i <= cache_rounds; i++) {
        mix[i] <-- (cache[mix[i - 1] % cache_entries]) * mix[i - 1];
    }
    out <== mix[cache_rounds];
}

template Ethash_cache0_test(cache_entries, cache_rounds) {
    signal input seed;
    signal cache0[cache_entries];
    signal output out;
    component ethash_cache0 = Ethash_cache0(cache_entries);
    component ethash_mixer = Ethash_simple_mixer(cache_entries, cache_rounds);
    ethash_cache0.seed <== seed;
    ethash_mixer.seed <== seed;
    ethash_mixer.cache <== ethash_cache0.out;
    out <== ethash_mixer.out;
}

// component main = Ethash_cache0(128);
component main = Ethash_cache0_test(1024, 3);