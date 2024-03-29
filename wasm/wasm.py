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
    
    def readTableType(self):
        return (self.readRefType(), self.readLimits())
    
    def readVecOf(self, readFunc):
        size = self.readU32()
        return [readFunc() for _ in range(size)]
    
    def readExport(self):
        name = self.readName()
        desc = self.readExportDesc()
        return (name, desc)
    
    def readBytes(self):
        size = self.readU32()
        return self._read(size)

    def readName(self):
        return self.readBytes()
        
    def readExportDesc(self):
        t = self._readByte()
        idx = self.readU32()
        assert t in {0, 1, 2, 3}
        # check IDX
        return (t, idx)
    
    def readFunc(self):
        return Func(self.readVecOf(self.readLocals), self._readAll())

    def readExpr(self):
        # TODO:
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
        else:
            assert False
        
    def readImport(self):
        modname = self.readName()
        name = self.readName()
        t = self._readByte()
        if t == 0:
            # typeidx => func[typeidx]
            # TODO: check func exists
            return (modname, name, t, self.readU32())
        elif t == 1:
            return (modname, name, t, self.readTableType())
        elif t == 2:
            # memory type
            return (modname, name, t, self.readLimits())
        elif t == 3:
            return (modname, name, t, self.readGlobalType())
        else:
            assert False


class WasmWriter:
    def __init__(self, w):
        self.w = w  
    
    def _write(self, bs):
        return self.w.write(bs)
    
    def writeU32(self, v):
        while True:
            if v >= 128:
                self._write(bytes([v % 128 + 128]))
                v = v // 128
            else:
                self._write(bytes([v]))
                break

    def _writeByte(self, b):
        self._write(bytes([b]))

    def _flush(self):
        self.w.flush()

    def _getvalue(self):
        return self.w.getvalue()
    
    def writeBytes(self, bs):
        self.writeU32(len(bs))
        return self._write(bs)

    def writeName(self, name):
        return self.writeBytes(name)
        
    def writeExportDesc(self, desc):
        self._writeByte(desc[0])
        self.writeU32(desc[1])

    def writeExport(self, export):
        self.writeName(export[0])
        self.writeExportDesc(export[1])

    def writeVecOf(self, vec, func):
        self.writeU32(len(vec))
        for v in vec:
            func(v)

    def writeImport(self, imp):
        modname = imp[0]
        name = imp[1]
        t = imp[2]
        self.writeName(modname)
        self.writeName(name)
        self._writeByte(t)
        if t == 0:
            # typeidx => func[typeidx]
            self.writeU32(imp[3])
        elif t == 1: 
            raise NotImplementedError()
            #return (modname, name, t, self.readTableType())
        elif t == 2:
            raise NotImplementedError()
            # memory type
            #return (modname, name, t, self.readLimits())
        elif t == 3:
            raise NotImplementedError()
            # return (modname, name, t, self.readGlobalType())
        else:
            assert False


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
            2: self.handleImportSection,
            3: self.handleFuncSection,
            4: self.handleTableSection,
            5: self.handleMemorySection,
            6: self.handleGlobalSection,
            7: self.handleExportSecion,
            9: self.handleElementSection,
            10: self.handleCodeSection,
            11: self.handleDataSection,
        }
        self.inited = True

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
            bs = r._read(size)
            bsr = WasmReader(io.BytesIO(bs))
            self.sectionHandler[sid](bsr)

    def handleTypeSection(self, r):
        print("detect type")
        self.typeSec = r.readType()
        print("types = {}".format(self.typeSec))

    def handleFuncSection(self, r):
        print("detect func")
        self.funcSec = r.readVecOf(r.readU32)
        print("funcs = {}".format(self.funcSec))

    def handleExportSecion(self, r: WasmReader):
        print("detect export")
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

    def handleImportSection(self, r: WasmReader):
        print("detect import")
        self.importSec = r.readVecOf(r.readImport)
        print("importSec = {}".format(self.importSec))

    def handleElementSection(self, r: WasmReader):
        print("skip element")

        

def test():
    filename = sys.argv[1] if len(sys.argv) >= 2 else "test.wasm"
    with open(filename, "rb") as f:
        m = Module(WasmReader(f))

if __name__ == "__main__":
    test()