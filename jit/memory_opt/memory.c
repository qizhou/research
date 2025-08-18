// An optimizatio of memory access in EVM to defer memory allocation/boundary check to hardware with the following assumptions introduced in EIP-7923:
// - Memory size grows in the unit of 4KB (page size);
// - Page-based allocation;
// - Hard memory limit (e.g., 1MB);
// The core idea is to use mmap with read/write permission and SEGSEGV handling.
// If a new memory page is accessed, SEGSEGV will be triggered and captured by the handler.
// The handler will then allocate the page on-demand (and charge gas accordingly), and then recover the exection.

#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>

#include <errno.h>
#include <signal.h>
#include <sys/mman.h>
#include <setjmp.h>

static uint8_t* mem;
jmp_buf buf;
void segfault_handler(int signum, siginfo_t *info, void *context);
int npages_allocated;
int npages_invalid;

typedef struct {
    int offset;
    uint8_t v;
} access_t;

static access_t accesses[4] = {
    {0, 1},
    {8*1024, 2},
    {1020*1024, 3},
    {1024*1024, 4},
};

void register_segfault_handler() {
    struct sigaction sa;
    sa.sa_flags = SA_SIGINFO; // Get detailed information
    sa.sa_sigaction = segfault_handler; // Assign the handler function
    sigemptyset(&sa.sa_mask); // Clear the signal mask

    if (sigaction(SIGSEGV, &sa, NULL) == -1) {
        perror("Error setting up signal handler");
        exit(EXIT_FAILURE);
    }
}

void segfault_handler(int signum, siginfo_t *info, void *context) {
    if (((uintptr_t)info->si_addr >= (uintptr_t)mem) && (uintptr_t)info->si_addr<((uintptr_t)mem+1024*1024)) {
        fprintf(stderr, "Page fault is detected, allocating a new page (and charging gas) and resuming exection.\n");
        if (mprotect((void *)((uintptr_t)info->si_addr & ~(uintptr_t)(4*1024-1)), 4*1024, PROT_READ | PROT_WRITE) == -1) {
            perror("Cannot change page permission!");
            exit(EXIT_FAILURE);
        }
        npages_allocated += 1;
        siglongjmp(buf, 1);
    }

    fprintf(stderr, "Invalid access %p\n", info->si_addr);
    npages_invalid += 1;
    siglongjmp(buf, 2);

    exit(EXIT_FAILURE); // Terminate the program for unexpected access
}

int main() {
    register_segfault_handler();

    // Allocate one more page to detect invalid access.
    // In practice, we may assume memory limit is 2^x and xor all accesses in a EVM code section.
    // Then check if the all_access && ~(2^x-1) is zero during a jump.
    void* ptr = mmap(NULL, 1025*1024, PROT_NONE, MAP_PRIVATE | MAP_ANON, -1, 0);
    printf("Allocated 1MB at %p, errno %d\n", ptr, errno);
    mem = ptr;

    for (int i = 0; i < sizeof(accesses) / sizeof(access_t); i++) {
        switch(sigsetjmp(buf, 1)) {
        case 0:
        case 1:
            printf("Accessing at offset %d\n", accesses[i].offset);
            mem[accesses[i].offset] = accesses[i].v;
            break;
        case 2:
            printf("Skipping invalid access at offset %d\n", accesses[i].offset);
            break;
        }
    }

    printf("Done.  Allocated pages %d, invalid accesses %d.\n", npages_allocated, npages_invalid);
}