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
	"time"
	"unsafe"

	"github.com/holiman/uint256"
)

func fib(n int) *uint256.Int {
	a := uint256.NewInt(0)
	b := uint256.NewInt(1)
	for i := 0; i < n; i++ {
		a = a.Add(a, b)
		a, b = b, a
	}
	return b
}

func main() {
	// Initialize the ORC JIT with our IR file
	if C.init_jit(C.CString("fib.ll")) != 0 {
		log.Fatal("Failed to initialize JIT")
	}

	now := time.Now()
	// Buffer to receive 32 bytes of result
	var buf [32]byte

	n := 10000
	if C.call_fib(C.int(n), (*C.uchar)(unsafe.Pointer(&buf[0]))) != 0 {
		log.Fatal("Failed to call fib")
	}

	// Convert little endian 32 bytes to big.Int
	reversed := reverse(buf[:])
	res := new(big.Int).SetBytes(reversed)
	fmt.Println(fmt.Sprintf("llvm: fib(%d) = %s, used time %d ns", n, res.String(), time.Now().Sub(now).Nanoseconds()))
	now = time.Now()
	fmt.Println(fmt.Sprintf("native: fib(%d) = %s, used time %d ns", n, fib(n).String(), time.Now().Sub(now).Nanoseconds()))
}

func reverse(b []byte) []byte {
	out := make([]byte, len(b))
	for i := range b {
		out[len(b)-1-i] = b[i]
	}
	return out
}
