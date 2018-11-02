import socket


class Server:
    host = '127.0.0.1'
    client = '255.255.255.255'

    def __init__(self):
        self.host = socket.gethostbyname(socket.gethostname())
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_RAW, 200)
            self.s.bind((self.host, 0))

        except OSError as e:
            print(f'Coś poszło nie tak: {e.strerror}, kod: [{e.errno}]')

    def s_step_handshake(self, seq):
        seq = str(seq)
        self.s.sendto(seq.encode(), (self.client, 0))

    def listen(self):
        while True:
            row = self.s.recvfrom(65535)
            self.client = row[1][0]
            packet = row[0].hex()
            ihl = int(int(packet[1]) * 32 / 8)
            data = row[0][ihl:]
            data = data.decode()
            print("from:", self.client, "data:", data)
            data = data.split(', ')
            if data[0] == 12:
                self.s_step_handshake(data[1]+1)
