package main

/*
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>

#include <errno.h>
#include <signal.h>
#include <sys/mman.h>
#include <setjmp.h>

void* allocate_stack() {
	void* ptr = mmap(NULL, 40*1024, PROT_NONE, MAP_PRIVATE | MAP_ANON, -1, 0);
    if (mprotect(ptr+4*1024, 32*1024, PROT_READ | PROT_WRITE) == -1) {
        perror("mprotect error");
        exit(EXIT_FAILURE);
    }
	return ptr;
}

*/
import "C"
import (
	"fmt"
	"reflect"
	"runtime/debug"
	"unsafe"

	"github.com/holiman/uint256"
)

func main() {
	fmt.Println("Starting program")

	// This function will cause a panic
	debug.SetPanicOnFault(true)

	fault()

	fmt.Println("Program continues after potential recovery") // This line will execute if recovered
}

func fault() {
	// Defer a function to recover from potential panics
	defer func() {
		if r := recover(); r != nil {
			fmt.Println("Recovered from panic:", r)
			receiverValue := reflect.ValueOf(r)
			method := receiverValue.MethodByName("Addr")
			results := method.Call([]reflect.Value{})
			if len(results) > 0 {
				fmt.Printf("Invalid access at %p\n", unsafe.Pointer(results[0].Interface().(uintptr)))
			}
		}
	}()

	ptr := C.allocate_stack()
	fmt.Printf("Allocated stack at %p\n", ptr)
	buf := unsafe.Slice((*uint256.Int)(ptr), 32*40)
	fmt.Println("Accessing 256 stack element")
	buf[256].SetUint64(6)
	fmt.Println("Accessing 4 stack element")
	buf[4].SetUint64(3)
	fmt.Println("Accessing 512 stack element")
	buf[512].SetUint64(1)
}
