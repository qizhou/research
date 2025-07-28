#!/bin/bash

set -x

go run main.go -t 32 -op write -n 274877906944 -r 0
for t in 8 16 32 64; do
  go run main.go -t $t -op randread -n 274877906944 -r 0
done