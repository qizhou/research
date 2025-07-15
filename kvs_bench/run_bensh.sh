#!/bin/bash

set -x

for db in goleveldb pebble; do
  rm -r bench_*; go run main.go -r 0 -t 1 -op randwrite -n 10000000 -S 100 --dbn 1 --db $db
  for t in 1 2 4 8 16 32; do
    go run main.go -r 0 -t $t -op randread -n 1000000 -S 100 --dbn 1 --db $db
  done
done
