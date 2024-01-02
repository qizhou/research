# https://asecuritysite.com/encryption/wint

import hashlib
from binascii import unhexlify, hexlify


from os import urandom

import sys
message="Hello"

def random_key(n=32):                   #returns a 256 bit hex encoded (64 bytes) random number
    return hexlify(urandom(n))

def sha256(message):
    return hashlib.sha256(message.encode()).hexdigest()

def sha256b(message):
    return hashlib.sha256(message.encode()).digest()

def random_wkey(w=8, verbose=0):      #create random W-OTS keypair

    priv = []
    pub = []
    print("Hashing number random keys by:\t",2**w)
    for x in range(256//w):
        a = str(random_key())
        priv.append(a)
        for y in range(2**w-1):              
            a = sha256(a)
        pub.append(sha256(a))               

    return priv, pub 

def sign_wkey(priv, message):      

    signature = []
    bin_msg = unhexlify(sha256(message))

    for y in range(len(priv)):
        s = priv[y]    
        for x in range(256-ord(bin_msg[y:y+1])):
            s = sha256(s)
        signature.append(s)
    return signature

def verify_wkey(signature, message, pub):

    verify = []
    bin_msg = unhexlify(sha256(message))
    
    for x in range(len(signature)):
        a = signature[x]
                                                    #f is all but last hash..
        for z in range(ord(bin_msg[x:x+1])):
                a=sha256(a)
        #a = sha256(a)                               #g is the final hash, separate so can be changed..
        verify.append(a)
  
    if pub != verify:
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
print("Pub[0]: ",pub[0])
print("Pub[1]: ",pub[1])
print("Pub[2]: ",pub[2])
print("Pub[3]: ",pub[3])
print("Pub[4]: ",pub[4])
print("Pub[5]: ",pub[5])

print("==== Message to sign ===============")
print("Message:\t",message)
print("SHA-256:\t",sha256(message))
print("==== Signature =====================")
sign = sign_wkey(priv,message)

print("Sign[0]:\t",sign[0])
print("Sign[1]:\t",sign[1])
print("Sign[2]:\t",sign[2])
print("Sign[3]:\t",sign[3])
print("The signature test is ",verify_wkey(sign,message,pub))
