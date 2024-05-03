import torch
# a simple SGD example with

n = 1000 # training samples
n_i = 5 # number of inputs

w = torch.randn(n_i) # true weight
x = torch.randn(n_i, n)

def forward_fn(w, x):
    return w @ x

def backward_fn(t, w, x):
    return (t - forward_fn(w, x)) * x

def forward_fn(w, x):
    return torch.sigmoid(w @ x)

def backward_fn(t, w, x):
    o = forward_fn(w, x)
    return (t - o) * o * (1 - o) * x

t = forward_fn(w, x) + 0.1 * torch.randn(n) # add error

# iterative update
w_p = torch.randn(n_i) # inital guess
eta = 0.1
sample_indices = torch.randint(0, n, (n * 10,))
for i in range(n * 10):
    i_s = sample_indices[i]
    w_p = w_p + eta * backward_fn(t[i_s], w_p, x[:, i_s])
    eta = eta * 0.999
    if i % 100 == 0:
        print("err = ", sum((w - w_p) ** 2))