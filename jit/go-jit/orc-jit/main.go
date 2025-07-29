package main

/*
#cgo CXXFLAGS: -std=c++17
#include "jit_wrapper.h"
*/
import "C"
import (
	"fmt"
	"log"
	"math/big"
	"unsafe"
)

func main() {
	// Initialize the ORC JIT with our IR file
	if C.init_jit(C.CString("fib.ll")) != 0 {
		log.Fatal("Failed to initialize JIT")
	}

	// Buffer to receive 32 bytes of result
	var buf [32]byte

	// Call fib(100)
	if C.call_fib(100, (*C.uchar)(unsafe.Pointer(&buf[0]))) != 0 {
		log.Fatal("Failed to call fib")
	}

	// Convert little endian 32 bytes to big.Int
	reversed := reverse(buf[:])
	res := new(big.Int).SetBytes(reversed)
	fmt.Println("fib(100) =", res.String())
}

func reverse(b []byte) []byte {
	out := make([]byte, len(b))
	for i := range b {
		out[len(b)-1-i] = b[i]
	}
	return out
}
