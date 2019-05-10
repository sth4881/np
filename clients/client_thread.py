import socket, threading
import msg

sent_bytes = []
recv_bytes = []

def recv_loop(in_file):
    print('recv thread started')
    while True:
        data = in_file.readline()     # receive response
        if not data:
            print('Server closing')
            break
        recv_bytes.append(len(data))
    print('received {} times: {}'.format(len(recv_bytes), sum(recv_bytes)))
    print('recv byte:', recv_bytes)
    print('recv thread exiting.')
   
def client(server_addr):
    """Client implementation by the sending and receiving threads
    """

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_addr)         # connect to server process
    in_file = sock.makefile('rb')     # file-like obj 
    out_file = sock.makefile('wb')    # file-like obj

    receiver = threading.Thread(target=recv_loop, args=(in_file,))
    receiver.start()    # start recv_loop thread

    # main thread continues hereafter
    for message in msg.msgs(20, length=2000):
        out_file.write(message)       # buffered
        sent_bytes.append(len(message))
    out_file.flush()              # flush-out buffer
    sock.shutdown(socket.SHUT_WR)     # send FIN. This will stop receiver thread
    print('sent: {}'.format(sum(sent_bytes)))

    receiver.join()                   # wait for receiver exit
    sock.close()
    print('Client terminated')
    msg.report(sent_bytes, recv_bytes)

if __name__ == '__main__':
    client(('np.hufs.ac.kr', 7))
