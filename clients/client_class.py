import socket, sys
import msg

class Client:
    """Class implentation
    """
    def __init__(self, server_addr):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(server_addr)      # connect to server process
        # convert socket to file-like obj only for imcoming messages
        self.in_file = self.sock.makefile('rb')
        self.sent_bytes = []
        self.recv_bytes = []

    def run(self):
        for message in msg.msgs(20, length=2000):
            self.sock.sendall(message)
            self.sent_bytes.append(len(message))
            data = self.in_file.readline() # receive response
            if not data:
                print('Server closing')
                break
            self.recv_bytes.append(len(data))
        self.sock.close()                    # to send eof to server
        msg.report(self.sent_bytes, self.recv_bytes)

if __name__ == '__main__':
    # command line processing
    serv_addr = ('np.hufs.ac.kr', 7)    # default server_addr
    if len(sys.argv) == 3:
        serv_addr = sys.argv[1], sys.argv[2]
    elif len(sys.argv) != 1:
        print('Usage: {} [host port]', sys.argv[0])
        sys.exit(1)

    cli = Client(serv_addr)
    cli.run()
