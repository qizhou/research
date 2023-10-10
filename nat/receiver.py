import socket
import sys
from time import sleep

# rendezvous port and address
RENDEZVOUS_UDP_IP = sys.argv[1]
RENDEZVOUS_UDP_PORT = 5005

UDP_IP = "0.0.0.0"
UDP_PORT = 5007

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print("sending hello to rendezvous ...")
sock.sendto(b"receiver hello", (RENDEZVOUS_UDP_IP, RENDEZVOUS_UDP_PORT))

print("waiting for relay msg from rendezvous ...")
data, _ = sock.recvfrom(1024)

int_ip = str(data[0:-2], "ascii")
int_port = int.from_bytes(data[-2:], byteorder="big")

sock.settimeout(1)
while True:
    try:
        data, _ = sock.recvfrom(1024)
        print("initiator msg: %s" % data)
    except socket.timeout:
        pass

    print("send message to receiver %s:%s" % (int_ip, int_port))
    sock.sendto(b"receiver hello", (int_ip, int_port))