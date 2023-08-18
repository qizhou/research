import wasm
import sys
import io

if __name__ == "__main__":
    if len(sys.argv) <= 4:
        print("need 4 arguments")
        sys.exit(1)
    
    source = sys.argv[1]
    dest = sys.argv[2]

    oldname = bytes(sys.argv[3], "utf-8")
    newname = bytes(sys.argv[4], "utf-8")

    print("renaming {} to {} ...".format(oldname, newname))

    with open(source, "rb") as inp, open(dest, "wb") as out:
        r = wasm.WasmReader(inp)
        w = wasm.WasmWriter(out)
        # magic
        assert r._read(4) == bytes.fromhex("0061736d")
        # version
        assert r._read(4) == bytes.fromhex("01000000")

        w._write(bytes.fromhex("0061736d01000000"))

        # section
        while True:
            try:
                sid = r._readByte()
            except EOFError:
                break

            size = r.readU32()
            bs = r._read(size)
            
            if sid == 7:
                sectionReader = wasm.WasmReader(io.BytesIO(bs))
                importSec = sectionReader.readVecOf(sectionReader.readExport)
                for i, imp in enumerate(importSec):
                    if imp[0] == oldname:
                        print("renaming {} from export to {}".format(oldname, newname))
                        importSec[i] = (newname, imp[1])
                
                sectionWriter = wasm.WasmWriter(io.BytesIO())
                sectionWriter.writeVecOf(importSec, sectionWriter.writeExport)
                sectionWriter._flush()

                bs = sectionWriter._getvalue()
            elif sid == 2:
                sectionReader = wasm.WasmReader(io.BytesIO(bs))
                importSec = sectionReader.readVecOf(sectionReader.readImport)
                for i, imp in enumerate(importSec):
                    if imp[1] == oldname:
                        print("renaming {}.{} from import to {}.{}".format(imp[0], oldname, imp[0], newname))
                        imp = list(imp)
                        imp[1] = newname
                        importSec[i] = tuple(imp)
                
                sectionWriter = wasm.WasmWriter(io.BytesIO())
                sectionWriter.writeVecOf(importSec, sectionWriter.writeImport)
                sectionWriter._flush()

                bs = sectionWriter._getvalue()

            w._writeByte(sid)
            w.writeU32(len(bs))
            w._write(bs)
            