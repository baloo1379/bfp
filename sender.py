import socket

HOST = socket.gethostbyname(socket.gethostname())


def main():
    print("send from", HOST)

    with socket.socket(socket.AF_INET, socket.SOCK_RAW, 200) as s:
        s.bind((HOST, 0))
        out = True

        while out:
            user_input = input("Wpisz dane aby wysłać, lub exit sby wyjść\n")
            if user_input == "exit":
                out = False
            else:
                s.sendto(user_input.encode(), ('192.168.0.101', 0))
                while True:
                    row = s.recvfrom(65535)
                    client = row[1][0]
                    packet = row[0].hex()
                    ihl = int(int(packet[1]) * 32 / 8)
                    data = row[0][ihl:]
                    data = data.decode()
                    print("from:", client, "data:", data)


if __name__ == "__main__":
    main()
