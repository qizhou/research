package main

import (
	"fmt"

	"tinygo.org/x/go-llvm"
)

func main() {
	llvm.InitializeNativeTarget()
	llvm.InitializeNativeAsmPrinter()

	ctx := llvm.NewContext()
	module := ctx.NewModule("fib_module")

	// Define i32 fib(i32)
	fib_args := []llvm.Type{ctx.Int32Type()}
	uint_type := ctx.IntType(64)
	fib_type := llvm.FunctionType(uint_type, fib_args, false)
	fib_func := llvm.AddFunction(module, "fib", fib_type)
	fib_func.SetFunctionCallConv(llvm.CCallConv)
	n := fib_func.Param(0)

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
	builder.CreateRet(result)

	err := llvm.VerifyModule(module, llvm.ReturnStatusAction)
	if err != nil {
		panic(fmt.Sprintf("failed to verify module: %s", err))
	}

	options := llvm.NewMCJITCompilerOptions()
	options.SetMCJITOptimizationLevel(2)
	options.SetMCJITEnableFastISel(true)
	options.SetMCJITNoFramePointerElim(true)
	options.SetMCJITCodeModel(llvm.CodeModelJITDefault)
	engine, err := llvm.NewMCJITCompiler(module, options)
	if err != nil {
		panic(fmt.Sprintf("Error creating JIT: %s", err))
	}
	defer engine.Dispose()

	exec_args := []llvm.GenericValue{llvm.NewGenericValueFromInt(ctx.Int32Type(), 10, false)}
	exec_res := engine.RunFunction(fib_func, exec_args)
	// var fib uint64 = 55
	// if exec_res.Int(false) != fib {
	// 	panic(fmt.Sprintf("Expected %d, got %d", fib, exec_res.Int(false)))
	// }
	fmt.Println(exec_res.IntWidth())
}
