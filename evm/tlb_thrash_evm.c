// tlb_thrash_evm.c
// Build:  gcc -O2 -std=c11 -pthread tlb_thrash_evm.c -o tlb_thrash_evm
// Run examples:
//   ./tlb_thrash_evm               # defaults (4096 pages, enough to thrash most STLBs)
//   ./tlb_thrash_evm  256          # ~1MB working set, often fits in STLB
//   ./tlb_thrash_evm  4096  10     # 4096 pages, 10 passes
//   sudo taskset -c 1 ./tlb_thrash_evm 4096 10 # pin to CPU 1 (more stable)
// Notes:
// - Linux; x86-64 assumed 4K pages. Use `perf stat -e dTLB-load-misses` to confirm.
// - EVM word size is 32 bytes, so to simulate worst case random access, we randomly access 32B across two consective pages.


#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <unistd.h>
#include <sched.h>
#include <string.h>
#include <sys/mman.h>
#include <errno.h>

#ifndef CLOCK_MONOTONIC_RAW
#define CLOCK_MONOTONIC_RAW CLOCK_MONOTONIC
#endif

static inline uint64_t nsec_now(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC_RAW, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ull + ts.tv_nsec;
}

// Simple xorshift RNG for shuffling
static inline uint32_t xs32(uint32_t *s) {
    uint32_t x = *s;
    x ^= x << 13; x ^= x >> 17; x ^= x << 5;
    *s = x;
    return x;
}

int main(int argc, char *argv[]) {
    const size_t page_bytes = 4096;   // 4K pages
    size_t pages = 4096;              // default: 16 MB working set -> likely thrash STLB on many CPUs
    size_t passes = 5;                // how many sweeps over the working set
    size_t roff = 0;                  // initial read offset
    int pin = 0;                      // pin to CPU 0
    if (argc >= 2) pages = strtoull(argv[1], NULL, 10);
    if (argc >= 3) passes = strtoull(argv[2], NULL, 10);
    if (argc >= 4) roff = strtoull(argv[3], NULL, 10);

    size_t bytes = (pages + 1) * page_bytes;
    // Page-aligned allocation. Use mmap so we can control hugepage behavior.
    void *buf = mmap(NULL, bytes, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (buf == MAP_FAILED) { perror("mmap"); return 1; }

    // Disable huge pages so we really exercise 4K TLBs.
    // (This may be a no-op on some systems; still helps reduce THP surprises.)
    if (madvise(buf, bytes, MADV_NOHUGEPAGE) != 0) {
        // Not fatal; ignore if EPERM/ENOSYS
    }

    // Build a page index array and shuffle it to defeat streamer prefetch
    size_t *idx = malloc(pages * sizeof(*idx));
    if (!idx) { perror("malloc"); return 1; }
    for (size_t i = 0; i < pages; i++) idx[i] = i;
    uint32_t seed = 0x12345678u;
    for (size_t i = pages - 1; i > 0; i--) {
        size_t j = xs32(&seed) % (i + 1);
        size_t t = idx[i]; idx[i] = idx[j]; idx[j] = t;
    }

    // Prefault: touch each page to avoid measuring major page faults
    for (size_t i = 0; i < pages+1; i++) {
        volatile uint8_t *p = (volatile uint8_t *)buf + idx[i] * page_bytes;
    }

    // Main measurement loop: touch one 32-byte word accross two pages, random order, repeated.
    volatile uint64_t sink = 0;
    uint64_t start = nsec_now();
    for (size_t pass = 0; pass < passes; pass++) {
        for (size_t k = 0; k < pages; k++) {
            size_t i = idx[k];
            size_t off = i * page_bytes+roff;
            volatile uint64_t *p0 = (volatile uint64_t *)((uint8_t *)buf + off);
            sink += *p0;
            volatile uint64_t *p1 = (volatile uint64_t *)((uint8_t *)buf + off + 8);
            sink += *p1;
            volatile uint64_t *p2 = (volatile uint64_t *)((uint8_t *)buf + off + 16);
            sink += *p2;
            volatile uint64_t *p3 = (volatile uint64_t *)((uint8_t *)buf + off + 32);
            sink += *p3;
        }
    }
    uint64_t end = nsec_now();

    // Results
    double total_accesses = (double)pages * (double)passes;
    double ns_per_access = (end - start) / total_accesses;
    double mb = bytes / (1024.0 * 1024.0);

    printf("Working set: %.1f MiB (%zu pages of 4K)\n", mb, pages);
    printf("Passes: %zu, total EVM accesses: %.0f (one per page)\n", passes, total_accesses);
    printf("Time: %.3f ms, %.3f ns/access\n", (end - start)/1e6, ns_per_access);
    printf("Sum: %llu\n", (unsigned long long)sink);

    // Hints for experimentation
    fprintf(stderr,
        "\nTips:\n"
        "  • Increase pages till you exceed your L1 dTLB (often ~64 entries for 4K) to see the first jump.\n"
        "  • Go beyond your STLB (often ~1–2K entries) to see a bigger jump.\n"
        "  • Compare with huge pages: comment MADV_NOHUGEPAGE and enable THP, or map with MAP_HUGETLB (needs root).\n"
        "  • Use perf to confirm TLB misses: `perf stat -e dTLB-loads,dTLB-load-misses,cycles,instructions ./tlb_thrash ...`\n"
        "  • Pinning to a CPU (add 'pin') and closing background apps reduces noise.\n");

    munmap(buf, bytes);
    free(idx);
    return 0;
}