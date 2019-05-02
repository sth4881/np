"""Iterative echo server"""
import sys
from socket import *

def echo_server(my_port):   
    """Echo server (iterative)"""
    try:
        sock = socket(AF_INET, SOCK_STREAM) # make listening socket
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1) # Reuse port number if used
        sock.bind(('', my_port))        # bind it to server port number
        sock.listen(5)                  # listen, allow 5 pending connects
    except OSError as e:
        print('socket error', e)
        sock.close()
        sys.exit(1)
    else:
        print('Server started')

    while True:                     # do forever (until process killed)
        conn, cli_addr = sock.accept()  # wait for next client connect
                                    # conn: new socket, addr: client addr
        print('Connected by', cli_addr)
        try:
            while True:
                data = conn.recv(1024)  # recv next message on connected socket
                if not data: break      # eof when the socket closed
                print('Server received:', data.decode())
                conn.send(data)         # send a reply to the client
        except OSError as e:              # socket.error exception
            print('socket error:', e)
        except Exception as e:
            print('Exception:', e)
        else:
            print('Client closed', cli_addr) # This client normally terminated.
        finally:
            conn.close()                # close the connected socket
        
if __name__ == '__main__':
    echo_server(50007)

