import copy
import time
import random


def listener(this, socket, debug):
    while True:
        try:
            raw = this.s.recvfrom(65535)
        except socket.timeout:
            if debug:
                print("SOCKET TIMEOUT")
            return False
        else:
            this.timeout = False
            this.ip = raw[1][0]
            if debug:
                print("RECEIVED FROM", this.ip, "AT", time.asctime())

            raw_packet = raw[0].hex()
            ihl = int(int(raw_packet[1]) * 32 / 8)
            raw_data = raw[0][ihl:]
            this.old_packet = copy.copy(this.packet)
            this.packet.parse_data(raw_data)
            if debug:
                this.packet.print()
            return True


def sender(this, debug):
    if this.packet.ack:
        this.packet.ack_id = this.packet.seq_id + 1
    else:
        this.packet.ack_id = 0
    this.packet.seq_id = random.randrange(1, 1024)
    this.s.sendto(this.packet.pack_packet(), (this.ip, 0))
    if debug:
        print("SEND TO", this.ip, "AT", time.asctime())
        this.packet.print()
