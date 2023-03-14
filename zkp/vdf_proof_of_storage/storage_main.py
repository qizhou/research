# A demo code for proving storage on dynamic datasets of L2 using L1 contract 

import random
import time
from mimc_stark import mimc_encode, mimc_decode, mk_mimc_proof, verify_mimc_proof
from hashlib import blake2s

hash_fn = lambda x: blake2s(x).digest()
N_s = 16        # number of samples per solving window
N_d = 128       # number of data (BLOBs) of F_q
addr = random.randint(0, 2 ** 20 - 1)   # address of the storage provider (in eth format)
encode_type = "vde"  # vde or ethash

if encode_type == "vde":
    print("Using VDE")
    modulus = 2**256 - 2**32 * 351 + 1      # q value of F_q, 256 bits
    N_trace = 64        # number of computation trace of VDF (MiMC)
    MIMC_constants = [(i**7) ^ 42 for i in range(min(N_trace // 2, 64))] # MiMC round constants
    # encoder and decoder (note that the choice of encoding key may suffer from grinding attack)
    encode = lambda d, _, addr, idx: mimc_encode((d + addr + idx) % modulus, N_trace, MIMC_constants)
    decode = lambda d, _, addr, idx: (mimc_decode(d, N_trace, MIMC_constants) - addr - idx) % modulus
    mk_proof = lambda encoded_sample: mk_mimc_proof(encoded_sample, N_trace, MIMC_constants)
    verify_proof = lambda encoded_sample, raw_sample, _, addr, idx, proof: verify_mimc_proof(encoded_sample, N_trace, MIMC_constants, (raw_sample + addr + idx) % modulus, proof)
elif encode_type == "ethash":
    print("Using Ethash")
    modulus = 2**256     # Full 32-bytes
    # encoder and decoder with simple hash (note that the choice of encoding key may suffer from grinding attack)
    encode = lambda d, h, addr, idx: (d + int.from_bytes(hash_fn(h + addr.to_bytes(20) + idx.to_bytes(8)), byteorder="big")) % modulus
    decode = lambda d, h, addr, idx: (d - int.from_bytes(hash_fn(h + addr.to_bytes(20) + idx.to_bytes(8)), byteorder="big")) % modulus
    # TODO
    mk_proof = lambda encoded_sample: []
    verify_proof = lambda encoded_sample, raw_sample, _, addr, idx, proof: True


# Raw data written by users
dataset = [random.randint(0, modulus - 1) for i in range(N_d)]

# On-chain hashes for integrity check
hashes = [hash_fn(inp.to_bytes(32, byteorder="big")) for inp in dataset]

# Encoded data (replica) stored by a storage provider (L2 off-chain)
# For VDE encoding, the encoding time T_e of each BLOB should be very time consuming so that
# - T_e is greater than the duration of solving window (T_w).
#   This means that an on-demanding encoding cannot produce a candidate within a solving window; or
# - N_s * T_e > T_w.
#   This means that an on-demanding encoding must encode all data (or unstored data) to produce a candidate.
# For Ethash encoding, we just want to make sure the energy cost of encoding a BLOB > sampling cost of a BLOB
# The encoded data is mixed with addr and index to ensure the encoded replica/BLOB is unique
print("Encoding")
start_time = time.time()
encoded_dataset = [encode(inp, hashes[i], addr, i) for (i, inp) in enumerate(dataset)]
print("Encoding use time: %.2fs, avg : %.2f ms" % (time.time() - start_time, (time.time() - start_time) / N_d * 1000))

# Decoding the data for verification.  The decoding time should be must faster than encoding.
print("Decoding")
start_time = time.time()
decoded_dataset = [decode(inp, hashes[i], addr, i) for (i, inp) in enumerate(encoded_dataset)]
assert decoded_dataset == dataset
print("Decoding use time: %.2fs, avg : %.2f ms" % (time.time() - start_time, (time.time() - start_time) / N_d * 1000))

# Given a on-chain seed (e.g., from RANDAO), addr, produce a candidate
def produce_candidate(N_s, seed, addr, encoded_dataset):
    seed = hash_fn(seed + addr.to_bytes(32, byteorder="big"))
    ps = []
    for i in range(N_s):
        # random sampling position, which is unpredicable until the sampled data is obtained
        p = int.from_bytes(seed, byteorder="big") % len(encoded_dataset)
        seed = hash_fn(seed + encoded_dataset[p].to_bytes(32, byteorder="big"))
        ps.append(p)
    return seed, ps

# Generate a proof with a list of seeds
# Each seed is revealed at the beginning of solving window (e.g., prevRANDAO of Eth2.0 epoch)
def generate_proof(seed, diff, N_s, addr, encoded_dataset):
    i = 0
    while True:
        i = i + 1
        seed = hash_fn(seed)
        candidate, ps = produce_candidate(N_s, seed, addr, encoded_dataset)
        if int.from_bytes(candidate, byteorder="big") * diff <= 2 ** 256:
            break
    encoded_samples = [encoded_dataset[p] for p in ps]
    samples = [decode(s, hashes[i], addr, i) for i, s in zip(ps, encoded_samples)]
    encoding_proof = [mk_proof(encoded_sample) for encoded_sample in encoded_samples]
    proof = (ps, samples, encoded_samples, encoding_proof)
    print("Generated proof with %d candidates" % i)
    return seed, proof


# Verify the proof on-chain, where
# - N_s, N_d, seed, diff, hashes are available on-chain
# - addr, proof are provided by the prover
def verify(N_s, seed, addr, diff, hashes, proof):
    # check proof
    # check if the samples of the encoded_samples matches 
    pos, samples, encoded_samples, stark_proof = proof
    assert len(samples) == N_s
    assert len(encoded_samples) == N_s
    assert len(pos) == N_s
    # check MIMC using stark
    for i in range(N_s):
        assert verify_proof(encoded_samples[i], samples[i], hashes[i], addr, pos[i], stark_proof[i])
        # assert verify_mimc_proof(encoded_samples[i], N_c, MIMC_constants, mimc_decode(encoded_samples[i], N_c, MIMC_constants), stark_proof[i])
    # check integrity
    assert [hash_fn(sample.to_bytes(32, byteorder="big")) for sample in samples] == [hashes[p] for p in pos]

    # check random sampling
    seed = hash_fn(seed + addr.to_bytes(32, byteorder="big"))
    for i in range(N_s):
        # random sampling position, which is unpredicable until the sampled data is obtained
        p = int.from_bytes(seed, byteorder="big") % N_d
        assert p == pos[i]
        seed = hash_fn(seed + encoded_samples[i].to_bytes(32, byteorder="big"))
    assert int.from_bytes(seed, byteorder="big") * diff <= 2 ** 256
    print("Verification passed")


produce_candidate(N_s, random.randbytes(8), addr, encoded_dataset)
diff = 16  # times T_w to get the expect interval of generating proofs
seed, proof = generate_proof(b"", diff, N_s, addr, encoded_dataset)
verify(N_s, seed, addr, diff, hashes, proof)