import torch
# a simple SGD example with

n = 1000 # training samples
n_i = 5 # number of inputs

w = torch.randn(n_i) # true weight
x = torch.randn(n_i, n)
t = w @ x + torch.randn(n) # add error

# iterative update
w_p = torch.randn(n_i) # inital guess
eta = 0.1
sample_indices = torch.randint(0, n, (n * 10,))
for i in range(n * 10):
    i_s = sample_indices[i]
    o = w_p @ x[:, i_s]
    w_p = w_p + eta * (t[i_s] - o) * x[:, i_s]
    eta = eta * 0.999
    if i % 100 == 0:
        print("err = ", sum((w - w_p) ** 2))