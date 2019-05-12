import socket, sys
import msg

class Client:
    """Class implementation
    outgoing: socket
    incoming: file-like object (buffering)
    """
    def __init__(self, server_addr):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(server_addr)      # connect to server process
        # convert socket to file-like obj only for imcoming messages
        self.in_file = self.sock.makefile('rb')
        self.sent_bytes = []
        self.recv_bytes = []

    def run(self):
        for message in msg.msgs(20, length=2000, delay=0.5):
            n_sent = self.sock.send(message)
            self.sent_bytes.append(n_sent)
            data = self.in_file.readline() # receive response
            if not data:
                print('Server closing')
                break
            self.recv_bytes.append(len(data))
        self.sock.close()                    # to send eof to server
        msg.report(self.sent_bytes, self.recv_bytes)

if __name__ == '__main__':
    # command line processing
    if len(sys.argv) == 3:
        serv_addr = sys.argv[1], int(sys.argv[2])
    elif len(sys.argv) == 1:
        serv_addr = ('np.hufs.ac.kr', 7)    # default server_addr
    else:
        print('Usage: {} [host port]', sys.argv[0])
        sys.exit(1)                         # exit with error

    cli = Client(serv_addr)
    cli.run()
