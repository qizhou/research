import io
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
        

class Reader:
    def __init__(self, r):
        self.r = r        
    
    def readU32(self):
        v = 0
        m = 1
        while True:
            x = self.readByte()
            if x >= 128:
                v += m * (x - 128)
            else:
                v += m * x
                break
            m *= 128
        return v
    
    def read(self, size=1):
        return self.r.read(size)
    
    def readByte(self):
        b = self.r.read(1)
        if len(b) == 0:
            raise EOFError()
        return b[0]
    
    def readAll(self):
        return self.r.read(-1)
    
    def readFuncType(self):
        b = self.readByte()
        assert b == 0x60 # func type
        return (self.readResultType(), self.readResultType())

    def readValType(self):
        valtype = self.readByte()
        if valtype not in VALUE_TYPES:
            raise Exception("unsupported valtype {}".format(valtype))
        return valtype
        
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

    def readName(self):
        size = self.readU32()
        return self.read(size)

    def readExportDesc(self):
        t = self.readByte()
        idx = self.readByte()
        assert t in {0, 1, 2, 3}
        # check IDX
        return (t, idx)
    
    def readFunc(self):
        return Func(self.readVecOf(self.readLocals), self.readAll())

    def readExpr(self):
        pass
    
    def readLocals(self):
        return Locals(self.readByte(), self.readValType())
    
    def readCode(self):
        size = self.readU32()
        bs = self.read(size)
        r = Reader(io.BytesIO(bs))
        return Code(size, r.readFunc())


class Module:

    sectionHandler = {
    }

    inited = False

    def __init_class(self):
        if self.inited:
            return
        
        self.sectionHandler = {
            1: self.handleTypeSection,
            3: self.handleFuncSection,
            7: self.handleExportSecion,
            10: self.handleCodeSection
        }

    def __init__(self, r):
        self.__init_class()

        # magic
        assert r.read(4) == bytes.fromhex("0061736d")
        # version
        assert r.read(4) == bytes.fromhex("01000000")

        # section
        while True:
            try:
                sid = r.readByte()
            except EOFError:
                break
            if sid not in self.sectionHandler:
                raise Exception("{} section id not supported".format(sid))
            size = r.readU32()
            bs = r.read(size)
            self.sectionHandler[sid](bs)

    def handleTypeSection(self, bs):
        print("detect type")
        r = Reader(io.BytesIO(bs))
        self.types = r.readType()
        print("types = {}".format(self.types))

    def handleFuncSection(self, bs):
        print("detect func")
        r = Reader(io.BytesIO(bs))
        self.funcs = r.readVecOf(r.readU32)
        print("funcs = {}".format(self.funcs))

    def handleExportSecion(self, bs):
        print("detect func")
        r = Reader(io.BytesIO(bs))
        self.exports = r.readVecOf(r.readExport)
        print("exports = {}".format(self.exports))

    def handleCodeSection(self, bs):
        print("detect code")
        r = Reader(io.BytesIO(bs))
        self.code = r.readVecOf(r.readCode)
        print("code = {}".format(self.code))

def test():
    with open("test.wasm", "rb") as f:
        m = Module(Reader(f))

if __name__ == "__main__":
    test()