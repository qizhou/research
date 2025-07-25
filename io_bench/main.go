package main

import (
	"encoding/binary"
	"encoding/hex"
	"flag"
	"fmt"
	"log"
	"math/rand/v2"
	"os"
	"runtime/pprof"
	"sync"
	"time"
)

var n = flag.Int64("n", 16*1024*1024*1024, "total filesize")

var op = flag.String("op", "write", "operation: write, read, randread")
var r = flag.Int64("r", 100000, "report interval")
var ioSize = flag.Int64("s", 4*1024, "IO size")
var t = flag.Int("t", 8, "threads")
var v = flag.Int("v", 3, "verbosity")
var fn = flag.Int("fn", 1, "number of files")
var cpuprofile = flag.String("cpuprofile", "", "write cpu profile to file")

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

func generateOffs() []int64 {
	N := *n / *ioSize
	offs := make([]int64, N)
	for i := int64(0); i < N; i++ {
		offs[i] = i
	}

	if *op == "randwrite" || *op == "randread" {
		rand.Shuffle(len(offs), func(i, j int) { offs[i], offs[j] = offs[j], offs[i] })
	}
	return offs
}

func main() {
	flag.Parse()

	if *cpuprofile != "" {
		f, err := os.Create(*cpuprofile)
		if err != nil {
			log.Fatal(err)
		}
		pprof.StartCPUProfile(f)
		defer pprof.StopCPUProfile()
	}

	fs := make([]*os.File, *fn)
	for i := 0; i < *fn; i++ {
		var err error

		fs[i], err = os.OpenFile(fmt.Sprintf("bench_file_%d", i), os.O_CREATE|os.O_RDWR, 666)

		if err != nil {
			panic(err)
		}
		defer fs[i].Close()
	}

	var startTime time.Time

	if *op == "write" {
		offs := generateOffs()
		tsize := len(offs) / *t

		startTime = time.Now()
		var wg sync.WaitGroup
		for ti := 0; ti < *t; ti++ {
			endOff := (ti + 1) * tsize
			if ti == *t-1 {
				endOff = len(offs)
			}

			wg.Add(1)
			go func(ti int, offs []int64) {
				defer wg.Done()
				for i := 0; i < len(offs); i++ {
					var value []byte
					value = generateRandomData(int(*ioSize), uint64(offs[i]))

					fi := offs[i] % int64(*fn)
					foff := offs[i] / int64(*fn) * *ioSize
					n, err := fs[fi].WriteAt(value, foff)
					if err != nil {
						panic(err)
					}
					if n != len(value) {
						panic("not full write")
					}

					if *v == 4 {
						fmt.Printf("thread: %d, write %d\n", ti, offs[i])
					} else if *v == 5 {
						fmt.Printf("thread: %d, write %d:%s\n", ti, offs[i], hex.EncodeToString(value))
					}
					if *r != 0 && int64(i)%*r == 0 {
						fmt.Printf("thread: %d, task: %d\n", ti, i)
					}
				}
			}(ti, offs[ti*tsize:endOff])
		}
		wg.Wait()
	} else if *op == "read" || *op == "randread" {
		offs := generateOffs()
		tsize := len(offs) / *t

		startTime = time.Now()
		var wg sync.WaitGroup
		for ti := 0; ti < *t; ti++ {
			endOff := (ti + 1) * tsize
			if ti == *t-1 {
				endOff = len(offs)
			}

			wg.Add(1)
			go func(ti int, offs []int64) {
				defer wg.Done()
				for i := 0; i < len(offs); i++ {
					fi := offs[i] % int64(*fn)
					foff := offs[i] / int64(*fn) * *ioSize

					value := make([]byte, *ioSize)

					n, err := fs[fi].ReadAt(value, foff)
					if err != nil {
						panic(err)
					}
					if n != len(value) {
						panic("not full read")
					}

					if *v == 4 {
						fmt.Printf("thread: %d, read %d,%d\n", ti, foff, *ioSize)
					} else if *v == 5 {
						fmt.Printf("thread: %d, read %d:%s\n", ti, foff, hex.EncodeToString(value))
					}
					if *r != 0 && int64(i)%*r == 0 {
						fmt.Printf("thread: %d, task: %d\n", ti, i)
					}
				}
			}(ti, offs[ti*tsize:endOff])
		}
		wg.Wait()
	} else {
		panic("Unknown operation")
	}

	elapsed := time.Since(startTime)
	fmt.Printf("used time %f, ops %f\n", elapsed.Seconds(), float64((*n)/(*ioSize))/elapsed.Seconds())
}
