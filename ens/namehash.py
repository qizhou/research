import sha3


def s3(data):
  k = sha3.keccak_256()
  k.update(data)
  return k.digest()


def namehash(name):
  if name == b'':
    return b'\0' * 32
  else:
    label, _, remainder = name.partition(b'.')
    return s3(namehash(remainder) + s3(label))

print("namehash of w3url.eth is {}".format(namehash(b'w3url.eth').hex()))
