# a simple demo for matmul in pytorch
# - unlike matlab, 1D vector of size n is not 2D matrix of size (n, 1) or (1,n)
# - for 1D lhs, then 1-dim is preprended so that it becomes (1, n) and removed after.
# - for 1D rhs, then 1-dim is appended so that it becomes (n, 1) and removed after.
# - 1Dx1D is a special case
import torch

def expectError(fn, error):
    try:
        fn()
    except error:
        return # expected
    else:
        raise Exception("error not raised")

# 1D vector
a = torch.randn(4) # 4
b = torch.randn(4) # 4
print(a @ b) # sum a_i * b_i

b = torch.randn((1, 4)) # 1x4
expectError(lambda: a @ b, RuntimeError) # mat1 and mat2 shapes cannot be multiplied (1x4 and 1x4)

# 2D * 2D
a = torch.randn((4, 2))
b = torch.randn((2, 8))
print(a @ b) # 2x8

# Unlike matlab, 1D size (n) != 2D size (n,1)
a = torch.randn((4, 1)) # 4x1
b = torch.randn((4, 1)) # 4x1
expectError(lambda: a @ b, RuntimeError) # mat1 and mat2 shapes cannot be multiplied (4x1 and 4x1)
print(a.transpose(0, 1) @ b) # inner product
print(a.transpose(0, 1) @ b == a.view((4,)) @ b.view((4,)))
print(a @ b.transpose(0, 1)) # outer product

# 1D * 2D
a = torch.randn(4) # 4
b = torch.randn((4, 2)) # 4x2
print(a @ b) # vector size (2)
print((a.view(1,4) @ b).view((2,))) # preprend a as 1x4, then multiple b as 1x2 and then convert to vector 2

b = torch.randn((4, 8)) # 4x8
print(a @ b) # vector size (8)
print((a.view(1,4) @ b).view((8,))) # preprend a as 1x4, then multiple b as 1x8 and then convert to vector 8

# 2D * 1D
a = torch.randn((4,2))
b = torch.randn(2)
print(a @ b)
print((a @ b.view((2, 1))).view((4,))) # append b as 4x1, then multiple a (lhs) as 4x1 and then remove last dim to vector 4

# batch multiplication (only last two dims are matrix-multiplied)
# note that with broadcast rule https://numpy.org/doc/stable/user/basics.broadcasting.html,
# a dim of size 1 will be automatically broadcasted (expanded) to match another dim size
a = torch.randn((4,1,3,2))
b = torch.randn((6,2,5))
r = a @ b # 4 * 6 batch of (3,2) * (2,5) matrices as (4, 6, 3, 5)
print(torch.allclose(r[2,3,:,:], a[2,0,:,:] @ b[3,:,:]))

a = torch.randn((4,7,1,1,3,2))
b = torch.randn((6,8,2,5))
r = a @ b # 4 * 7 * 6 * 8 batch of (3,2) * (2,5) matrices as (4, 7, 6, 8 3, 5)
print(torch.allclose(r[2,3,1,4,:,:], a[2,3,0,0,:,:] @ b[1,4,:,:])) 

a = torch.randn((4,6,3,2))
b = torch.randn((6,2,5))
r = a @ b # 4 * 6 batch of (3,2) * (2,5) matrices as (4, 6, 3, 5)
print(torch.allclose(r[2,3,:,:], a[2,3,:,:] @ b[3,:,:]))


