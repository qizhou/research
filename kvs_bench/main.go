package main

import (
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"flag"
	"fmt"
	"math/rand"
	"sync"

	"github.com/syndtr/goleveldb/leveldb"
)

var n = flag.Int64("n", 100000, "number of IOs")

var startKeyFlag = flag.Int64("start", 0, "start key")
var op = flag.String("op", "randwrite", "operation: write, randwrite, read, randread")
var r = flag.Int64("r", 10000, "report interval")
var valueSizeSmall = flag.Int("s", 50, "value size small")
var valueSizeBig = flag.Int("S", 51, "value size big (inclusive)")
var t = flag.Int("t", 8, "threads")
var v = flag.Int("v", 3, "verbosity")

func main() {
	flag.Parse()

	db, err := leveldb.OpenFile("bench_db", nil)
	if err != nil {
		panic(err)
	}

	if *op == "write" || *op == "randwrite" {
		tsize := *n / int64(*t)

		var wg sync.WaitGroup

		keys := make([]int64, *n)
		for i := int64(0); i < *n; i++ {
			keys[i] = i + *startKeyFlag
		}

		if *op == "randwrite" {
			rand.Shuffle(len(keys), func(i, j int) { keys[i], keys[j] = keys[j], keys[i] })
		}

		for ti := 0; ti < *t; ti++ {
			endKey := int64(ti+1) * tsize
			if ti == *t-1 {
				endKey = *startKeyFlag + *n
			}

			wg.Add(1)
			go func(ti int, keys []int64) {
				defer wg.Done()
				for i := 0; i < len(keys); i++ {
					hfunc := sha256.New()
					buf := make([]byte, 8)
					binary.BigEndian.PutUint64(buf, uint64(keys[i]))
					hfunc.Write(buf)
					key := hfunc.Sum(nil)

					valueSize := keys[i]%int64(*valueSizeBig-*valueSizeSmall) + int64(*valueSizeSmall)

					value := make([]byte, valueSize)
					for j := 0; j < len(value); j++ {
						value[j] = byte(int(keys[i]) + j)
					}

					db.Put(key, value, nil)
					if *v == 4 {
						fmt.Printf("thread: %d, write %d\n", ti, keys[i])
					} else if *v == 5 {
						fmt.Printf("thread: %d, write %s:%s\n", ti, hex.EncodeToString(key), hex.EncodeToString(value))
					}
					if int64(i)%*r == 0 {
						fmt.Printf("thread: %d, task: %d\n", ti, i)
					}
				}
			}(ti, keys[int64(ti)*tsize:endKey])
		}
		wg.Wait()
	}
}
