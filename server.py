import socket
from protocol import BFP
import time
import sys
import random
import copy


DEBUG = True


class Server:
    server = '192.168.0.101'
    client = '255.255.255.255'
    packet = BFP()
    old_packet = BFP()
    estabilished = False
    stage = 0

    def __init__(self, host='25.21.131.8'):
        self.server = host
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_RAW, 200)
            self.s.bind((self.server, 0))

        except OSError as e:
            print(f'Coś poszło nie tak: {e.strerror}, kod: [{e.errno}], adres: {self.server}')
            sys.exit()
        print("Server ready on", self.server)

    def send(self):
        self.packet.ack_id = self.packet.seq_id + 1
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

        self.listen()
        print("stage:", self.stage)
        if self.packet.syn and self.stage == 0:
            print("Received first step")
            self.old_packet = copy.copy(self.packet)
            self.packet.ack = True
            self.send()
            self.stage = 1
            print("stage up 1")

        elif self.packet.syn and self.packet.ack and self.stage == 1:
            if self.old_packet.seq_id+1 != self.packet.ack_id and self.old_packet.session_id != self.packet.session_id:
                print("Wrong response. Leaving.")
                self.packet = BFP()
                self.stage = 0
                return
            print("Received second step")
            self.old_packet = copy.copy(self.packet)
            new_packet = copy.copy(self.packet)
            new_packet.ack_id = self.packet.seq_id + 1
            new_packet.seq_id = random.randrange(1, 1024)
            self.packet = copy.copy(new_packet)
            self.send()
            self.stage = 2
            print("stage up 2")

        elif self.packet.syn and self.packet.ack and self.stage == 2:
            if self.old_packet.seq_id+1 != self.packet.ack_id and self.old_packet.session_id != self.packet.session_id:
                print("Wrong response. Leaving.")
                self.packet = BFP()
                self.stage = 0
                return
            print("ESTABILISHED")
            self.estabilished = True
            self.packet.syn = False

        else:
            print("Unrecognized packet")
            self.packet = BFP()
            self.stage = 0

    def close(self, ack=True):
        if ack:
            self.packet.fin = True
            self.send()
        self.packet = BFP()
        self.stage = 0
        self.estabilished = False
        print("CONNECTION CLOSED")
        input("ENTER to Continue")
        sys.exit()


def main():
    if len(sys.argv) > 1:
        x = Server(str(sys.argv[1]))
    else:
        x = Server()

    while not x.estabilished:
        x.connect()
        while x.estabilished:
            x.receive()
            x.send()

    input("ENTER to Continue")


if __name__ == "__main__":
    main()
