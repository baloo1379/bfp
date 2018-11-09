import socket
from protocol import BFP
import sys
import random
from core import listener, sender


DEBUG = True

# states
WAIT = 0
SYN_SENT = 1
ESTABLISHED = 2
FIN_WAIT_1 = 3
FIN_WAIT_2 = 4
TIME_WAIT = 5


class Client:
    def __init__(self, server_ip, client_ip):
        self.client_ip = client_ip
        self.server_ip = server_ip
        self.ip = server_ip
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_RAW, 200)
            self.s.bind((self.client_ip, 0))
        except OSError as e:
            print(f'Something went wrong: {e.strerror}, code: [{e.errno}], address: {self.server_ip}')
            sys.exit()
        else:
            if DEBUG:
                self.s.settimeout(2.0)
            else:
                self.s.settimeout(10.0)
            self.state = WAIT
            self.packet = BFP()
            self.old_packet = BFP()

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
        if not self.listen():
            return False
        if self.is_response_ok():
            # response ok
            if DEBUG:
                print("REQUEST OK")
            self.send()
            if self.old_packet.operation == '!':
                print("Equals:", self.packet.second)
            else:
                print("Equals:", self.packet.first)
            self.packet.ack = False
            return True
        else:
            if DEBUG:
                print("WRONG ACK RESPONSE")
            return False

    def connect(self):
        sync_counter = 0
        # synchronizing
        while True:
            self.packet = BFP("-", (False, False, False, True), random.randrange(0, 1024), random.randrange(0, 1024),
                              random.randrange(1, 65535), 1234, 4321)
            if DEBUG:
                print("SYNC_COUNTER =", sync_counter)
            if sync_counter > 2:
                if DEBUG:
                    print("CAN'T CONNECT TO SERVER. QUITING")
                return False
            self.send()
            self.state = SYN_SENT
            if DEBUG:
                print("SYNCHRONIZING")
            if not self.listen():
                sync_counter = sync_counter + 1
                continue
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
                    print("Connected")
            else:
                print("BAD RESPONSE")
                self.packet = BFP()
                self.state = WAIT
                return False
            if DEBUG:
                print("END CONNECT")
            return True

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

    def ping(self):
        self.packet = BFP("NOT", (False, True, True, True), random.randrange(0, 1024), random.randrange(0, 1024),
                          random.randrange(1, 65535), random.randrange(0, 1024), random.randrange(0, 1024))
        self.send()


def run():
    if len(sys.argv) == 3:
        server = sys.argv[1]
        host = sys.argv[2]
    else:
        server = input("Give me server address: ")
        host = input("Give me your address: ")

    c = Client(server, host)

    if not c.connect():
        print("Cant' connect.")
        input("Press ENTER to exit.")
        sys.exit()
    while c.state == ESTABLISHED:
        err_counter = 0
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

            while True:
                if DEBUG:
                    print("err_counter =", err_counter)
                if err_counter > 2:
                    print("Connection lost. Quiting.")
                    c.state = TIME_WAIT
                    break
                c.send()
                if not c.receive():
                    err_counter = err_counter + 1
                    continue
                else:
                    err_counter = 0
                    break


if __name__ == "__main__":
    run()
