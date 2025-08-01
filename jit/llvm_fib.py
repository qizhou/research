from llvmlite import ir, binding
import ctypes
import time

# === Initialize LLVM ===
binding.initialize()
binding.initialize_native_target()
binding.initialize_native_asmprinter()

def create_execution_engine():
    target = binding.Target.from_default_triple()
    target_machine = target.create_target_machine()
    backing_mod = binding.parse_assembly("")
    engine = binding.create_mcjit_compiler(backing_mod, target_machine)
    return engine

def compile_ir(engine, llvm_ir):
    mod = binding.parse_assembly(llvm_ir)
    mod.verify()
    engine.add_module(mod)
    engine.finalize_object()
    return mod

def build_iterative_fib_ir():
    module = ir.Module(name="fib_iter")
    int32 = ir.IntType(32)
    func_type = ir.FunctionType(int32, [int32])
    fib_func = ir.Function(module, func_type, name="fib")
    n = fib_func.args[0]
    n.name = "n"

    # Create blocks
    entry_block = fib_func.append_basic_block(name="entry")
    loop_block = fib_func.append_basic_block(name="loop")
    after_loop_block = fib_func.append_basic_block(name="after_loop")

    builder = ir.IRBuilder(entry_block)

    # Initial values: a = 0, b = 1, i = 0
    a_ptr = builder.alloca(int32, name="a")
    b_ptr = builder.alloca(int32, name="b")
    i_ptr = builder.alloca(int32, name="i")

    builder.store(int32(0), a_ptr)
    builder.store(int32(1), b_ptr)
    builder.store(int32(0), i_ptr)

    # Jump to loop block
    builder.branch(loop_block)

    # === Loop block ===
    builder.position_at_start(loop_block)
    i_val = builder.load(i_ptr, name="i_val")
    cond = builder.icmp_signed("<", i_val, n, name="loopcond")
    with builder.if_then(cond):
        a_val = builder.load(a_ptr, name="a_val")
        b_val = builder.load(b_ptr, name="b_val")
        next_a = b_val
        next_b = builder.add(a_val, b_val, name="next_b")

        builder.store(next_a, a_ptr)
        builder.store(next_b, b_ptr)

        next_i = builder.add(i_val, int32(1), name="next_i")
        builder.store(next_i, i_ptr)
        builder.branch(loop_block)

    # If not, exit loop
    builder.branch(after_loop_block)

    # === After loop ===
    builder.position_at_start(after_loop_block)
    result = builder.load(a_ptr, name="result")
    builder.ret(result)

    return module


def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, (a + b) % 2**32
    return a


def main():
    engine = create_execution_engine()
    llvm_module = build_iterative_fib_ir()
    llvm_ir = str(llvm_module)
    print("Generated LLVM IR:")
    print(llvm_ir)

    compile_ir(engine, llvm_ir)
    func_ptr = engine.get_function_address("fib")

    # Call from Python
    cfunc = ctypes.CFUNCTYPE(ctypes.c_uint32, ctypes.c_uint32)(func_ptr)

    n = 10000000
    t = time.monotonic()
    print(f"fib({n}) = {cfunc(n)}")
    print(f"used time ={time.monotonic() - t}")

    print("Python version")
    t = time.monotonic()
    print(f"fib({n}) = {fib(n)}")
    print(f"used time ={time.monotonic() - t}")


if __name__ == "__main__":
    main()
