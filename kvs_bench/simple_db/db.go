package simple_db

import (
	"encoding/binary"
	"errors"
	"os"
	"sync"
)

type valueEntry struct {
	off  int64
	size int
}

type Database struct {
	kvEntry  map[string]valueEntry
	f        *os.File
	filesize int64
	lock     sync.Mutex
}

func NewDatabase(path string) (*Database, error) {
	f, err := os.OpenFile(path, os.O_CREATE|os.O_RDWR, 0666)
	if err != nil {
		return nil, err
	}

	stat, err := f.Stat()
	if err != nil {
		return nil, err
	}

	// TODO: initialize kvEntry
	return &Database{
		kvEntry:  make(map[string]valueEntry),
		f:        f,
		filesize: stat.Size(),
		lock:     sync.Mutex{},
	}, nil
}

func (db *Database) Get(key []byte) ([]byte, error) {
	s := string(key)
	db.lock.Lock()
	defer db.lock.Unlock()
	v, ok := db.kvEntry[s]
	if !ok {
		return nil, errors.New("not found")
	}

	// early unlock as reading the file is threadsafe
	db.lock.Unlock()
	value := make([]byte, v.size)
	n, err := db.f.ReadAt(value, v.off+8+int64(len(key)))
	if err != nil {
		return nil, err
	}
	if n != v.size {
		return nil, errors.New("full read failed")
	}
	return value, nil
}

func (db *Database) Put(key []byte, value []byte) error {
	data := make([]byte, 8+len(key)+len(value))
	binary.BigEndian.PutUint32(data, uint32(len(key)+len(value)))
	binary.BigEndian.PutUint32(data[4:], uint32(len(key)))
	copy(data[8:], key)
	copy(data[8+len(key):], value)
	s := string(key)

	db.lock.Lock()
	defer db.lock.Unlock()
	off := db.filesize
	db.filesize += int64(len(data))
	n, err := db.f.WriteAt(data, off)
	if err != nil {
		return err
	}

	if n != len(data) {
		return errors.New("failed to write")
	}
	db.kvEntry[s] = valueEntry{off: off, size: len(value)}
	return nil
}

func (db *Database) Delete(key []byte) error {
	return errors.ErrUnsupported
}

func (db *Database) Has(key []byte) (bool, error) {
	db.lock.Lock()
	defer db.lock.Unlock()
	_, ok := db.kvEntry[string(key)]
	return ok, nil
}

func (db *Database) Close() error {
	return db.f.Close()
}
