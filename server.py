import socket
from protocol import BFP
import sys
from core import listener, sender


DEBUG = True
# states
LISTEN = 0
SYN_RCVD = 1
ESTABLISHED = 2
CLOSE_WAIT = 3
LAST_ACK = 4
CLOSED = 5


class Server:
    def __init__(self, server_ip):
        self.server_ip = server_ip
        self.ip = ''
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_RAW, 200)
            self.s.bind((self.server_ip, 0))
        except OSError as e:
            print(f'Something went wrong: {e.strerror}, code: [{e.errno}], address: {self.server_ip}')
            sys.exit()
        else:
            if DEBUG:
                self.s.settimeout(2.0)
            else:
                self.s.settimeout(10.0)
            self.state = LISTEN
            self.error_count = 0
            self.packet = BFP()
            self.old_packet = BFP()
            print("Server ready on", self.server_ip)

    def is_response_ok(self):
        if self.packet.ack and self.old_packet.seq_id + 1 == self.packet.ack_id and \
                self.old_packet.session_id == self.packet.session_id:
            return True
        else:
            return False

    def send(self):
        return sender(self, DEBUG)

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
                while True:
                    if DEBUG:
                        print("OPERATION: ", self.packet.first, self.packet.operation, self.packet.second)

                    if self.packet.operation == '+':
                        self.packet.first = self.packet.first + self.packet.second
                    elif self.packet.operation == '-':
                        self.packet.first = self.packet.first - self.packet.second
                    elif self.packet.operation == '*':
                        self.packet.first = self.packet.first * self.packet.second
                    elif self.packet.operation == '/':
                        self.packet.first = int(self.packet.first / self.packet.second)
                    elif self.packet.operation == 'OR':
                        self.packet.first = self.packet.first or self.packet.second
                    elif self.packet.operation == 'XOR':
                        self.packet.first = self.packet.first or self.packet.second
                    elif self.packet.operation == 'AND':
                        self.packet.first = self.packet.first and self.packet.second
                    elif self.packet.operation == 'NOT' or self.packet.operation == '!':
                        self.packet.first = -self.packet.first
                        self.packet.second = -self.packet.second
                    if DEBUG:
                        print("EQUALS", self.packet.first)
                    self.packet.ack = True
                    self.send()

                    if not self.listen():
                        self.error_count = self.error_count + 1
                        continue
                    if self.is_response_ok():
                        print("Response ok")
                        break
                    else:
                        self.error_count = self.error_count + 1
                        continue

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
