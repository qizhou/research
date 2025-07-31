#include <llvm/ExecutionEngine/Orc/LLJIT.h>
#include <llvm/ExecutionEngine/Orc/ThreadSafeModule.h>
#include <llvm/Object/ObjectFile.h>
#include <llvm/Support/TargetSelect.h>
#include <llvm/Support/MemoryBuffer.h>
#include <llvm/Support/Error.h>
#include <iostream>

using namespace llvm;
using namespace llvm::orc;

int main() {
    // Initialize LLVM
    InitializeNativeTarget();
    InitializeNativeTargetAsmPrinter();
    InitializeNativeTargetAsmParser();

    // Create the ORC JIT engine
    auto JIT = cantFail(LLJITBuilder().create());

    // Load fib.o into a memory buffer
    auto ObjBuffer = MemoryBuffer::getFile("fib.o");
    if (!ObjBuffer) return 2;

    // Add the object file to the JIT session
    cantFail(JIT->addObjectFile(std::move(*ObjBuffer)));

    // Look up symbol (must be exported, e.g., "fib")
    auto Sym = JIT->lookup("fib");
    if (!Sym) {
        logAllUnhandledErrors(Sym.takeError(), llvm::errs(), "Lookup error: ");
        return 1;
    }

    // Cast the function pointer and call
    using FibFn = int(*)(int);
    FibFn fib = (FibFn)(Sym->getAddress());

    int result = fib(10);
    std::cout << "fib(10000) = " << result << std::endl;

    return 0;
}

