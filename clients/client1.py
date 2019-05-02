import socket
import msg

def client(server_addr):
    """Client - may not receive all the responses"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_addr)       # connect to server process

    sent_bytes = []
    recv_bytes = []
    for message in msg.msgs(20, max_length=2000):  # generate 20 msgs
        n_sent = sock.send(message)          # send message to server
        sent_bytes.append(n_sent)
        data = sock.recv(1024)      # receive response from server
        recv_bytes.append(len(data))
    sock.close()                    # send eof mark (FIN)

    print('sent {} times: {}'.format(len(sent_bytes), sum(sent_bytes)))
    print(sent_bytes)
    print('received {} times: {}'.format(len(recv_bytes), sum(recv_bytes)))
    print(recv_bytes)

if __name__ == '__main__':
    client(('np.hufs.ac.kr', 7))

