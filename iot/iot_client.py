"""
We define IoT Protocol messages as a Python dict.
They should be converted into JSON format string,
and serialized by utf-8 enconding in order to communicate via TCP socket.
Each message should be terminaed by new line character (b'\n')
in a TCP session.

POST message exchange
    Request:
    {   'method': 'POST'
        'id': IOT id (str),
        'data': dict of sensors' data }

    Response:
    {   'status': 'OK' or 'ERROR',
        'id': requesting IoT id }

POLL message exchange
    Request:
    {   'method': 'POLL',
        'id': IOT id (str) }

    Response:
    {   'status': 'OK' or 'ERROR',
        'id': requesting IoT id,
        # Control field can be omitterd if no more control needed.
        # Define yourself!
        'control': {'ON': 'aircon', 'OFF': 'LED'}  }
"""

import socket, json, time, random, sys

def read_sensors(interval=1.5):
    """
    Read from sensors

    :param interval: sensing interval in seconds
    :return: dict containing sensors' data
    """

    time.sleep(interval)
    # Get values from the sensors
    temperature = random.randint(15, 40)
    humidity = random.randint(30, 90)
    data = {'temperature': temperature, 'humidity': humidity}
    return data

def client(server_addr, iot_id):
    """IoT client with persistent connection
    Each message separated by b'\n'

    :param server_addr: (host, port)
    :param iot_id: id of this IoT
    """

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_addr)  # connect to server process
    in_file = sock.makefile('rb')  # file-like obj

    # Report sensors' data forever
    while True:
        data = read_sensors()
        request = dict(method='POST', id=iot_id, data=data)
        print(request)
        request_bytes = json.dumps(request).encode('utf-8') + b'\n'
        sock.sendall(request_bytes)

        response_bytes = in_file.readline()     # receive response
        if not response_bytes:
            print('Server abnormally terminated')
            sock.close()
            exit(1)
        response = json.loads(response_bytes[:-1].decode('utf-8'))
        print(response)
    sock.close()       # never reach here

if __name__ == '__main__':
    if len(sys.argv) == 3:
        host, port = sys.argv[1].split(':')
        iot_id = sys.argv[2]
    elif len(sys.argv) == 2:
        host, port = 'localhost', '51111'
        iot_id = sys.argv[1]
    else:
        print('Usage: {} [host:port] iot_id'.format(sys.argv[0]))
        sys.exit(1)

    client((host, int(port)), iot_id)
