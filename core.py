import copy
import time


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
