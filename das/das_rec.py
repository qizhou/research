import random

# numbers of rows and cols of encoded matrix (1/2 RS)
N_ROWS = 512
N_COLS = 512

# encoded matrix, False means non-withheld and correct, True means withheld or corrupted
matrix = [[False] * N_COLS for r in range(N_ROWS)]
row_samples = [N_COLS] * N_ROWS
col_samples = [N_ROWS] * N_COLS

# number of corrupted samples
N_CORRUPTED = N_ROWS * N_COLS // 100 * 55
# N_CORRUPTED = 48
n_available = N_ROWS * N_COLS - N_CORRUPTED

# corrupt the samples with EXACT number
for i in range(N_CORRUPTED):
    while True:
        r = random.randint(0, N_ROWS - 1)
        c = random.randint(0, N_COLS - 1)
        if not matrix[r][c]:
            matrix[r][c] = True
            row_samples[r] -= 1
            col_samples[c] -= 1
            break


tik = 0
while n_available != N_ROWS * N_COLS:
    print("Tik: {}, available samples: {}".format(tik, n_available))
    tik += 1
    n_rec_total = 0
    # reconstruct row by row
    for r in range(N_ROWS):      
        if row_samples[r] == N_COLS:
            # nothing to reconstruct
            continue
        if row_samples[r] < N_COLS // 2:
            # insufficient samples to reconstruct
            continue
        # reconstruct and re-distribute the samples
        n_rec = 0
        for c in range(N_COLS):
            if matrix[r][c]:
                matrix[r][c] = False
                n_rec += 1
                col_samples[c] += 1
        assert n_rec == N_COLS - row_samples[r]
        row_samples[r] = N_COLS
        n_rec_total += n_rec
    
    # reconstruct col by col
    for c in range(N_COLS):
        if col_samples[c] == N_ROWS:
            # nothing to reconstruct
            continue
        if col_samples[c] < N_ROWS // 2:
            # insufficient samples to reconstruct
            continue
        # reconstruct and re-distribute the samples 
        n_rec = 0
        for r in range(N_ROWS):
            if matrix[r][c]:
                matrix[r][c] = False
                n_rec += 1
                row_samples[r] += 1
        assert n_rec == N_ROWS - col_samples[c]
        col_samples[c] = N_ROWS
        n_rec_total += n_rec

    n_available += n_rec_total
    print("Tik: {}, reconstructed samples: {}".format(tik, n_rec_total))
    if n_rec_total == 0:
        break

if n_available == N_ROWS * N_COLS:
    print("All samples reconstructed, took {} tiks".format(tik))
else:
    print("Reconstruction failed, remaining samples {}, took {} tiks".format(N_ROWS * N_COLS - n_available, tik))
        


