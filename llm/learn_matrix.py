import torch
import torch.nn as nn

n_in = 4
n_out = 2
n = 10000
n_train = 8000
n_batch = 8
max_iters = 10000
eval_interval = 100
eval_iters = 200

A = torch.randn((n_in, n_out))
inputs = torch.randn((n, n_in))
outputs = inputs @ A + torch.randn((n, n_out))
train_in = inputs[:n_train, :]
train_out = outputs[:n_train, :]
val_in = inputs[n_train:,:]
val_out = outputs[n_train:,:]


def get_batch(split):
    inp = train_in if split == 'train' else val_in
    out = train_out if split == 'train' else val_out
    ix = torch.randint(inp.shape[0], (n_batch,))
    x = torch.stack([inp[i,:] for i in ix])
    y = torch.stack([out[i,:] for i in ix])
    return x, y

class LearnMatrix(nn.Module):

    def __init__(self):
        super().__init__()
        self.model = nn.Linear(n_in, n_out, bias=False)
        self.loss = nn.MSELoss()

    def forward(self, idx, targets=None):
        if targets is None:
            return None
        else:
            y = self.model(idx)
            return y, self.loss(y, targets)
        
@torch.no_grad()
def estimate_loss():
    out = {}
    lm.eval()
    for split in ['train', 'val']:
        losses = torch.zeros(eval_iters)
        for k in range(eval_iters):
            X, Y = get_batch(split)
            _, loss = lm(X, Y)
            losses[k] = loss.item()
        out[split] = losses.mean()
    lm.train()
    return out


x, y = get_batch('train')
lm = LearnMatrix()
e_y, loss = lm(x, y)
print(loss)

# create a PyTorch optimizer
optimizer = torch.optim.AdamW(lm.parameters(), lr=1e-3)

for iter in range(max_iters):

    # every once in a while evaluate the loss on train and val sets
    if iter % eval_interval == 0 or iter == max_iters - 1:
        losses = estimate_loss()
        with torch.no_grad():
            model_err = sum(sum((lm.model.weight.transpose(0, 1) - A) ** 2))
        print(f"step {iter}: train loss {losses['train']:.4f}, val loss {losses['val']:.4f}, model err {model_err:.4f}")

    # sample a batch of data
    xb, yb = get_batch('train')

    # evaluate the loss
    logits, loss = lm(xb, yb)
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    optimizer.step()
