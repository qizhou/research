
export CGO_CXXFLAGS="$(llvm-config --cxxflags)"
export CGO_LDFLAGS="$(llvm-config --ldflags --libs --system-libs)"
export CGO_CPPFLAGS="$(llvm-config --cppflags)"
export CGO_CFLAGS="$(llvm-config --cflags)"