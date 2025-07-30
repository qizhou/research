#include <llvm/Object/ObjectFile.h>
#include <llvm/Object/ELF.h>
#include <llvm/Support/MemoryBuffer.h>
#include <llvm/Support/Error.h>
#include <llvm/Support/raw_ostream.h>

using namespace llvm;
using namespace llvm::object;

int main() {
    // Load the .o file into memory
    auto FileOrErr = MemoryBuffer::getFile("fib.o");
    if (!FileOrErr) {
        errs() << "Error reading file\n";
        return 1;
    }

    auto ObjOrErr = ObjectFile::createObjectFile(FileOrErr->get()->getMemBufferRef());
    if (!ObjOrErr) {
        logAllUnhandledErrors(ObjOrErr.takeError(), errs(), "object error: ");
        return 1;
    }

    ObjectFile &Obj = **ObjOrErr;

    // Iterate symbols
    for (const SymbolRef &Sym : Obj.symbols()) {
        Expected<StringRef> NameOrErr = Sym.getName();
        if (NameOrErr)
            outs() << "Symbol: " << *NameOrErr << "\n";
        else
            logAllUnhandledErrors(NameOrErr.takeError(), errs(), "symbol name error: ");
    }

    // Iterate sections
    for (const SectionRef &Sec : Obj.sections()) {
        Expected<StringRef> NameOrErr = Sec.getName();
        if (NameOrErr)
            outs() << "Section: " << *NameOrErr << "\n";
        else
            logAllUnhandledErrors(NameOrErr.takeError(), errs(), "section name error: ");
    }

    return 0;
}