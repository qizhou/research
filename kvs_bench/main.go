package main

import (
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"flag"
	"fmt"
	"math/rand"
	"sync"
	"time"

	"github.com/ethereum/go-ethereum/ethdb"
	"github.com/ethereum/go-ethereum/ethdb/leveldb"
	"github.com/ethereum/go-ethereum/ethdb/pebble"
)

var n = flag.Int64("n", 1000000, "number of IOs")
var N = flag.Int64("N", 0, "size of the keys")

var startKeyFlag = flag.Int64("start", 0, "start key")
var op = flag.String("op", "randwrite", "operation: write, randwrite, read, randread")
var r = flag.Int64("r", 100000, "report interval")
var valueSizeSmall = flag.Int("s", 50, "value size small")
var valueSizeBig = flag.Int("S", 51, "value size big (inclusive)")
var t = flag.Int("t", 8, "threads")
var v = flag.Int("v", 3, "verbosity")
var dbn = flag.Int("dbn", 1, "number of dbs")
var dbFlag = flag.String("db", "goleveldb", "db type: goleveldb, pebble")
var valueFlag = flag.String("V", "fnv", "value generator: fnv, simple")

func generateRandomData(size int, seed uint64) []byte {
	// a simple FNV 64 bytes algorithm
	if size == 0 {
		return []byte{}
	}

	data := make([]byte, (size+7)/8*8)
	h := uint64(0xcbf29ce484222325) ^ seed
	for i := 0; i < len(data); i += 8 {
		h = h * uint64(0x00000100000001b3)
		binary.BigEndian.PutUint64(data[i:], h)
	}
	return data[:size]
}

func generateKeys() []int64 {
	keys := make([]int64, *N)
	for i := int64(0); i < *N; i++ {
		keys[i] = i + *startKeyFlag
	}

	if *op == "randwrite" || *op == "randread" {
		rand.Shuffle(len(keys), func(i, j int) { keys[i], keys[j] = keys[j], keys[i] })
	}
	return keys
}

func main() {
	flag.Parse()

	dbs := make([]ethdb.KeyValueStore, *dbn)
	for i := 0; i < *dbn; i++ {
		// db, err := leveldb.OpenFile(, nil)
		var db ethdb.KeyValueStore
		var err error
		if *dbFlag == "goleveldb" {
			db, err = leveldb.New(fmt.Sprintf("bench_leveldb_%d", i), 512, 0, "", false)
		} else if *dbFlag == "pebble" {
			db, err = pebble.New(fmt.Sprintf("bench_pebble_%d", i), 512, 0, "", false)
		} else {
			panic("Unknow db")
		}

		if err != nil {
			panic(err)
		}
		dbs[i] = db
		defer db.Close()
	}

	startTime := time.Now()

	if *N == 0 {
		*N = *n
	} else if *N < *n {
		panic("Insufficient keys")
	}

	if *op == "write" || *op == "randwrite" {
		tsize := *n / int64(*t)

		keys := generateKeys()

		startTime = time.Now()
		var wg sync.WaitGroup
		for ti := 0; ti < *t; ti++ {
			endKey := int64(ti+1) * tsize
			if ti == *t-1 {
				endKey = *n
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

					var value []byte
					if *valueFlag == "fnv" {
						value = generateRandomData(int(valueSize), uint64(keys[i]))
					} else if *valueFlag == "simple" {
						value = make([]byte, valueSize)
						for j := 0; j < len(value); j++ {
							value[j] = byte(int(keys[i]) + j)
						}
					} else {
						panic("unknown value generator")
					}

					dbs[keys[i]%int64(*dbn)].Put(key, value)
					if *v == 4 {
						fmt.Printf("thread: %d, write %d\n", ti, keys[i])
					} else if *v == 5 {
						fmt.Printf("thread: %d, write %s:%s\n", ti, hex.EncodeToString(key), hex.EncodeToString(value))
					}
					if *r != 0 && int64(i)%*r == 0 {
						fmt.Printf("thread: %d, task: %d\n", ti, i)
					}
				}
			}(ti, keys[int64(ti)*tsize:endKey])
		}
		wg.Wait()
	} else if *op == "read" || *op == "randread" {
		tsize := *n / int64(*t)

		keys := generateKeys()

		startTime = time.Now()
		var wg sync.WaitGroup
		for ti := 0; ti < *t; ti++ {
			endKey := int64(ti+1) * tsize
			if ti == *t-1 {
				endKey = *n
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

					value, err := dbs[keys[i]%int64(*dbn)].Get(key)
					if err != nil || len(value) != int(valueSize) {
						panic("data verification failed")
					}
					if *v == 4 {
						fmt.Printf("thread: %d, read %d\n", ti, keys[i])
					} else if *v == 5 {
						fmt.Printf("thread: %d, read %s:%s\n", ti, hex.EncodeToString(key), hex.EncodeToString(value))
					}
					if *r != 0 && int64(i)%*r == 0 {
						fmt.Printf("thread: %d, task: %d\n", ti, i)
					}
				}
			}(ti, keys[int64(ti)*tsize:endKey])
		}
		wg.Wait()
	} else {
		panic("Unknown operation")
	}

	elapsed := time.Since(startTime)
	fmt.Printf("used time %f, ops %f\n", elapsed.Seconds(), float64(*n)/elapsed.Seconds())
}
