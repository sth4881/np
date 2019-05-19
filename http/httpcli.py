import socket
import logging
from urllib.request import urlparse
from requests.structures import CaseInsensitiveDict

logging.basicConfig(level=logging.DEBUG)

class Response:
    def __init__(self):
        self.status_code = None
        self.content = bytearray()
        self.headers = CaseInsensitiveDict()
        self.encoding = 'UTF-8'  # default


class Request:
    template = '{method} {path} HTTP/1.1\r\n{headers}\r\n'

    def __init__(self, url, data=None, headers={}):
        self.method = 'POST' if data else 'GET'
        self.full_url = url
        self.data = data
        self.headers = CaseInsensitiveDict()

        r = urlparse(self.full_url)
        self.path = r.path if r.path else '/'
        if r.params:
            self.path += ';' + r.params
        if r.query:
            self.path += '?' + r.query
        self.headers['Host'] = r.hostname
        self.headers['Agent'] = 'httpopen'
        self.headers['Accept'] = '*/*'
        self.headers['Connection'] = 'close'
        for key, value in headers.items():
            self.headers[key] = value
        if self.data:
            if not self.headers.get('content-type', None):
                raise ValueError('No Content-type header specified')
            self.headers['content-length'] = str(len(self.data))

        headers_list = [key + ': ' + value for key, value in self.headers.items()]
        headers_str = '\r\n'.join(headers_list) + '\r\n'
        self.message = self.template.format(method=self.method, path=self.path, headers=headers_str)


def httpopen(url, data=None):
    def read_headers(file, headers):
        for line in file:
            if line == b'\r\n':  # end of headers
                break
            header = line.decode().strip()  # remove leading and trailing white spaces
            key, value = header.split(':', maxsplit=1)
            headers[key] = value.strip()

    if isinstance(url, Request):
        request = url
    elif isinstance(url, str):
        request = Request(url, data)
    r = urlparse(request.full_url)
    if r.scheme != 'http':
        raise NotImplementedError('{}: not implemented'.format(r.scheme))
    logging.debug('Request message:\n{}'.format(request.message))

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_addr = r.hostname, r.port if r.port else 80
    sock.connect(server_addr)
    rfile = sock.makefile('rb')

    sock.sendall(request.message.encode('utf-8'))
    if request.data:
        sock.sendall(request.data)

    response = Response()
    # read status line
    response.status_code = int(rfile.readline().decode('utf-8').split()[1])
    logging.debug('status code: {}'.format(response.status_code))
    # read headers
    read_headers(rfile, response.headers)
    logging.debug('Response headers:\n{}'.format(response.headers))

    # read contents
    ## Content-length specified:
    if response.headers.get('Content-length', None):    # Content-length header exists
        response.content = rfile.read(int(response.headers['Content-length']))
    ## Chunked transfer specified: chunk represented as hexa string + CRLF
    elif response.headers.get('Transfer-Encoding', None) == 'chunked': # chunked transfer
        while True:
            content_length = int(rfile.readline().decode('utf-8').strip(), 16)
            if content_length == 0:
                break
            chunk = rfile.read(content_length)
            response.content.extend(chunk)
            rfile.readline()
        rfile.readline()        # skip CRLF
    ## nothing specified:
    else:
        response.content = rfile.read()         # read until FIN arrival

    if response.status_code >= 400:             # HTTP error response
        logging.warning(response.content)
        response.content = None

    rfile.close()
    sock.close()
    return response

# GET method - chunked transfer
url = 'http://mclab.hufs.ac.kr/wiki/Lectures/IA/2019#Python_Network_Programming'
response = httpopen(url)
print('content:')
print(response.content[:400])

# Test POST method with JSON data
import json
url = 'http://httpbin.org/post'     # simple HTTP Request & Response Service.
conditions =  {"con1":40, "con2":20, "con3":99, "con4":40, "password":"1234"}
data = json.dumps(conditions).encode('utf-8')
request = Request(url, data=data, headers={'content-type': 'application/json'})
# end of POST
response = httpopen(request)
print('content:')
print(response.content)
if response.headers.get('content-type') == 'application/json':
    text = json.loads(response.content.decode('utf-8'))
    print('decoded json contents:')
    print(text)
