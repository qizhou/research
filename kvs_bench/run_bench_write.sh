#!/bin/bash

set -x

# performance of randwrite
for db in goleveldb pebble; do
  for t in 1 2 4 8 16 32 64; do
    rm -r bench_*; go run main.go -r 0 -t $t -op randwrite -n 1000000 -S 100 --dbn 1 --db $db
  done
done
