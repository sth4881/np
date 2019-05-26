"""
We may define IoT Protocol messages as Python dicts.
They are serialized as JSON format string, then encoded in utf-8.
Because every messages are delimeted by new line character (b'\n') in a TCP session,
avoid using LF character inside Python strings.

The POLL request messages are sent periodically
for server to inform the client to activate actuators if needed.

<request message> ::= <POST request message> | <POLL request message>
<response message> ::= <POST response message> | <POLL response message>

<POST request message> ::=
    {   'method': 'POST',
        'deviceid': <device id>,
        'data': <sensor data>
    } <LF>

<POST response message> ::=
    {   'status': 'OK' | 'ERROR <error msg>',
        'deviceid': <device id>
    } <LF>

<POLL request message> ::=
    {   'method': 'POLL',
        'deviceid': <device id>
    } <LF>

<POLL response message>:
    {   'status': 'OK' | 'DO' | 'ERROR <error msg>',
        'deviceid': <device id>
        'activate': {
                        'aircon': 'ON',
                        'led': 'OFF',
                        ...
                    }
    } <LF>
"""

import socket, json, time, random, sys
import selectors, uuid

def read_sensors():
    """
    Read from sensors

    :param interval: sensing interval in seconds
    :return: dict containing sensors' data
    """

    # Get values from the sensors
    temperature = random.randint(15, 40)
    humidity = random.randint(30, 90)
    data = {'temperature': temperature, 'humidity': humidity}
    return data

class IoTClient:
    def __init__(self, server_addr, deviceid):
        """IoT client with persistent connection
        Each message separated by b'\n'

        :param server_addr: (host, port)
        :param deviceid: id of this IoT
        """

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(server_addr)  # connect to server process
        rfile = sock.makefile('rb')  # file-like obj
        sel = selectors.DefaultSelector()
        sel.register(sock, selectors.EVENT_READ)

        self.sock = sock
        self.rfile = rfile
        self.deviceid = deviceid
        self.sel = sel
        self.requests = {}      # messages sent but not yet received their responses
        self.time_to_expire = None

    def select_periodic(self, interval):
        """Wait for ready events or time interval.
        Timeout event([]) occurs every interval, periodically.
        """
        now = time.time()
        if self.time_to_expire is None:
            self.time_to_expire = now + interval
        timeout_left = self.time_to_expire - now
        if timeout_left > 0:
            events = self.sel.select(timeout=timeout_left)
            if events:
                return events
        # time to expire elapsed or timeout event occurs
        self.time_to_expire += interval # set next time to expire
        return []


    def run(self):
        # Report sensors' data forever
        try:
            while True:
                events = self.select_periodic(interval=0.001)
                if not events:      # timeout occurs
                    data = read_sensors()
                    msgid = str(uuid.uuid1())
                    request = dict(method='POST', deviceid=self.deviceid, msgid=msgid, data=data)
                    print(time.time(), request)
                    request_bytes = json.dumps(request).encode('utf-8') + b'\n'
                    self.sock.sendall(request_bytes)
                    self.requests[msgid] = request_bytes
                else:               # EVENT_READ
                    response_bytes = self.rfile.readline()     # receive response
                    if not response_bytes:
                        self.sock.close()
                        raise OSError('Server abnormally terminated')
                    response = json.loads(response_bytes.decode('utf-8'))
                    print(response)
                    msgid = response.get('msgid')
                    if msgid and msgid in self.requests:
                        del self.requests[msgid]
                    else:
                        print('{}: illegal msgid received. Ignored'.format(msgid))
        except Exception as e:
            print('{}: client terminated'.format(e))
        finally:
            self.sock.close()

if __name__ == '__main__':
    # if len(sys.argv) == 3:
    #     host, port = sys.argv[1].split(':')
    #     deviceid = sys.argv[2]
    # else:
    #     print('Usage: {} host:port iot_id '.format(sys.argv[0]))
    #     sys.exit(1)

    client = IoTClient(('np.hufs.ac.kr', 7), deviceid=100)
    client.run()
