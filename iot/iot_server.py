import socketserver, json, datetime
import logging

class IoTRequestHandler(socketserver.StreamRequestHandler):
    def handle(self):
        client = self.request.getpeername()
        logging.info("Client connecting: {}".format(client))
        for line in self.rfile:
            if not line:
                logging.warning('Client closing without request message: {}'.format(client))
                break
            request = json.loads(line[:-1].decode('utf-8'))
            logging.debug("{}: {}\n{}".format(client, datetime.datetime.now(), request))

            response = dict(status='OK', id=request['id'])
            response = json.dumps(response)
            self.wfile.write(response.encode('utf-8') + b'\n')
            logging.debug("%s" % response)
            # DB handling code here

        logging.info('Client closing: {}'.format(client))

# logging.basicConfig(filename='', level=logging.INFO)
logging.basicConfig(filename='', level=logging.DEBUG)

Handler = IoTRequestHandler
PORT = 51111

with socketserver.ThreadingTCPServer(("", PORT), IoTRequestHandler) as server:
    print("serving at port", PORT)
    server.serve_forever()

