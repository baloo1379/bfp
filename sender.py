import socket
from protocol import BFP
import time
import sys
import random
import copy

SERVER = '25.21.164.65'
HOST = '25.21.131.8'
DEBUG = True

WAIT = 0
SYN_SENT = 1
ESTABLISHED = 2
FIN_WAIT_1 = 3
FIN_WAIT_2 = 4
TIME_WAIT = 5


class Client:
    server_ip = ''
    host_ip = ''
    packet = BFP()
    old_packet = BFP()
    state = WAIT

    def __init__(self, server_ip='25.21.131.8', host_ip='25.21.131.8'):
        self.host_ip = host_ip
        self.server_ip = server_ip
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_RAW, 200)
            self.s.bind((self.host_ip, 0))
            self.s.settimeout(10.0)

        except OSError as e:
            print(f'Coś poszło nie tak: {e.strerror}, kod: [{e.errno}], adres: {self.host_ip}')
            sys.exit()

    def is_response_ok(self):
        if self.packet.ack and self.old_packet.seq_id + 1 == self.packet.ack_id and \
                self.old_packet.session_id == self.packet.session_id:
            return True
        else:
            return False

    def send(self):
        if self.packet.ack:
            self.packet.ack_id = self.packet.seq_id + 1
        else:
            self.packet.ack_id = 0
        self.packet.seq_id = random.randrange(1, 1024)
        self.s.sendto(self.packet.pack_packet(), (self.server_ip, 0))
        if DEBUG:
            print("Send to", self.server_ip, "at", time.asctime())
            self.packet.print()

    def listen(self):
        while True:
            try:
                raw = self.s.recvfrom(65535)
            except socket.timeout:
                self.state = TIME_WAIT
                if DEBUG:
                    print("TIMEOUT")
                    return
            # self.server_ip = raw[1][0]
            if DEBUG:
                print("Received from", self.server_ip, "at", time.asctime())

            raw_packet = raw[0].hex()
            ihl = int(int(raw_packet[1]) * 32 / 8)
            raw_data = raw[0][ihl:]
            self.old_packet = copy.copy(self.packet)
            self.packet.parse_data(raw_data)
            self.packet.print()
            return

    def receive(self):
        self.listen()
        if self.is_response_ok():
            # response ok
            if DEBUG:
                print("REQUEST OK")
            self.send()
            print("Wynik:", self.packet.first)
            self.packet.ack = False

    def connect(self):
        self.packet = BFP("-", (False, False, False, True), random.randrange(0, 1024), random.randrange(0, 1024),
                          random.randrange(1, 65535), 1234, 4321)
        # synchronizing
        self.send()
        self.state = SYN_SENT
        if DEBUG:
            print("SYNCHRONIZING")

        self.listen()
        if self.packet.status == (False, False, True, True) and self.state == SYN_SENT:
            if self.old_packet.seq_id+1 == self.packet.ack_id and self.old_packet.session_id == self.packet.session_id:
                # estabilished
                if DEBUG:
                    print("ESTABILISHED")
                self.packet.syn = False
                self.packet.ack = True
                self.send()
                self.state = ESTABLISHED
                self.packet.syn = False
                self.packet.ack = False

        else:
            print("BAD RESPONSE")
            self.packet = BFP()
            self.state = WAIT
        print("END CONNECT")

    def close(self):
        self.packet = BFP('+', (False, True, False, False), random.randrange(0, 1024), 0, self.packet.session_id, 0, 0)
        self.send()
        self.state = FIN_WAIT_1
        self.listen()
        if self.packet.ack and self.old_packet.seq_id+1 == self.packet.ack_id:
            # ack ok
            self.state = FIN_WAIT_2
            self.listen()
            if self.packet.fin:
                # fin received
                self.state = TIME_WAIT
                self.packet.fin = False
                self.packet.ack = True
                self.send()


def main():
    if len(sys.argv) == 3:
        server = sys.argv[1]
        host = sys.argv[2]
    else:
        server = SERVER
        host = HOST

    # c = Client('127.0.0.1', '127.0.0.1')
    c = Client(server, host)
    while not c.state == ESTABLISHED:
        c.connect()
        if c.state == WAIT:
            user = input("RECONNECT?")
    while c.state == ESTABLISHED:
        user = input()

        if user == "exit":
            c.close()
            print('Goodbye')
            break

        user = user.split(" ")
        if len(user) > 3:
            if DEBUG:
                print(len(user), user)
            print("Too many arguments. Only 3 arguments are valid. ex. 3 + 5")
            continue
        else:
            a = int(user[0])
            b = int(user[2])
            operation = user[1]
            c.packet.operation = operation
            c.packet.first = a
            c.packet.second = b
            c.send()
            c.receive()


if __name__ == "__main__":
    main()
