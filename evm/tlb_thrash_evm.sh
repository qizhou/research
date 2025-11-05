# simulate EVM MLOAD for random access
set -x

# random page read (single page)
taskset -c 1 perf stat -e dTLB-loads,dTLB-load-misses,cycles,instructions ./tlb_thrash_evm 640 1000000 0
taskset -c 1 perf stat -e dTLB-loads,dTLB-load-misses,cycles,instructions ./tlb_thrash_evm 65536 10000 0
# random page read (cross two pages)
taskset -c 1 perf stat -e dTLB-loads,dTLB-load-misses,cycles,instructions ./tlb_thrash_evm 640 1000000 4080
taskset -c 1 perf stat -e dTLB-loads,dTLB-load-misses,cycles,instructions ./tlb_thrash_evm 65536 10000 4080
# random page read (cross two pages with unaligned 8-byte offset)
taskset -c 1 perf stat -e dTLB-loads,dTLB-load-misses,cycles,instructions ./tlb_thrash_evm 640 1000000 4081
taskset -c 1 perf stat -e dTLB-loads,dTLB-load-misses,cycles,instructions ./tlb_thrash_evm 65536 10000 4081