import random
import matplotlib.pyplot as plt
import seaborn as sns
import time


# seed = time.time_ns()
seed = 1662426016441515000 # for 128x128 with 60% corrupted
random.seed(seed)
print("seed {}".format(seed))
show_plot = False

# numbers of rows and cols of encoded matrix (1/2 RS)
N_ROWS = 128
N_COLS = 128

SAMPLE_MISSING = 0
SAMPLE_RECEIVED = 1
SAMPLE_RECOVERED = 2

# encoded matrix, False means non-withheld and correct, True means withheld or corrupted
matrix = [[SAMPLE_RECEIVED] * N_COLS for r in range(N_ROWS)]
row_samples = [N_COLS] * N_ROWS
col_samples = [N_ROWS] * N_COLS

# number of corrupted samples
N_CORRUPTED = N_ROWS * N_COLS // 100 * 60
# N_CORRUPTED = 48
n_available = N_ROWS * N_COLS - N_CORRUPTED

# corrupt/withhold the samples with EXACT number
for i in range(N_CORRUPTED):
    while True:
        r = random.randint(0, N_ROWS - 1)
        c = random.randint(0, N_COLS - 1)
        if matrix[r][c] != SAMPLE_MISSING:
            matrix[r][c] = SAMPLE_MISSING
            row_samples[r] -= 1
            col_samples[c] -= 1
            break


tik = 0
if show_plot:
    sns.heatmap(matrix, vmin=SAMPLE_MISSING, vmax=SAMPLE_RECOVERED, linewidth=0.5, cbar=False)
    plt.pause(10)
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
            if matrix[r][c] == SAMPLE_MISSING:
                matrix[r][c] = SAMPLE_RECOVERED
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
            if matrix[r][c] == SAMPLE_MISSING:
                matrix[r][c] = SAMPLE_RECOVERED
                n_rec += 1
                row_samples[r] += 1
        assert n_rec == N_ROWS - col_samples[c]
        col_samples[c] = N_ROWS
        n_rec_total += n_rec

    n_available += n_rec_total
    print("Tik: {}, reconstructed samples: {}".format(tik, n_rec_total))
    if show_plot:
        ax = sns.heatmap(matrix, vmin=SAMPLE_MISSING, vmax=SAMPLE_RECOVERED, linewidth=0.5, cbar=False)
        plt.pause(0.2)
    if n_rec_total == 0:
        break

if n_available == N_ROWS * N_COLS:
    print("All samples reconstructed, took {} tiks".format(tik))
else:
    print("Reconstruction failed, remaining samples {}, took {} tiks".format(N_ROWS * N_COLS - n_available, tik))
        
if show_plot:
    plt.show()

