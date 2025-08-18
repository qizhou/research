// Ethereum allows up to 1024 stack elemenets, i.e., 32KB stack size
// The stack may be underflow or overflow.
// For underflow, we may employ static analysis to ensure the minimum stack depth of an instruction,
// and thus avoiding the underflow check.
// For overflow, static analysis can also help, but it is complicated to study the maximum of the stack depth.
// The idea here is to allocate 32KB + 8KB = 40KB memory via mmap, with first 4KB and last 4KB being PROT_NONE.
// Then underflow and overflow access will trigger SEGSEGV automatically, which will be captured.
// An recovery will be attempted if underflow or overflow is detected (i.e., addr is in underflow/overflow memory).

#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>

#include <errno.h>
#include <signal.h>
#include <sys/mman.h>
#include <setjmp.h>

static uint8_t* v;
jmp_buf buf;
void segfault_handler(int signum, siginfo_t *info, void *context);

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
    fprintf(stderr, "Segmentation Fault (SIGSEGV) received!\n");
    fprintf(stderr, "Faulting address: %p\n", info->si_addr);

    if (((uintptr_t)info->si_addr >= (uintptr_t)v) && (uintptr_t)info->si_addr<((uintptr_t)v+4096)) {
        fprintf(stderr, "Underflow is found, recovering\n");
        siglongjmp(buf, 1);
    }

    if (((uintptr_t)info->si_addr >= (uintptr_t)v+36*1024) && (uintptr_t)info->si_addr<((uintptr_t)v+40*1024)) {
        fprintf(stderr, "Overflow is found, recovering\n");
        siglongjmp(buf, 2);
    }

    exit(EXIT_FAILURE); // Terminate the program after handling
}

int main() {
    register_segfault_handler();

    void* ptr = mmap(NULL, 40*1024, PROT_NONE, MAP_PRIVATE | MAP_ANON, -1, 0);
    printf("Allocated 40KB at %p, errno %d\n", ptr, errno);
    v = ptr;

    printf("Setting rw permissions on [4K, 36K)");
    if (mprotect(ptr+4*1024, 32*1024, PROT_READ | PROT_WRITE) == -1) {
        perror("mprotect error");
        exit(EXIT_FAILURE);
    }

    printf("Accessing 4KB should succeed\n");
    v[4096] = 1;
    printf("Accessing 0B should fail\n");
    switch(sigsetjmp(buf, 1)) {
    case 0:
         v[0] = 1;
    case 1:
        printf("Recovered from underflow\n");
        printf("Accessing 8KB should succeed\n");
        v[2*4096] = 1;
        printf("Accessing 36KB should fail\n");
        v[4096+32*1024] = 1;
    case 2:
        printf("Recovered from overflow\n");
    }


    printf("Done\n");
}