import socket
from protocol import BFP
import time
import sys
import random
import copy


DEBUG = True
#states
LISTEN = 0
SYN_RCVD = 1
ESTABLISHED = 2
CLOSE_WAIT = 3
LAST_ACK = 4
CLOSED = 5
#addresses
LOCALHOST = '127.0.0.1'


class Server:
    server = '192.168.0.1'
    client = '255.255.255.255'
    packet = BFP()
    old_packet = BFP()
    state = LISTEN
    error_count = 0

    def __init__(self, host):
        self.server = host
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_RAW, 200)
            self.s.bind((self.server, 0))
            self.s.settimeout(10.0)

        except OSError as e:
            print(f'Coś poszło nie tak: {e.strerror}, kod: [{e.errno}], adres: {self.server}')
            sys.exit()

        print("Server ready on", self.server)
        self.state = LISTEN
        self.error_count = 0

    def is_response_ok(self):
        if self.packet.ack and self.old_packet.seq_id + 1 == self.packet.ack_id and self.old_packet.session_id == self.packet.session_id:
            return True
        else:
            return False

    def send(self):
        if self.packet.ack:
            self.packet.ack_id = self.packet.seq_id + 1
        else:
            self.packet.ack_id = 0
        self.packet.seq_id = random.randrange(1, 1024)
        self.s.sendto(self.packet.pack_packet(), (self.client, 0))
        if DEBUG:
            print("Send to", self.client, "at", time.asctime())
            self.packet.print()

    def listen(self):
        while True:
            raw = self.s.recvfrom(65535)
            self.client = raw[1][0]
            if DEBUG:
                print("Received from", self.client, "at", time.asctime())

            raw_packet = raw[0].hex()
            ihl = int(int(raw_packet[1]) * 32 / 8)
            raw_data = raw[0][ihl:]
            self.old_packet = copy.copy(self.packet)
            self.packet.parse_data(raw_data)
            self.packet.print()
            return

    def receive(self):
        self.listen()

        # flags                    none   fin    ack    syn
        if self.packet.status == (False, False, False, False):
            if self.state == ESTABLISHED:
                # request from connected client
                ok = False
                while not ok:
                    ok = True
                    if self.packet.operation == '+':
                        self.packet.first = self.packet.first + self.packet.second
                        self.packet.ack = True
                        self.send()
                    elif self.packet.operation == '-':
                        self.packet.first = self.packet.first - self.packet.second
                        self.packet.ack = True
                        self.send()
                    elif self.packet.operation == '*':
                        self.packet.first = self.packet.first * self.packet.second
                        self.packet.ack = True
                        self.send()
                    elif self.packet.operation == '/':
                        self.packet.first = int(self.packet.first / self.packet.second)
                        self.packet.ack = True
                        self.send()
                    elif self.packet.operation == 'OR':
                        self.packet.first = self.packet.first + self.packet.second
                        self.packet.ack = True
                        self.send()
                    elif self.packet.operation == 'XOR':
                        self.packet.first = self.packet.first + self.packet.second
                        self.packet.ack = True
                        self.send()
                    elif self.packet.operation == 'AND':
                        self.packet.first = self.packet.first + self.packet.second
                        self.packet.ack = True
                        self.send()
                    elif self.packet.operation == 'NOT' or self.packet.operation == '!':
                        self.packet.first = -self.packet.first
                        self.packet.second = -self.packet.second
                        self.packet.ack = True
                        self.send()

                    self.listen()
                    if self.is_response_ok():
                        print("RESPONSE OK")
                    else:
                        ok = False
                        self.error_count = self.error_count + 1
                        if self.error_count > 1:
                            self.state = LISTEN
                            self.error_count = 0
                            ok = True

            else:
                # random request - ignore
                self.state = CLOSED

        if self.packet.status == (False, True, False, False):
            # received closing
            self.state = CLOSE_WAIT
            self.packet.fin = False
            self.packet.ack = True
            self.send()
            # send ack of client fin
            self.packet.fin = True
            self.packet.ack = False
            self.send()
            # send server fin
            self.state = LAST_ACK
            self.listen()
            # waiting for client ack
            if self.packet.ack and self.old_packet.seq_id+1 == self.packet.ack_id:
                #ack ok
                self.state = CLOSED

        if self.packet.status == (False, False, False, True):
            if self.state == LISTEN:
                # synchronizing
                if DEBUG:
                    print("SYNCHRONIZING")
                self.state = 1
                self.packet.ack = True
                self.send()
                self.listen()
                if self.packet.status == (False, False, True, False):
                    if self.old_packet.seq_id + 1 == self.packet.ack_id and self.old_packet.session_id == self.packet.session_id:
                        # estabilished
                        if DEBUG:
                            print("ESTABILISHED")
                        self.packet.syn = False
                        self.packet.ack = False
                        self.state = ESTABLISHED
            else:
                #error
                print("Wrong response")
                self.error_count = self.error_count + 1
                if self.error_count > 1:
                    self.state = LISTEN
                    self.error_count = 0


def main():
    if len(sys.argv) > 1:
        x = Server(str(sys.argv[1]))
    else:
        x = Server(LOCALHOST)

    while not x.state == CLOSED:
        x.receive()

    input("ENTER to Continue")


if __name__ == "__main__":
    main()
