; fib.ll
define void @fib(i32 %n, i256* %out) {
entry:
  %cmp1 = icmp sle i32 %n, 1
  br i1 %cmp1, label %base, label %loop

base:
  %n64 = zext i32 %n to i256
  store i256 %n64, i256* %out
  ret void

loop:
  %a = alloca i256
  %b = alloca i256
  %i = alloca i32
  store i256 1, i256* %a
  store i256 1, i256* %b
  store i32 2, i32* %i
  br label %cond

cond:
  %iv = load i32, i32* %i
  %cmp = icmp sle i32 %iv, %n
  br i1 %cmp, label %body, label %done

body:
  %aval = load i256, i256* %a
  %bval = load i256, i256* %b
  %sum = add i256 %aval, %bval
  store i256 %bval, i256* %a
  store i256 %sum, i256* %b
  %inext = add i32 %iv, 1
  store i32 %inext, i32* %i
  br label %cond

done:
  %res = load i256, i256* %b
  store i256 %res, i256* %out
  ret void
}
