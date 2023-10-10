import socket

# public port and address
UDP_IP = "0.0.0.0"
UDP_PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sock.bind((UDP_IP, UDP_PORT))

print("waiting for receiver message")
data, rev_addr = sock.recvfrom(1024)
print("received message from receiver: %s, addr: %s" % (data, rev_addr))

print("waiting for initiator message")
data, int_addr = sock.recvfrom(1024)
print("received message from initiator: %s, addr: %s" % (data, int_addr))

# now the rendezvous node has the info of both nodes, share the info to both of them

print("send receiver address to initiator")
msg = bytes(rev_addr[0], "ascii") + rev_addr[1].to_bytes(2, byteorder="big")
sock.sendto(msg, int_addr)

print("waiting initiator to tryhello")
data, _ = sock.recvfrom(1024)
# assert addr from initiator

print("send initiator address to receiver")
msg = bytes(int_addr[0], "ascii") + int_addr[1].to_bytes(2, byteorder="big")
sock.sendto(msg, rev_addr)

# initiator should be able to talk with receiver