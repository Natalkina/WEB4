import urllib.parse
import pathlib
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import socket
from datetime import datetime
import logging
from threading import Thread


BASE_DIR = pathlib.Path()
SOCKET_IP = '127.0.0.1'
HTTP_IP = '0.0.0.0'
SOCKET_PORT = 5000
HTTP_PORT = 3000
BUFFER_SIZE = 1024

def send_data_to_socket(data):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(data, (SOCKET_IP, SOCKET_PORT))
    sock.close()

class TheBestFastApp(BaseHTTPRequestHandler):
    def do_POST(self):
        length = self.headers.get('Content-Length')
        data = self.rfile.read(int(length))
        send_data_to_socket(data)
        self.send_response(302)
        self.send_header('Location', '/message')
        self.end_headers()

    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        print(route.path)
        match route.path:
            case '/':
                self.send_html('index.html')
            case '/message':
                self.send_html('message.html')
            case _:
                file = BASE_DIR.joinpath(route.path[1:])
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html('error.html', 404)

    def send_html(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self, filename, status_code=200):
        self.send_response(status_code)
        mt = mimetypes.guess_type(filename)
        if mt:
            self.send_header('Content-type', mt[0])
        else:
            self.send_header('Content-type', 'text/plain')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())


def save_data_from_http_server(data):
    storage_dir = pathlib.Path().joinpath('storage')
    if not storage_dir.exists():
        storage_dir.mkdir()

    storage_file = storage_dir / 'data.json'
    if storage_file.exists():
        log = json.load(open(storage_file))
    else:
        log = {}

    msg_time = datetime.now()

    parse_data = urllib.parse.unquote_plus(data.decode())
    dict_parse = {key: value for key, value in [el.split('=') for el in parse_data.split('&')]}
    log[str(msg_time)] = dict_parse

    try:
        with open('storage/data.json', 'w', encoding='utf-8') as fd:
            json.dump(log, fd, ensure_ascii=False, indent=4)
    except ValueError as err:
        logging.debug(f"for data {parse_data} error: {err}")
    except OSError as err:
        logging.debug(f"Write data {parse_data} error: {err}")



def run_http(ip, port):

    httpd = HTTPServer((ip, port), TheBestFastApp)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()


def run_socket(ip, port):

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((ip, port))

    try:
        while True:
            message, address = sock.recvfrom(1024)
            save_data_from_http_server(message)
    except KeyboardInterrupt:
        print(f'Destroy server')
    finally:
        sock.close()


if __name__ == '__main__':

    th_server = Thread(target=run_http, args=(HTTP_IP,HTTP_PORT))
    th_server.start()

    th_socket = Thread(target=run_socket, args=(SOCKET_IP, SOCKET_PORT))
    th_socket.start()

