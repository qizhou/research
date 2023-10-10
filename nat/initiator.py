import socket
import sys

# rendezvous port and address
RENDEZVOUS_UDP_IP = sys.argv[1]
RENDEZVOUS_UDP_PORT = 5005

UDP_IP = "0.0.0.0"
UDP_PORT = 5006

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

sock.sendto(b"initiator hello", (RENDEZVOUS_UDP_IP, RENDEZVOUS_UDP_PORT))

print("waiting for rendezvous relay msg ...")
data, _ = sock.recvfrom(1024)

rev_ip = str(data[0:-2], "ascii")
rev_port = int.from_bytes(data[-2:], byteorder="big")

sock.settimeout(1.1)
while True:
    try:
        data, _ = sock.recvfrom(1024)
        print("receiver msg: %s" % data)
    except socket.timeout:
        pass

    print("send message to receiver %s:%s" % (rev_ip, rev_port))
    sock.sendto(b"initator hello", (rev_ip, rev_port))

