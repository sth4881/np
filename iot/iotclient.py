"""
We may define IoT Protocol messages as Python dicts.
They are serialized as JSON format string, then encoded in utf-8.
Because every messages are delimited by new line character (b'\n') in a TCP session,
avoid using LF character inside Python strings.

The POST request messages might be sent periodically
for server to inform the client to activate the actuators if needed.

<request message> ::=
    {   'method': 'POST',
        'deviceid': <device id>,
        'msgid': <messge id>,
        'data': {'temperature': 28.5, 'humidity': 71},
    } <LF>

<response message with activate>:
    {   'status': 'OK' | 'DO' | 'ERROR <error msg>',
        'deviceid': <device id>
        'msgid': <messge id>
      [ 'activate': {'aircon': 'ON', 'led': 'OFF' } ]
    } <LF>
"""

import socket, json, time, sys
import selectors, uuid
import random, math
import logging


def gen_data(mean, deviation, samples=100):
    """Simulate reading sensor's data, adding noise to sine curve.

    :param mean: mean of sine curve
    :param deviation: deviation of sine curve
    :param samples: total number of samples to be generated
    :return: sensor data (float)
    """

    # Get values from the sensors
    Fs = samples
    f = 1
    for t in range(samples):
        signal = deviation * math.sin(2 * math.pi * f * t / Fs) + mean
        noise = random.gauss(mu=deviation / 4, sigma=deviation / 4)
        measured = signal + noise
        yield measured

def ewma(generator, alpha=0.25):
    """Exponential weighted moving average

    :param generator: iterables including touples, lists, and generators
    :return: smoothed data
    """
    s = None
    for y in generator:
        if s:
            s = alpha*y + (1-alpha)*s
        else:
            s = y
        yield s

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
        gen_temp = ewma(gen_data(mean=20, deviation=20, samples=20))
        gen_humid = ewma(gen_data(mean=50, deviation=15, samples=20))
        msgid = 0

        while True:
            try:
                events = self.select_periodic(interval=5)
                if not events:      # timeout occurs
                    try:
                        temperature = next(gen_temp)
                        humidity = next(gen_humid)
                    except StopIteration:
                        logging.info('No more sensor data to send')
                        break
                    data = dict(temperature=temperature, humidity=humidity)
                    # msgid = str(uuid.uuid1())
                    msgid += 1
                    request = dict(method='POST', deviceid=self.deviceid, msgid=msgid, data=data)
                    logging.debug(request)
                    request_bytes = json.dumps(request).encode('utf-8') + b'\n'
                    self.sock.sendall(request_bytes)
                    self.requests[msgid] = request_bytes
                else:               # EVENT_READ
                    response_bytes = self.rfile.readline()     # receive response
                    if not response_bytes:
                        self.sock.close()
                        raise OSError('Server abnormally terminated')
                    response = json.loads(response_bytes.decode('utf-8'))
                    logging.debug(response)
                    msgid = response.get('msgid')
                    if msgid and msgid in self.requests:
                        del self.requests[msgid]
                    else:
                        logging.warning('{}: illegal msgid received. Ignored'.format(msgid))
            except (ValueError, OSError) as e:
                logging.error(e)
                break
            except Exception as e:
                logging.error(e)
                break

        logging.info('client terminated')
        self.sock.close()

if __name__ == '__main__':
    if len(sys.argv) == 3:
        host, port = sys.argv[1].split(':')
        port = int(port)
        deviceid = sys.argv[2]
    else:
        print('Usage: {} host:port iot_id '.format(sys.argv[0]))
        sys.exit(1)

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s:%(levelname)s:%(message)s')
    client = IoTClient((host, port), deviceid)
    client.run()
