// jit_wrapper.cpp
#include "jit_wrapper.h"
#include <llvm/ADT/StringRef.h>
#include <llvm/ExecutionEngine/Orc/LLJIT.h>
#include <llvm/IRReader/IRReader.h>
#include <llvm/Support/MemoryBuffer.h>
#include <llvm/Support/SourceMgr.h>
#include <llvm/Support/TargetSelect.h>
#include <llvm/IR/LegacyPassManager.h>
#include <llvm/Transforms/IPO/PassManagerBuilder.h>
#include <memory>
#include <iostream>


using namespace llvm;
using namespace llvm::orc;

static std::unique_ptr<LLJIT> J;
static JITEvaluatedSymbol FibSym;

int init_jit(const char *llvm_ir_file) {
    InitializeNativeTarget();
    InitializeNativeTargetAsmPrinter();

    SMDiagnostic Err;
    LLVMContext Context;
    auto Mod = parseIRFile(llvm_ir_file, Err, Context);
    if (!Mod) {
        Err.print("jit_wrapper", errs());
        return 1;
    }

    auto JIT = LLJITBuilder().create();
    if (!JIT) return 2;

    // Add optimization transform
    (*JIT)->getIRTransformLayer().setTransform(
        [](ThreadSafeModule TSM, const MaterializationResponsibility&) -> Expected<ThreadSafeModule> {
            TSM.withModuleDo(
                [](Module &M) {
                    llvm::legacy::PassManager PM;
                    llvm::PassManagerBuilder PMB;
                    PMB.OptLevel = 3; // O3 optimization
                    PMB.populateModulePassManager(PM);
                    PM.run(M);
                }
            );
            return TSM;
        }
    );

    J = std::move(*JIT);
    if (auto Err = J->addIRModule(ThreadSafeModule(std::move(Mod), std::make_unique<LLVMContext>())))
        return 3;

    auto Sym = J->lookup("fib");
    if (!Sym) return 4;

    FibSym = *Sym;
    return 0;
}

int init_jit_from_obj(const char *obj_file) {
    InitializeNativeTarget();
    InitializeNativeTargetAsmPrinter();
    InitializeNativeTargetAsmParser();

    auto JIT = LLJITBuilder().create();
    if (!JIT) return 2;

    // Load fib.o into a memory buffer
    auto ObjBuffer = MemoryBuffer::getFile(obj_file);
    if (!ObjBuffer) return 3;

    // Add the object to the JIT
    auto ret = (*JIT)->addObjectFile(std::move(*ObjBuffer));
    if (!ret) return 4;

    J = std::move(*JIT);
    auto Sym = J->lookup("fib");
    if (!Sym) return 5;

    FibSym = *Sym;
    return 0;
}

int call_fib(int n, uint8_t* result_buf) {
    using FibFn = void(*)(int32_t, uint8_t*);
    auto func = (FibFn)FibSym.getAddress();
    func(n, result_buf);
    return 0;
}
