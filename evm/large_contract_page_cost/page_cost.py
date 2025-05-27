import time

JUMP = 0x56
JUMPDEST = 0x5B
PUSH0 = 0x5F
PUSH3 = 0x62 # maximum offset = 16M - 1
PUSH4 = 0x63
RET = 0xF3


def create_page_code(page_num, is_first=False, is_last=False, size=4096):
    data = bytearray()
    idx = 0
    while len(data) + 6 <= size:
        if is_first and idx == 0:
            data.append(PUSH4)
            jump_addr = (page_num + 1) * size + 6 * idx
            data.extend(jump_addr.to_bytes(4, byteorder='big'))
            data.append(JUMP)
        elif is_last and len(data) + 6 + 6 > size:
            data.append(JUMPDEST)
            data.append(PUSH0)
            data.append(PUSH0)
            data.append(RET)
        else:
            data.append(JUMPDEST)
            data.append(PUSH3)
            if is_last:
                jump_addr = 6 * (idx + 1)
            else:
                jump_addr = (page_num + 1) * size + 6 * idx
            data.extend(jump_addr.to_bytes(3, byteorder='big'))
            data.append(JUMP)
        idx += 1
    for _ in range(size - len(data)):
        data.append(0) 
    return bytes(data)


def create_code(num_pages, size=4096):
    assert num_pages >= 2 # at least two pages
    pages = [create_page_code(i, is_first=(i == 0), is_last=(i == num_pages - 1), size=size) for i in range(num_pages)]
    return b''.join(pages)
    

def execute(code, print_jump=False):
    pc = 0
    stack = []
    num_jumps = 0
    while True:
        op = int(code[pc])
        if op == RET:
            break
        if op == JUMP:
            if len(stack) == 0:
                raise RuntimeError("no stack var to jump")
            pc = stack.pop()
            num_jumps += 1
            if print_jump:
                print(pc)
            # simple jumpdest analysis
            if int(code[pc]) != JUMPDEST:
                raise RuntimeError("invalid jump dest")
        elif op == PUSH0:
            stack.append(0)
        elif op == PUSH3:
            stack.append(int.from_bytes(code[pc+1:pc+4], byteorder='big'))
            pc += 3
        elif op == PUSH4:
            stack.append(int.from_bytes(code[pc+1:pc+5], byteorder='big'))
            pc += 4
        pc += 1
    return {'num_jumps': num_jumps}


def write_code():
    with open("code_24KB", "wb") as f:
        f.write(create_code(6, 4096))

    with open("code_256KB", "wb") as f:
        f.write(create_code(64, 4096))


code = create_code(2, 14)
print(code.hex())
execute(code, print_jump=True)
        
code = create_code(3, 4096)
print(execute(code))

# write_code()

print("24KB")
code = create_code(6, 4096)
start = time.monotonic()
for _ in range(6400):
    execute(code)
print("used time", time.monotonic() - start)

print("256KB")
code = create_code(64, 4096)
start = time.monotonic()
for _ in range(600):
    execute(code)
print("used time", time.monotonic() - start)