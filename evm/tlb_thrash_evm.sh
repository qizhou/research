# simulate EVM MLOAD for random access
set -x

gcc -O2 -std=c11 -pthread tlb_thrash_evm.c -o tlb_thrash_evm

for page_num in 16 64 256 640 6400 65536 262144 1048576 4194304 16777216; do
    # random page read (single page)
    taskset -c 1 perf stat -e dTLB-loads,dTLB-load-misses,cycles,instructions ./tlb_thrash_evm ${page_num} $((100000000/${page_num})) 0
    # random page read (cross two pages)
    taskset -c 1 perf stat -e dTLB-loads,dTLB-load-misses,cycles,instructions ./tlb_thrash_evm ${page_num} $((100000000/${page_num})) 4080
    # random page read (cross two pages with unaligned 8-byte offset)
    taskset -c 1 perf stat -e dTLB-loads,dTLB-load-misses,cycles,instructions ./tlb_thrash_evm ${page_num} $((100000000/${page_num})) 4081
done