// jit_wrapper.h
#ifndef JIT_WRAPPER_H
#define JIT_WRAPPER_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// Initialize ORC JIT
int init_jit(const char *llvm_ir_file);

// Call compiled function: fib(i32 n, uint8_t* out32bytes)
int call_fib(int n, uint8_t* result_buf);

#ifdef __cplusplus
}
#endif

#endif
