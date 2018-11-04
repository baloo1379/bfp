import socket
from protocol import BFP
import time
import sys
import random
from core import listener


DEBUG = False
# states
LISTEN = 0
SYN_RCVD = 1
ESTABLISHED = 2
CLOSE_WAIT = 3
LAST_ACK = 4
CLOSED = 5


class Server:
    server = ''
    ip = ''
    packet = BFP()
    old_packet = BFP()
    state = LISTEN
    error_count = 0

    def __init__(self, host):
        self.server = host
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_RAW, 200)
            self.s.bind((self.server, 0))
            if DEBUG:
                self.s.settimeout(2.0)
            else:
                self.s.settimeout(10.0)

        except OSError as e:
            print(f'Something went wrong: {e.strerror}, code: [{e.errno}], address: {self.server}')
            sys.exit()

        print("Server ready on", self.server)
        self.state = LISTEN
        self.error_count = 0

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
        self.s.sendto(self.packet.pack_packet(), (self.ip, 0))
        if DEBUG:
            print("Send to", self.ip, "at", time.asctime())
            self.packet.print()

    # def listen(self):
    #     while True:
    #         raw = self.s.recvfrom(65535)
    #         self.ip = raw[1][0]
    #         if DEBUG:
    #             print("Received from", self.ip, "at", time.asctime())
    #
    #         raw_packet = raw[0].hex()
    #         ihl = int(int(raw_packet[1]) * 32 / 8)
    #         raw_data = raw[0][ihl:]
    #         self.old_packet = copy.copy(self.packet)
    #         self.packet.parse_data(raw_data)
    #         if DEBUG:
    #             self.packet.print()
    #
    def listen(self):
        return listener(self, socket, DEBUG)

    def receive(self):
        while True:
            if self.listen():
                break

        # receiving data                    none   fin    ack    syn
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

        # closing
        if self.packet.status == (False, True, False, False):
            # received closing
            print("Closing connection")
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
                # ack ok
                print("Connection closed")
                self.state = CLOSED

        # syncing
        if self.packet.status == (False, False, False, True):
            if self.state == LISTEN:
                sync_counter = 0
                while True:
                    if sync_counter > 1:
                        if DEBUG:
                            print("CAN'T SYNC WITH CLIENT. BACK TO LISTEN")
                        self.state = LISTEN
                        return
                    # synchronizing
                    if DEBUG:
                        print("SYNCHRONIZING")
                    print("Connecting")
                    self.state = SYN_RCVD
                    self.packet.ack = True
                    self.send()
                    if not self.listen():
                        sync_counter = sync_counter + 1
                        continue
                    if self.packet.status == (False, False, True, False):
                        if self.old_packet.seq_id + 1 == self.packet.ack_id and \
                                self.old_packet.session_id == self.packet.session_id:
                            # established
                            if DEBUG:
                                print("ESTABLISHED")
                            print("Connected with", self.ip)
                            self.packet.syn = False
                            self.packet.ack = False
                            self.state = ESTABLISHED
                            break
            else:
                # error
                print("Wrong packet")
                self.error_count = self.error_count + 1
                if self.error_count > 1:
                    self.state = LISTEN
                    self.error_count = 0


def run():
    if len(sys.argv) > 1:
        x = Server(str(sys.argv[1]))
    else:
        self_ip_address = input("Type your ip address\n")
        x = Server(self_ip_address)

    while not x.state == CLOSED:
        x.receive()

    input("Press ENTER to exit")


if __name__ == "__main__":
    run()
