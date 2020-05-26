import json
import abc
import threading
import logging
import socket
import socketserver
from datetime import datetime
from typing import Mapping, Callable, Any, Optional, Tuple

Json = Mapping[Any, Any]
Responder = Callable[[Mapping[Any, Any]], Any]
logger = logging.getLogger('serviceit')


class Payload(dict):
    @classmethod
    def decode(cls, bts: bytes):
        payload = bts.decode('utf8')
        return json.loads(payload)
    def encode(self) -> bytes:
        return bytes(json.dumps(self), encoding='utf8')


class Handler(socketserver.BaseRequestHandler):

    def handle(self):
        logger.info("Received payload. Processing...")
        payload = Payload.decode(self.request.recv(4096))
        returned = self.receive(payload)
        if returned is not None:
            response = Payload(returned).encode()
            self.request.send(response)
            logger.info("Processed payload and replied.")
        else:
            logger.info("Processed payload : {}".format(payload))

    @abc.abstractmethod
    def receive(self, payload: Json) -> Optional[Json]:
        raise NotImplementedError()


class Server(socketserver.TCPServer):
    def __init__(self, server_address, RequestHandlerClass):
        super().__init__(server_address, RequestHandlerClass)
        self.last_processed = None
        self.payloads_processed = 0
        self.started_at = datetime.now()

    def finish_request(self, request, client_address):
        super().finish_request(request, client_address)
        self.last_processed = datetime.now()
        self.payloads_processed += 1


class Service:
    def __init__(self, receiver: Optional[Callable[[Json], None]], port: int, poll_interval: float = 0.1):
        class H(Handler):
            def receive(self, payload: Json):
                receiver(payload)
        self.poll_interval = poll_interval
        self._handler_class = H
        self._server_thread = None
        self.server = None
        self.client = None
        self.ip = 'localhost'
        self.port = port
        self.last_sent = None
        self.payloads_sent = 0
        self.bytes_sent = 0

    def start_server(self):
        server = Server((self.ip, self.port), self._handler_class)
        self.server = server
        self.ip, self.port = server.server_address
        self._server_thread = threading.Thread(target=server.serve_forever, kwargs=dict(poll_interval=self.poll_interval))
        self._server_thread.setDaemon(True)
        self._server_thread.start()
        logger.info("Started service at {}:{}.".format(self.ip, self.port))

    def start_client(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((self.ip, self.port))

    def send(self, data: Json) -> int:
        encoded = Payload(data).encode()
        ell = self.client.send(encoded)
        self.last_sent = datetime.now()
        logger.debug("Sent {} bytes".format(ell))
        self.payloads_sent += 1
        self.bytes_sent += ell
        return ell


class ServiceClient:
    def __init__(self, port: int):
        self._service = Service(None, port)
        self.port = self._service.port
        self._service.start_client()

    @property
    def payloads_sent(self) -> int:
        return self._service.payloads_sent

    @property
    def bytes_sent(self) -> int:
        return self._service.bytes_sent

    @property
    def last_sent(self) -> Optional[datetime]:
        if self._service.client is None: return None
        return self._service.last_sent

    def send(self, data: Json):
        self._service.send(data)


class ServiceServer:
    def __init__(self, receiver: Callable[[Json], None], port: int, poll_interval: float = 0.1):
        self._service = Service(receiver, port, poll_interval)
        self.port = self._service.port
        self._service.start_server()

    @property
    def started_at(self) -> datetime:
        return self._service.server.started_at

    @property
    def last_processed(self) -> Optional[datetime]:
        if self._service.server is None: return None
        return self._service.server.last_processed

    def payloads_processed(self) -> int:
        return self._service.server.payloads_processed

    def start_client(self):
        return ServiceClient(self.port)

__all__ = ['ServiceServer', 'ServiceClient', 'Json', 'Responder']
