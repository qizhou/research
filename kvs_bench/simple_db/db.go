package simple_db

import (
	"bufio"
	"encoding/binary"
	"errors"
	"io"
	"os"
	"sync"
)

type valueEntry struct {
	entryOff  int64
	valueSize int
}

type Database struct {
	kvEntries map[string]valueEntry
	f         *os.File
	filesize  int64
	lock      sync.Mutex
	appendBuf []byte
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

	filesize := stat.Size()
	off := int64(0)
	reader := bufio.NewReader(f)
	kvEntries := make(map[string]valueEntry)
	for off < filesize {
		data := make([]byte, 8)
		// TODO: check error
		io.ReadFull(reader, data)
		totalSize := binary.BigEndian.Uint32(data)
		keySize := binary.BigEndian.Uint32(data[4:])
		valueSize := totalSize - keySize
		key := make([]byte, keySize)
		value := make([]byte, valueSize)
		io.ReadFull(reader, key)
		io.ReadFull(reader, value)
		kvEntries[string(key)] = valueEntry{
			entryOff:  off,
			valueSize: int(valueSize),
		}
		off += 8 + int64(len(key)+len(value))
	}

	return &Database{
		kvEntries: kvEntries,
		f:         f,
		filesize:  filesize,
		lock:      sync.Mutex{},
	}, nil
}

func (db *Database) Get(key []byte) ([]byte, error) {
	db.lock.Lock()
	v, ok := db.kvEntries[string(key)]
	if !ok {
		db.lock.Unlock()
		return nil, errors.New("not found")
	}

	value := make([]byte, v.valueSize)
	actualFileSize := db.filesize - int64(len(db.appendBuf))
	if v.entryOff >= actualFileSize {
		copy(value, db.appendBuf[v.entryOff+8+int64(len(key))-actualFileSize:])
		db.lock.Unlock()
	} else {
		// early unlock as reading the file is threadsafe
		db.lock.Unlock()
		n, err := db.f.ReadAt(value, v.entryOff+8+int64(len(key)))
		if err != nil {
			return nil, err
		}
		if n != v.valueSize {
			return nil, errors.New("full read failed")
		}
	}
	return value, nil
}

func (db *Database) Put(key []byte, value []byte) error {
	data := make([]byte, 8)
	binary.BigEndian.PutUint32(data, uint32(len(key)+len(value)))
	binary.BigEndian.PutUint32(data[4:], uint32(len(key)))
	s := string(key)

	db.lock.Lock()
	defer db.lock.Unlock()
	db.appendBuf = append(db.appendBuf, data...)
	db.appendBuf = append(db.appendBuf, key...)
	db.appendBuf = append(db.appendBuf, value...)
	off := db.filesize
	db.filesize += int64(8 + len(key) + len(value))

	if len(db.appendBuf) > 256*1024 {
		n, err := db.f.WriteAt(db.appendBuf, db.filesize-int64(len(db.appendBuf)))
		if err != nil {
			return err
		}

		if n != len(db.appendBuf) {
			return errors.New("failed to write")
		}
		db.appendBuf = make([]byte, 0)
	}
	db.kvEntries[s] = valueEntry{entryOff: off, valueSize: len(value)}

	return nil
}

func (db *Database) Delete(key []byte) error {
	return errors.ErrUnsupported
}

func (db *Database) Has(key []byte) (bool, error) {
	db.lock.Lock()
	defer db.lock.Unlock()
	_, ok := db.kvEntries[string(key)]
	return ok, nil
}

func (db *Database) Close() error {
	// TODO: error & threadsafe
	db.f.WriteAt(db.appendBuf, db.filesize-int64(len(db.appendBuf)))
	return db.f.Close()
}
