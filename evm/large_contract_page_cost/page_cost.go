package main

import (
	"errors"
	"flag"
	"fmt"
	"math/big"
	"os"
	"time"
)

const (
	JUMP     = byte(0x56)
	JUMPDEST = byte(0x5B)
	PUSH0    = byte(0x5F)
	PUSH3    = byte(0x62)
	PUSH4    = byte(0x63)
	RET      = byte(0xF3)
)

func execute(code []byte) (int, error) {
	pc := 0
	stack := make([]int, 0)
	jumps := 0
	for {
		op := code[pc]
		if op == RET {
			return jumps, nil
		}
		if op == JUMP {
			if len(stack) == 0 {
				return jumps, errors.New("no stack var to jump")
			}
			pc = stack[len(stack)-1]
			jumps += 1
			stack = stack[:len(stack)-1]
			// simple jumpdest analysis
			if code[pc] != JUMPDEST {
				return jumps, errors.New("invalid jump dest")
			}
		} else if op == PUSH0 {
			stack = append(stack, 0)
		} else if op == PUSH3 {
			stack = append(stack, int(big.NewInt(0).SetBytes(code[pc+1:pc+4]).Uint64()))
			pc += 3
		} else if op == PUSH4 {
			stack = append(stack, int(big.NewInt(0).SetBytes(code[pc+1:pc+5]).Uint64()))
			pc += 4
		}
		pc += 1
	}
}

func main() {
	codeFile := flag.String("code", "", "path to code")
	numPtr := flag.Int("num", 1, "repeat calls")
	flag.Parse()

	f, err := os.Open(*codeFile)
	if err != nil {
		panic(err)
	}
	stat, err := f.Stat()
	if err != nil {
		panic(err)
	}
	code := make([]byte, stat.Size())
	n, err := f.Read(code)
	if err != nil {
		panic(err)
	}
	if n != len(code) {
		panic(errors.New("cannot read full"))
	}

	fmt.Printf("Read code with %d bytes\n", len(code))

	t := time.Now()
	total_jumps := 0
	for i := 0; i < *numPtr; i++ {
		jumps, err := execute(code)
		if err != nil {
			panic(err)
		}
		total_jumps += jumps
	}
	fmt.Println((time.Now().Sub(t).Seconds()))
	fmt.Printf("jumps %d\n", total_jumps)
}
