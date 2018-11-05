from struct import pack, unpack
from bitstring import BitArray, Bits


DEBUG = False


def tuple_to_int(tuplex):
    if type(tuplex) == int:
        return tuplex
    else:
        power = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]
        value = 0
        length = len(tuplex)-1
        for x in tuplex:
            if x:
                value = value + 1*power[length]
            length = length - 1
        return value


def int_to_tuple(value):
    word = bin(value)
    elements = list(word)
    elements = elements[2:]
    for x in range(len(elements)):
        if elements[x] == '1':
            elements[x] = True
        else:
            elements[x] = False

    elen = 4 - len(elements)
    for xx in range(elen):
        elements.insert(0, False)
    return tuple(elements)


class BFP:

    # offset
    offset = BitArray(uint=0, length=1)

    # operacja matematyczna
    operation = ''

    # status/flagi
    syn = False
    ack = False
    fin = False

    status = ''

    # dłygość dancyh
    length = 32*4

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

        self.operation = operation

        self.syn = status[3]
        self.ack = status[2]
        self.fin = status[1]
        self.status = status
        self.seq_id = seq
        self.ack_id = ack
        self.session_id = session_id
        self.first = first
        self.second = second

        # pakowanie pakietu po jego utworzeniu
        self.pack_packet()

    def pack_data(self):
        self.data = pack("!HHIii", self.seq_id, self.ack_id, self.session_id, self.first, self.second)

    def unpack_data(self):
        data = unpack("!HHIii", self.data)
        self.seq_id = data[0]
        self.ack_id = data[1]
        self.session_id = data[2]

        self.first = data[3]
        self.second = data[4]

    def pack_packet(self):
        self.pack_data()

        # ustawianie operacji
        if self.operation == '+':
            operation = BitArray(uint=0, length=3)
        elif self.operation == '-':
            operation = BitArray(uint=1, length=3)
        elif self.operation == '*':
            operation = BitArray(uint=2, length=3)
        elif self.operation == '/':
            operation = BitArray(uint=3, length=3)
        elif self.operation == 'OR':
            operation = BitArray(uint=4, length=3)
        elif self.operation == 'XOR':
            operation = BitArray(uint=5, length=3)
        elif self.operation == 'AND':
            operation = BitArray(uint=6, length=3)
        elif self.operation == 'NOT':
            operation = BitArray(uint=7, length=3)
        elif self.operation == '!':
            operation = BitArray(uint=7, length=3)
        else:
            raise Exception(f'Nieprawidłowy format operacji: {operation}')

        self.status = (False, self.fin, self.ack, self.syn)
        status = tuple_to_int(self.status)
        status = Bits(uint=status, length=4)

        header = operation + status + BitArray(uint=self.length, length=32) + self.offset
        self.header = header.bytes
        packet = self.header + self.data
        return packet

    def parse_data(self, data):
        self.data = BitArray(data)
        header = self.data[0:40]
        self.data = self.data[40:].bytes

        if DEBUG:
            print(header.bin, data)
            print(header[0:3].uint, header[3:7].uint, header[7:-1].int, int(header[-1]))

        operation = header[0:3].uint
        self.status = int_to_tuple(header[3:7].uint)
        self.syn = self.status[3]
        self.ack = self.status[2]
        self.fin = self.status[1]
        self.length = header[7:-1].int

        if operation == 0:
            self.operation = '+'
        elif operation == 1:
            self.operation = '-'
        elif operation == 2:
            self.operation = '*'
        elif operation == 3:
            self.operation = '/'
        elif operation == 4:
            self.operation = 'OR'
        elif operation == 5:
            self.operation = 'XOR'
        elif operation == 6:
            self.operation = 'AND'
        elif operation == 7:
            self.operation = 'NOT'
        elif operation == 7:
            self.operation = '!'

        self.unpack_data()

    def print(self):
        print(self.operation, (False, self.fin, self.ack, self.syn), self.seq_id, self.ack_id, self.session_id,
              self.first, self.second)


def main():
    # only for testing
    f_packet = BFP("/", (False, False, False, True), 22, 0, 1997, 222, 333)
    f_packet.print()

    s_packet = BFP()
    s_packet.parse_data(f_packet.pack_packet())
    s_packet.ack = True
    s_packet.pack_packet()
    s_packet.print()


if __name__ == "__main__":
    main()
