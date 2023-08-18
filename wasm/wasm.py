import io

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
        return self.r.read(1)[0]
    
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
        len = self.readU32()
        print("type len = {}".format(len))
        ts = []
        for _ in range(len):
            ft = self.readFuncType()
            print(ft)
            ts.append(ft)
        return ts


class Module:

    sectionHandler = {
    }

    inited = False

    def __init_class(self):
        if self.inited:
            return
        
        self.sectionHandler = {
            1: self.typeHandler,
            3: self.funcHandler
        }

    def __init__(self, r):
        self.__init_class()

        # magic
        assert r.read(4) == bytes.fromhex("0061736d")
        # version
        assert r.read(4) == bytes.fromhex("01000000")

        # section
        sid = r.readByte()
        if sid not in self.sectionHandler:
            raise Exception("{} section id not supported".format(sid))
        size = r.readU32()
        bs = r.read(size)
        self.sectionHandler[sid](bs)

    def typeHandler(self, bs):
        print("detect type")
        r = Reader(io.BytesIO(bs))
        self.types = r.readType()
        


def test():
    with open("test.wasm", "rb") as f:
        m = Module(Reader(f))

if __name__ == "__main__":
    test()