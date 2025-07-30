package main

import (
	"fmt"
	"math/big"
	"os"
	"time"
	"unsafe"

	"tinygo.org/x/go-llvm"
)

// #include <stdint.h>
// typedef void (*fib)(uint32_t, uint8_t* buf);
// static void call_fib(uint64_t f, uint32_t x, uint8_t* buf) { ((fib)f)(x, buf); }
// extern void hostLogFunc(char* msg);
import "C"

//export hostLogFunc
func hostLogFunc(msg *C.char) {
	fmt.Println("Host Log:", C.GoString(msg))
}

func main() {
	llvm.InitializeNativeTarget()
	llvm.InitializeNativeAsmPrinter()

	ctx := llvm.NewContext()
	module := ctx.NewModule("fib_module")

	// fibonnaci
	uint_type := ctx.IntType(256)
	fib_args := []llvm.Type{ctx.Int32Type(), llvm.PointerType(uint_type, 0)}
	fib_type := llvm.FunctionType(ctx.VoidType(), fib_args, false)
	fib_func := llvm.AddFunction(module, "fib", fib_type)
	fib_func.SetFunctionCallConv(llvm.CCallConv)
	n := fib_func.Param(0)
	out := fib_func.Param(1)

	entry := llvm.AddBasicBlock(fib_func, "entry")
	loop_block := llvm.AddBasicBlock(fib_func, "loop")
	loop_body_block := llvm.AddBasicBlock(fib_func, "loop_body")
	after_loop_block := llvm.AddBasicBlock(fib_func, "after_loop")

	builder := ctx.NewBuilder()
	defer builder.Dispose()

	builder.SetInsertPointAtEnd(entry)
	a_ptr := builder.CreateAlloca(uint_type, "a")
	b_ptr := builder.CreateAlloca(uint_type, "b")
	i_ptr := builder.CreateAlloca(ctx.Int32Type(), "i")
	builder.CreateStore(llvm.ConstInt(uint_type, 0, false), a_ptr)
	builder.CreateStore(llvm.ConstInt(uint_type, 1, false), b_ptr)
	builder.CreateStore(llvm.ConstInt(ctx.Int32Type(), 0, false), i_ptr)
	builder.CreateBr(loop_block)

	builder.SetInsertPointAtEnd(loop_block)
	i_val := builder.CreateLoad(ctx.Int32Type(), i_ptr, "i_val")
	cond := builder.CreateICmp(llvm.IntULT, i_val, n, "loopcond")
	builder.CreateCondBr(cond, loop_body_block, after_loop_block)

	builder.SetInsertPointAtEnd(loop_body_block)
	a_val := builder.CreateLoad(uint_type, a_ptr, "a_val")
	b_val := builder.CreateLoad(uint_type, b_ptr, "b_val")
	next_a := b_val
	next_b := builder.CreateAdd(a_val, b_val, "next_b")
	builder.CreateStore(next_a, a_ptr)
	builder.CreateStore(next_b, b_ptr)
	next_i := builder.CreateAdd(i_val, llvm.ConstInt(ctx.Int32Type(), 1, false), "next_i")
	builder.CreateStore(next_i, i_ptr)
	builder.CreateBr(loop_block)

	builder.SetInsertPointAtEnd(after_loop_block)
	result := builder.CreateLoad(uint_type, a_ptr, "result")
	builder.CreateStore(result, out)

	// // host function
	// i8ptr := llvm.PointerType(ctx.Int8Type(), 0)
	// hostLogType := llvm.FunctionType(ctx.VoidType(), []llvm.Type{i8ptr}, false)
	// logFunc := llvm.AddFunction(module, "host_log", hostLogType)
	// str := builder.CreateGlobalStringPtr("hello world!", "msg")
	// builder.CreateCall(hostLogType, logFunc, []llvm.Value{str}, "")

	builder.CreateRetVoid()

	err := llvm.VerifyModule(module, llvm.ReturnStatusAction)
	if err != nil {
		panic(fmt.Sprintf("failed to verify module: %s", err))
	}

	engine, err := llvm.NewJITCompiler(module, 3)
	if err != nil {
		panic(fmt.Sprintf("Error creating JIT: %s", err))
	}
	defer engine.Dispose()

	// host function
	// engine.AddGlobalMapping(logFunc, unsafe.Pointer(C.hostLogFunc))
	pointer := engine.GetFunctionAddress("fib")

	input := 10001
	now := time.Now()
	// // Buffer to receive 32 bytes of result
	var buf [32]byte
	C.call_fib(C.uint64_t(pointer), C.uint32_t(input), (*C.uchar)(unsafe.Pointer(&buf[0])))
	// Convert little endian 32 bytes to big.Int
	res := new(big.Int).SetBytes(reverse(buf[:]))
	fmt.Printf("llvm getFunctionAddress(): fib(%d) = %s, used time %d ns\n", input, res.String(), time.Now().Sub(now).Nanoseconds())
	if res.String() != "100569663553364666514085384053693927634549891439552765559319131137058237310013" {
		panic("wrong result")
	}

	now1 := time.Now()
	var buf1 [32]byte
	exec_args := []llvm.GenericValue{llvm.NewGenericValueFromInt(ctx.Int32Type(), uint64(input), false), llvm.NewGenericValueFromPointer(unsafe.Pointer(&buf1[0]))}
	engine.RunFunction(fib_func, exec_args)
	res1 := new(big.Int).SetBytes(reverse(buf1[:]))
	fmt.Printf("llvm runFunction(): fib(%d) = %s, used time %d ns\n", input, res1.String(), time.Now().Sub(now1).Nanoseconds())

	// Write to files
	os.WriteFile("fib.ll", []byte(module.String()), 0644)

	// Write to object file
	target, err := llvm.GetTargetFromTriple(llvm.DefaultTargetTriple())
	if err != nil {
		panic(err)
	}

	targetMachine := target.CreateTargetMachine(
		llvm.DefaultTargetTriple(), "generic", "", llvm.CodeGenLevelDefault,
		llvm.RelocDefault, llvm.CodeModelDefault)

	mem, err := targetMachine.EmitToMemoryBuffer(module, llvm.ObjectFile)
	if err != nil {
		panic(err)
	}
	os.WriteFile("fib.o", mem.Bytes(), 0644)

	mem, err = targetMachine.EmitToMemoryBuffer(module, llvm.AssemblyFile)
	if err != nil {
		panic(err)
	}
	os.WriteFile("fib.asm", mem.Bytes(), 0644)

	file, err := os.OpenFile("fib.bc", os.O_CREATE|os.O_RDWR, 0644)
	if err != nil {
		panic(err)
	}
	llvm.WriteBitcodeToFile(module, file)
}

func reverse(b []byte) []byte {
	out := make([]byte, len(b))
	for i := range b {
		out[len(b)-1-i] = b[i]
	}
	return out
}
