.PHONY: all build run

# llvm17 is perfered
all:  build run

build:
	llc -filetype=obj -O3 fib.ll -o fib.o
	go build -o main

run:
	./main