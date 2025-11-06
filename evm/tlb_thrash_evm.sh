# simulate EVM MLOAD for random access
set -x

gcc -O2 -std=c11 -pthread tlb_thrash_evm.c -o tlb_thrash_evm

# random page read (single page)
taskset -c 1 perf stat -e dTLB-loads,dTLB-load-misses,cycles,instructions ./tlb_thrash_evm 640 200000 0
taskset -c 1 perf stat -e dTLB-loads,dTLB-load-misses,cycles,instructions ./tlb_thrash_evm 65536 2000 0
taskset -c 1 perf stat -e dTLB-loads,dTLB-load-misses,cycles,instructions ./tlb_thrash_evm 1048576 100 0
# random page read (cross two pages)
taskset -c 1 perf stat -e dTLB-loads,dTLB-load-misses,cycles,instructions ./tlb_thrash_evm 640 200000 4080
taskset -c 1 perf stat -e dTLB-loads,dTLB-load-misses,cycles,instructions ./tlb_thrash_evm 65536 2000 4080
taskset -c 1 perf stat -e dTLB-loads,dTLB-load-misses,cycles,instructions ./tlb_thrash_evm 1048576 100 4080
# random page read (cross two pages with unaligned 8-byte offset)
taskset -c 1 perf stat -e dTLB-loads,dTLB-load-misses,cycles,instructions ./tlb_thrash_evm 640 200000 4081
taskset -c 1 perf stat -e dTLB-loads,dTLB-load-misses,cycles,instructions ./tlb_thrash_evm 65536 2000 4081
taskset -c 1 perf stat -e dTLB-loads,dTLB-load-misses,cycles,instructions ./tlb_thrash_evm 1048576 100 4081