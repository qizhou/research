# https://asecuritysite.com/encryption/wint

import hashlib

from os import urandom

import sys
message="Hello"

def sha256(message):
    return hashlib.sha256(message).digest()

def merkle(hash_list):
    if (len(hash_list) - 1) & len(hash_list) != 0:
        raise RuntimeError("hash list must be 2^n")
    while len(hash_list) != 1:
        hash_list = [sha256(hash_list[i] + hash_list[i + 1]) for i in range(0, 2, len(hash_list))]
    return hash_list[0]

def random_wkey(w=16, verbose=0):      #create random W-OTS keypair

    priv = []
    pub = []
    print("Hashing number random keys by:\t",2**w)
    for x in range(256//w):
        a = urandom(w)
        priv.append(a)
        for y in range(2**w-1):              
            a = sha256(a)
        pub.append(sha256(a))               

    return priv, pub 

def sign_wkey(priv, message):      

    signature = []
    bin_msg = sha256(message)

    l = 256 // len(priv) // 8
    for y in range(len(priv)):
        s = priv[y]
        v = int.from_bytes(bin_msg[l*y:y*l+l], 'big')
        for x in range(256**l-v):
            s = sha256(s)
        signature.append(s)
    return signature

def verify_wkey(signature, message, pub):

    verify = []
    bin_msg = sha256(message)

    l = 256 // len(priv) // 8
    
    for x in range(len(signature)):
        a = signature[x]
        v = int.from_bytes(bin_msg[l*x:l*x+l], 'big')
        for z in range(v):
            a=sha256(a)
        verify.append(a)
  
    if pub != merkle(verify):
        return False

    return True


priv, pub = random_wkey()

print("==== Private key (keep secret) =====")
print("Priv[0]: ",priv[0])
print("Priv[1]: ",priv[1])
print("Priv[2]: ",priv[2])
print("Priv[3]: ",priv[3])
print("Priv[4]: ",priv[4])
print("Priv[5]: ",priv[5])

print("==== Public key (show everyone)=====")
pub = merkle(pub)
print("Pub: ", pub)

print("==== Message to sign ===============")
print("Message:\t",message)
print("SHA-256:\t",sha256(message.encode()))
print("==== Signature =====================")
sign = sign_wkey(priv, message.encode())

print("Signature size is ", 32 * len(sign))
print("Sign[0]:\t",sign[0])
print("Sign[1]:\t",sign[1])
print("Sign[2]:\t",sign[2])
print("Sign[3]:\t",sign[3])
print("Sign[{}]:\t".format(len(sign) - 1), sign[-1])
print("The signature test is ",verify_wkey(sign, message.encode(),pub))
