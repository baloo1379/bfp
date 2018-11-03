import socket
from protocol import BFP
import threading
import time
import sys
import random
import copy

SERVER = '25.21.164.65'
HOST = '25.21.131.8'
DEBUG = True


class Client:
    server_ip = ''
    host_ip = ''
    packet = BFP()
    old_packet = BFP()
    estabilished = False
    stage = 0

    def __init__(self, server_ip='25.21.131.8', host_ip='25.21.131.8'):
        self.host_ip = host_ip
        self.server_ip = server_ip
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_RAW, 200)
            self.s.bind((self.host_ip, 0))

        except OSError as e:
            print(f'Coś poszło nie tak: {e.strerror}, kod: [{e.errno}], adres: {self.host_ip}')
            sys.exit()

    def send(self):
        self.packet.ack_id = self.packet.seq_id + 1
        self.packet.seq_id = random.randrange(1, 1024)
        self.s.sendto(self.packet.pack_packet(), (self.server_ip, 0))
        if DEBUG:
            print("Send to", self.server_ip, "at", time.asctime())
            self.packet.print()

    def listen(self):
        while True:
            raw = self.s.recvfrom(65535)
            # self.server_ip = raw[1][0]
            if DEBUG:
                print("Received from", self.server_ip, "at", time.asctime())

            raw_packet = raw[0].hex()
            ihl = int(int(raw_packet[1]) * 32 / 8)
            raw_data = raw[0][ihl:]
            self.packet.parse_data(raw_data)
            self.packet.print()
            return

    def receive(self):
        self.listen()
        if self.old_packet.seq_id + 1 != self.packet.ack_id and self.old_packet.session_id != self.packet.session_id:
            print("Wrong response. Leaving.")
            self.packet = BFP()
            self.stage = 0
            self.estabilished = False
            self.send()
        if self.packet.fin:
            self.close(False)

    def connect(self):
        self.packet = BFP("-", (False, False, False, True), random.randrange(0, 1024), random.randrange(0, 1024), 1997, 1234, 4321)
        self.old_packet = copy.copy(self.packet)

        self.send()
        self.listen()
        if self.packet.syn & self.packet.ack & self.stage == 0:
            if self.old_packet.seq_id+1 != self.packet.ack_id and self.old_packet.session_id != self.packet.session_id:
                print("Wrong response. Leaving.")
                self.packet = BFP()
                self.stage = 0
                return
            print("Received second step")
            self.send()
            self.listen()
            if self.old_packet.seq_id+1 != self.packet.ack_id and self.old_packet.session_id != self.packet.session_id:
                print("Wrong response. Leaving.")
                self.packet = BFP()
                self.stage = 0
                return
            print("ESTABILISHED")
            self.estabilished = True
            self.send()
            self.packet.syn = False
        else:
            print("Unrecognized packet")
            self.packet = BFP()
            self.stage = 0
        print("END CONNECT")

    def close(self, ack=True):
        if ack:
            self.packet.fin = True
            self.send()
        self.packet = BFP()
        self.stage = 0
        self.estabilished = False
        print("CONNECTION CLOSED")


def sender(s_ip, h_ip):

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, 200)
        s.bind((h_ip, 0))

    except OSError as e:
        print(f'Coś poszło nie tak: {e.strerror}, kod: [{e.errno}], adres: {h_ip}')
        sys.exit()

    packet = BFP("-", (False, True, True), 100, 0, 1997, 1234, 4321)
    s.sendto(packet.pack_packet(), (s_ip, 0))
    print(time.asctime(), "send from", h_ip, "to", s_ip)


def listener():
    print(f'listening on {HOST}')
    packet = BFP()
    with socket.socket(socket.AF_INET, socket.SOCK_RAW, 200) as s:
        s.bind((HOST, 0))
        while True:
            row = s.recvfrom(65535)

            client = row[1][0]
            pt = row[0].hex()
            ihl = int(int(pt[1]) * 32 / 8)
            data = row[0][ihl:]
            packet.parse_data(data)
            print("from:", client, "data:")
            packet.print()
            if packet.syn:
                new_packet = packet
                new_packet.ack_id = packet.seq_id + 1
                new_packet.seq_id = 500
                new_packet.ack = True
                s.sendto(new_packet.pack_packet(), (SERVER, 0))


class Sender (threading.Thread):
    def __init__(self, threadID, name, serv, host):
        super(Sender, self).__init__()
        self.threadID = threadID
        self.name = name
        self.serv = serv
        self.host = host

    def run(self):
        while True:
            sender(self.serv, self.host)
            time.sleep(5)


class Listener (threading.Thread):
    def __init__(self, threadID, name):
        super(Listener, self).__init__()
        self.threadID = threadID
        self.name = name

    def run(self):
        while True:
            listener()


def main():
    if len(sys.argv) == 3:
        serv = sys.argv[1]
        host = sys.argv[2]
    else:
        serv = SERVER
        host = HOST

    c = Client(serv, host)
    c.connect()
    while c.estabilished:
        c.send()
        time.sleep(1)
        c.receive()
        exit = input()
        if exit == "exit":
            c.close()

    input("ENTER to Continue")


if __name__ == "__main__":
    main()
