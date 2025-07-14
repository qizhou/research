package main

import (
	"crypto/sha256"
	"encoding/binary"
	"flag"
	"fmt"

	"github.com/syndtr/goleveldb/leveldb"
)

var n = flag.Int64("n", 100000, "number of IOs")

var startKey = flag.Int64("start", 0, "start key")
var endKey = flag.Int64("end", 0, "end key, = startKey + n if 0")
var op = flag.String("op", "randwrite", "operation: write, randwrite, read, randread")
var r = flag.Int64("r", 10000, "report interval")
var valueSizeSmall = flag.Int("s", 50, "value size small")
var valueSizeBig = flag.Int("S", 51, "value size big (inclusive)")

func main() {
	flag.Parse()

	if *endKey == 0 {
		*endKey = *startKey + *n
	}

	db, err := leveldb.OpenFile("bench_db", nil)
	if err != nil {
		panic(err)
	}

	if *op == "write" {
		for i := *startKey; i < *endKey; i++ {
			hfunc := sha256.New()
			buf := make([]byte, 8)
			binary.BigEndian.PutUint64(buf, uint64(i))
			hfunc.Write(buf)
			key := hfunc.Sum(nil)

			valueSize := i%int64(*valueSizeBig-*valueSizeSmall) + int64(*valueSizeSmall)

			value := make([]byte, valueSize)
			for j := 0; j < len(value); j++ {
				value[j] = byte(int(i) + j)
			}

			db.Put(key, value, nil)
			if i%*r == 0 {
				fmt.Println(i)
			}
		}
	}
}
