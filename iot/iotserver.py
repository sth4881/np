import socketserver, json
import logging

class IoTRequestHandler(socketserver.StreamRequestHandler):
    def handle(self):
        client = self.request.getpeername()
        logging.info("Client connecting: {}".format(client))

        for line in self.rfile:
            try:
                request = json.loads(line.decode('utf-8'))
            except ValueError as e:
                error_msg = '{}: json decoding error'.format(e)
                status = 'ERROR {}'.format(error_msg)
                response = dict(status=status, deviceid=request.get('deviceid'),
                                msgid=request.get('msgid'))
                response = json.dumps(response)
                self.wfile.write(response.encode('utf-8') + b'\n')
                logging.error(error_msg)
                break
            else:
                status = 'OK'
                logging.debug("{}:{}".format(client, request))

            # Insert request into DB
            pass

            # activate actuators if necessary to control
            activate = {}
            data = request.get('data')
            if data:
                temperature = float(data.get('temperature'))
                humidity = float(data.get('humidity'))
                if (temperature >= 32 and humidity >= 70) \
                    or (temperature >= 34) \
                    or (temperature >= 30 and humidity >= 90):
                    activate['aircon'] = 'ON'
                elif (temperature < 28 or humidity < 50):
                    activate['aircon'] = 'OFF'
            # reply response message
            response = dict(status=status, deviceid=request.get('deviceid'),
                            msgid=request.get('msgid'))
            if activate:
                response['activate'] = activate
            response = json.dumps(response)
            self.wfile.write(response.encode('utf-8') + b'\n')
            logging.debug("%s" % response)
            # DB handling code here

        logging.info('Client closing: {}'.format(client))

# logging.basicConfig(filename='', level=logging.INFO)
logging.basicConfig(filename='', level=logging.DEBUG,
                    format='%(asctime)s:%(levelname)s:%(message)s')

serv_addr = ("", 10007)
with socketserver.ThreadingTCPServer(serv_addr, IoTRequestHandler) as server:
    logging.info('Server starts: {}'.format(serv_addr))
    server.serve_forever()

