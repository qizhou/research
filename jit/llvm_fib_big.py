from llvmlite import ir, binding
import ctypes

# === Initialize LLVM ===
binding.initialize()
binding.initialize_native_target()
binding.initialize_native_asmprinter()

# bits of large integer
N = 256
M = N // 8 # bytes

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

def build_fib256_ir():
    module = ir.Module(name="fib256")
    # 256 causes core dump on python3.10+llvmlite0.44.0.
    # 128 works but the output seems to be wrong
    # 64 works as expected
    intN = ir.IntType(N)
    int32 = ir.IntType(32)
    func_type = ir.FunctionType(ir.VoidType(), [int32, ir.PointerType(intN)])
    fib_func = ir.Function(module, func_type, name="fib")

    n = fib_func.args[0]
    out = fib_func.args[1]
    n.name = "n"

    # Create blocks
    entry_block = fib_func.append_basic_block(name="entry")
    loop_block = fib_func.append_basic_block(name="loop")
    after_loop_block = fib_func.append_basic_block(name="after_loop")

    builder = ir.IRBuilder(entry_block)

    # Allocate and initialize: a = 0, b = 1, i = 0
    a_ptr = builder.alloca(intN, name="a")
    b_ptr = builder.alloca(intN, name="b")
    i_ptr = builder.alloca(int32, name="i")

    builder.store(intN(0), a_ptr)
    builder.store(intN(1), b_ptr)
    builder.store(int32(0), i_ptr)

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

    builder.branch(after_loop_block)

    # === After loop ===
    builder.position_at_start(after_loop_block)
    result = builder.load(a_ptr, name="result")
    builder.store(result, out)
    builder.ret_void()

    return module

# Convert N-bit return value to Python int
def intN_from_ptr(ptr):
    # Define a M-byte (N-bit) structure
    class UintN(ctypes.Structure):
        _fields_ = [("bytes", ctypes.c_ubyte * M)]
    raw = ctypes.cast(ptr, ctypes.POINTER(UintN)).contents
    return int.from_bytes(bytearray(raw.bytes), "little")

def main():
    engine = create_execution_engine()
    llvm_module = build_fib256_ir()
    llvm_ir = str(llvm_module)
    print("Generated LLVM IR:")
    print(llvm_ir)

    compile_ir(engine, llvm_ir)
    func_ptr = engine.get_function_address("fib")

    # Define function: returns M bytes
    # Simulate as void* return and interpret as N-bit integer
    fib_cfunc = ctypes.CFUNCTYPE(None, ctypes.c_int32, ctypes.c_char_p)(func_ptr)

    buf = ctypes.create_string_buffer(M)

    for i in range(0, 10001, 1000):
        fib_cfunc(i, buf)
        result = int.from_bytes(bytes(buf), "little")
        print(f"fib({i}) = {result}")

    i = 10001
    fib_cfunc(i, buf)
    result = int.from_bytes(bytes(buf), "little")
    assert result == 100569663553364666514085384053693927634549891439552765559319131137058237310013

if __name__ == "__main__":
    main()
