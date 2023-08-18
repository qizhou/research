import io
import sys
from collections import namedtuple

NUM_TYPE_I32 = 0x7F
NUM_TYPE_I64 = 0x7E
NUM_TYPE_F32 = 0x7D
NUM_TYPE_F64 = 0x7C
VEC_TYPE = 0x7B
REF_TYPE_FUNCREF = 0x70
REF_TYPE_EXTERNREF = 0x6F

VALUE_TYPES = {
    NUM_TYPE_I32, NUM_TYPE_I64, NUM_TYPE_F32, NUM_TYPE_F64,
    VEC_TYPE, REF_TYPE_FUNCREF, REF_TYPE_EXTERNREF
}

Code = namedtuple("Code", ["size", "func"])
Func = namedtuple("Func", ["vec_locals", "expr"])
Locals = namedtuple("Locals", ["n", "t"])
        

class WasmReader:
    def __init__(self, r):
        self.r = r        
    
    def _read(self, size=1):
        return self.r.read(size)
    
    def _readByte(self):
        b = self.r.read(1)
        if len(b) == 0:
            raise EOFError()
        return b[0]
    
    def _readAll(self):
        return self.r.read(-1)
    
    def readU32(self):
        v = 0
        m = 1
        while True:
            x = self._readByte()
            if x >= 128:
                v += m * (x - 128)
            else:
                v += m * x
                break
            m *= 128
        return v
    
    def readFuncType(self):
        b = self._readByte()
        assert b == 0x60 # func type
        return (self.readResultType(), self.readResultType())

    def readValType(self):
        valtype = self._readByte()
        if valtype not in VALUE_TYPES:
            raise Exception("unsupported valtype {}".format(valtype))
        return valtype
    
    def readRefType(self):
        reftype = self._readByte()
        assert reftype == REF_TYPE_EXTERNREF or reftype == REF_TYPE_FUNCREF
        return reftype
        
    def readResultType(self):
        size = self.readU32()
        rt = []
        for _ in range(size):
            rt.append(self.readValType())
        return rt
    
    def readType(self):
        return self.readVecOf(self.readFuncType)
    
    def readVecOf(self, readFunc):
        size = self.readU32()
        return [readFunc() for _ in range(size)]
    
    def readExport(self):
        return (self.readName(), self.readExportDesc())
    
    def readBytes(self):
        size = self.readU32()
        return self._read(size)

    def readName(self):
        return self.readBytes()
        
    def readExportDesc(self):
        t = self._readByte()
        idx = self._readByte()
        assert t in {0, 1, 2, 3}
        # check IDX
        return (t, idx)
    
    def readFunc(self):
        return Func(self.readVecOf(self.readLocals), self._readAll())

    def readExpr(self):
        pass
    
    def readLocals(self):
        return Locals(self._readByte(), self.readValType())
        
    def readCode(self):
        size = self.readU32()
        bs = self._read(size)
        r = WasmReader(io.BytesIO(bs))
        return Code(size, r.readFunc())
    
    def readTable(self):
        return self.readVecOf(self.readRefType)
    
    def readLimits(self):
        t = self._readByte()
        if t == 0:
            return (self.readU32(), 2 ** 32 - 1)
        else:
            return (self.readU32(), self.readU32())
        
    def readGlobalType(self):
        # mutable, valtype
        return (self._readByte(), self.readValType())
    
    def readGlobal(self):
        return (self.readGlobalType(), self.readExpr())
    
    def readData(self):
        t = self._readByte()
        if t == 0:
            return (0, self.readExpr(), self.readBytes())
        elif t == 1:
            return (1, self.readBytes())
        elif t == 2:
            return (2, self.readU32(), self.readExpr(), self.readBytes)
        


class Module:

    sectionHandler = {
    }

    inited = False

    def __init_class(self):
        if self.inited:
            return
        
        self.sectionHandler = {
            0: self.handleCustomSection,
            1: self.handleTypeSection,
            3: self.handleFuncSection,
            4: self.handleTableSection,
            5: self.handleMemorySection,
            6: self.handleGlobalSection,
            7: self.handleExportSecion,
            10: self.handleCodeSection,
            11: self.handleDataSection,
        }

    def __init__(self, r):
        self.__init_class()

        # magic
        assert r._read(4) == bytes.fromhex("0061736d")
        # version
        assert r._read(4) == bytes.fromhex("01000000")

        # section
        while True:
            try:
                sid = r._readByte()
            except EOFError:
                break
            if sid not in self.sectionHandler:
                raise Exception("{} section id not supported".format(sid))
            size = r.readU32()
            bsr = WasmReader(io.BytesIO(r._read(size)))
            self.sectionHandler[sid](bsr)

    def handleTypeSection(self, r):
        print("detect type")
        self.typeSec = r.readType()
        print("types = {}".format(self.typeSec))

    def handleFuncSection(self, r):
        print("detect func")
        self.funcSec = r.readVecOf(r.readU32)
        print("funcs = {}".format(self.funcSec))

    def handleExportSecion(self, r):
        print("detect func")
        self.exportSec = r.readVecOf(r.readExport)
        print("exports = {}".format(self.exportSec))

    def handleCodeSection(self, r):
        print("detect code")
        self.codeSec = r.readVecOf(r.readCode)
        print("codes = {}".format(self.codeSec))

    def handleTableSection(self, r):
        print("detect table")
        self.tableSec = r.readVecOf(r.readRefType)
        print("tables = {}".format(self.tableSec))

    def handleMemorySection(self, r):
        print("detect memory")
        self.memorySec = r.readVecOf(r.readLimits)
        print("memory = {}".format(self.memorySec))

    def handleGlobalSection(self, r):
        print("detect global")
        self.globals = r.readGlobal()
        print("globals = {}".format(self.globals))

    def handleDataSection(self, r):
        print("detect data")
        self.dataSec = r.readVecOf(r.readData)
        print("dataSec = {}".format(self.dataSec))

    def handleCustomSection(self, r: WasmReader):
        print("detect custom")
        self.customSec = (r.readName(), r._readAll())
        print("customSec = {}".format(self.customSec))

        

def test():
    filename = sys.argv[1] if len(sys.argv) >= 2 else "test.wasm"
    with open(filename, "rb") as f:
        m = Module(WasmReader(f))

if __name__ == "__main__":
    test()