import json
import abc
import threading
import logging
import socket
import socketserver
from typing import Mapping, Callable, Any

logger = logging.getLogger('serviceit')


class Handler(socketserver.BaseRequestHandler):

    def handle(self):
        payload = str(self.request.recv(4096), 'utf8').strip()
        payload = json.loads(payload)
        logger.info("Received payload. Processing...")
        self.receive(payload)
        logger.info("Processed payload.")

    def receive(self, payload: Mapping[Any, Any]):
        raise NotImplementedError()


class Server(socketserver.TCPServer):
    pass


class Service:
    def __init__(self, receiver: Callable[[Mapping[Any,Any]], None], port: int, daemon: bool = False):
        class H(Handler):
            def receive(self, payload: Mapping[Any,Any]):
                receiver(payload)
        self._handler_class = H
        self._port = port
        with socketserver.TCPServer(('localhost', port), H) as server:
            self._server_thread = threading.Thread(target=server.serve_forever)
            self._server_thread.daemon = daemon
            self._server_thread.start()

    def send(self, data: Mapping[Any, Any]):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(('localhost', self._port))
            sock.sendall(bytes(data))
