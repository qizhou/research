package pebble_v2

import (
	"fmt"
	"runtime"

	"github.com/cockroachdb/pebble"
	pebblev2 "github.com/cockroachdb/pebble/v2"
	"github.com/cockroachdb/pebble/v2/bloom"
	"github.com/ethereum/go-ethereum/ethdb"
)

type PebbleV2 struct {
	db           *pebblev2.DB // Underlying pebble storage engine
	writeOptions *pebblev2.WriteOptions
}

func New(file string, cache int, handles int) (*PebbleV2, error) {
	maxMemTableSize := (1<<31)<<(^uint(0)>>63) - 1
	memTableLimit := 4
	memTableSize := cache * 1024 * 1024 / 2 / memTableLimit
	if memTableSize >= maxMemTableSize {
		memTableSize = maxMemTableSize - 1
	}

	opt := &pebblev2.Options{
		// Pebble has a single combined cache area and the write
		// buffers are taken from this too. Assign all available
		// memory allowance for cache.
		Cache:        pebblev2.NewCache(int64(cache * 1024 * 1024)),
		MaxOpenFiles: handles,

		// The size of memory table(as well as the write buffer).
		// Note, there may have more than two memory tables in the system.
		MemTableSize: uint64(memTableSize),

		// MemTableStopWritesThreshold places a hard limit on the size
		// of the existent MemTables(including the frozen one).
		// Note, this must be the number of tables not the size of all memtables
		// according to https://github.com/cockroachdb/pebble/blob/master/options.go#L738-L742
		// and to https://github.com/cockroachdb/pebble/blob/master/db.go#L1892-L1903.
		MemTableStopWritesThreshold: memTableLimit,

		// The default compaction concurrency(1 thread),
		// Here use all available CPUs for faster compaction.
		MaxConcurrentCompactions: runtime.NumCPU,

		// Per-level options. Options for at least one level must be specified. The
		// options for the last level are used for all subsequent levels.
		Levels: []pebblev2.LevelOptions{
			{TargetFileSize: 2 * 1024 * 1024, FilterPolicy: bloom.FilterPolicy(10)},
			{TargetFileSize: 4 * 1024 * 1024, FilterPolicy: bloom.FilterPolicy(10)},
			{TargetFileSize: 8 * 1024 * 1024, FilterPolicy: bloom.FilterPolicy(10)},
			{TargetFileSize: 16 * 1024 * 1024, FilterPolicy: bloom.FilterPolicy(10)},
			{TargetFileSize: 32 * 1024 * 1024, FilterPolicy: bloom.FilterPolicy(10)},
			{TargetFileSize: 64 * 1024 * 1024, FilterPolicy: bloom.FilterPolicy(10)},
			{TargetFileSize: 128 * 1024 * 1024, FilterPolicy: bloom.FilterPolicy(10)},
		},
		ReadOnly: false,

		// Pebble is configured to use asynchronous write mode, meaning write operations
		// return as soon as the data is cached in memory, without waiting for the WAL
		// to be written. This mode offers better write performance but risks losing
		// recent writes if the application crashes or a power failure/system crash occurs.
		//
		// By setting the WALBytesPerSync, the cached WAL writes will be periodically
		// flushed at the background if the accumulated size exceeds this threshold.
		WALBytesPerSync: 5 * ethdb.IdealBatchSize,

		// L0CompactionThreshold specifies the number of L0 read-amplification
		// necessary to trigger an L0 compaction. It essentially refers to the
		// number of sub-levels at the L0. For each sub-level, it contains several
		// L0 files which are non-overlapping with each other, typically produced
		// by a single memory-table flush.
		//
		// The default value in Pebble is 4, which is a bit too large to have
		// the compaction debt as around 10GB. By reducing it to 2, the compaction
		// debt will be less than 1GB, but with more frequent compactions scheduled.
		L0CompactionThreshold: 2,
	}

	db, err := pebblev2.Open(file, opt)
	if err != nil {
		return nil, err
	}
	return &PebbleV2{
		db:           db,
		writeOptions: pebblev2.NoSync,
	}, nil
}

// Has retrieves if a key is present in the key-value store.
func (d *PebbleV2) Has(key []byte) (bool, error) {
	_, closer, err := d.db.Get(key)
	if err == pebble.ErrNotFound {
		return false, nil
	} else if err != nil {
		return false, err
	}
	if err = closer.Close(); err != nil {
		return false, err
	}
	return true, nil
}

// Get retrieves the given key if it's present in the key-value store.
func (d *PebbleV2) Get(key []byte) ([]byte, error) {
	dat, closer, err := d.db.Get(key)
	if err != nil {
		return nil, err
	}
	ret := make([]byte, len(dat))
	copy(ret, dat)
	if err = closer.Close(); err != nil {
		return nil, err
	}
	return ret, nil
}

// Put inserts the given value into the key-value store.
func (d *PebbleV2) Put(key []byte, value []byte) error {
	return d.db.Set(key, value, d.writeOptions)
}

// Delete removes the key from the key-value store.
func (d *PebbleV2) Delete(key []byte) error {
	return d.db.Delete(key, d.writeOptions)
}

// Close stops the metrics collection, flushes any pending data to disk and closes
// all io accesses to the underlying key-value store.
func (d *PebbleV2) Close() error {
	return d.db.Close()
}

func (d *PebbleV2) MetricsString() string {
	m := d.db.Metrics()
	s := m.String()
	s += fmt.Sprintf("Block cache: hits %d, misses %d\n", m.BlockCache.Hits, m.BlockCache.Misses)
	return s
}
