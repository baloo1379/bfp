from struct import pack, unpack
from bitstring import BitArray, Bits


class BFP:

    # operacja matematyczna
    operation = ''

    # status/flagi
    syn = False
    seq = False
    ack = False
    fin = False

    status = ''

    # dłygość dancyh
    length = BitArray(uint=32*4, length=32)

    # dane
    seq_id = 100
    ack_id = 101
    session_id = 12345
    first = 1
    second = 2

    # nagłowek i dane
    header = ''
    data = ''

    def __init__(self, operation="+", status=(False, False, False, False), seq=100, ack=100, session_id=100,
                 first=0, second=0):

        # ustawianie operacji
        if operation == '+':
            self.operation = BitArray(int=0, length=3)
        elif operation == '-':
            self.operation = BitArray(int=1, length=3)
        elif operation == '*':
            self.operation = BitArray(int=2, length=3)
        elif operation == '/':
            self.operation = BitArray(int=3, length=3)
        elif operation == 'OR':
            self.operation = BitArray(int=4, length=3)
        elif operation == 'XOR':
            self.operation = BitArray(int=5, length=3)
        elif operation == 'AND':
            self.operation = BitArray(int=6, length=3)
        elif operation == 'NOT':
            self.operation = BitArray(int=7, length=3)
        elif operation == '!':
            self.operation = BitArray(int=7, length=3)
        else:
            raise Exception(f'Nieprawidłowy format operacji: {operation}')

        # ustawianie poszczególnych flag
        # if status[0]:
        #     self.syn = True
        # else:
        #     self.syn = False
        # if status[1]:
        #     self.seq = True
        # else:
        #     self.seq = False
        # if status[2]:
        #     self.ack = True
        # else:
        #     self.ack = False
        # if status[3]:
        #     self.fin = True
        # else:
        #     self.fin = False

        self.status = Bits(uint=status, length=4)

        print(self.operation.bytes, self.status.bytes, self.length.bytes)
        self.first = first
        self.second = second

    def pack_data(self):
        self.data = pack("!HHIII", self.seq_id, self.ack_id, self.session_id, self.first, self.second)

    def pack_packet(self):
        self.pack_data()
        self.header = self.operation.bytes + self.status.bytes + self.length.bytes + self.data

    def parse_data(self, data):
        self.data = data

        print(len(self.data))



def main():
    f_packet = BFP("/", 12, 12, (True, True, False, False), 22, 0, 1997)

    s_packet = BFP()
    s_packet.parse_data(f_packet.pack_packet())


if __name__ == "__main__":
    main()


