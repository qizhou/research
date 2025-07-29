
export CGO_CXXFLAGS="$(llvm-config --cxxflags)"
export CGO_LDFLAGS="$(llvm-config --ldflags --libs --system-libs)" 