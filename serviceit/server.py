"""
Main code for service-it.
Contains the ``ServiceClient`` and ``ServiceServer`` classes.
"""
from __future__ import annotations
import json
import abc
import threading
import logging
import socket
import socketserver
from datetime import datetime
from typing import Mapping, Callable, Any, Optional, Tuple, Type

Json = Mapping[Any, Any]
Responder = Callable[[Mapping[Any, Any]], Optional[Json]]
logger = logging.getLogger("serviceit")


class Payload(dict):
    """
    A JSON payload.
    """

    @classmethod
    def decode(cls, bts: bytes) -> Payload:
        payload = bts.decode("utf8")
        try:
            return Payload(json.loads(payload))
        except json.decoder.JSONDecodeError:
            logger.error("Failed on payload: {}".format(payload))
            raise

    def encode(self) -> bytes:
        return bytes(json.dumps(self), encoding="utf8")


class Handler(socketserver.BaseRequestHandler):
    def handle_inner(self) -> bytes:
        req = self.request.recv(4096)
        if len(req) == 0:
            logger.debug("Received an empty payload.")
            return req
        logger.info("Received payload of {} bytes. Processing...".format(len(req)))
        payload = Payload.decode(req)
        returned = self.receive(payload)
        logger.debug("Payload was {}".format(payload))
        logger.debug("Responding with {}".format(returned))
        if returned is not None:
            response = Payload(returned).encode()
            self.request.send(response)
            logger.info("Processed payload and replied.")
        else:
            logger.info("Processed payload.")
        return req

    @abc.abstractmethod
    def receive(self, payload: Json) -> Optional[Json]:
        raise NotImplementedError()


class Server(socketserver.ThreadingTCPServer):
    # noinspection PyAbstractClass
    def __init__(self, server_address, handler_class: Type[Handler]):
        self.bytes_processed = [0]

        class MyHandler(handler_class):
            # noinspection PyMethodParameters
            def handle(inner_self):
                req = inner_self.handle_inner()
                self.bytes_processed[0] += len(req)

        super().__init__(server_address, MyHandler)
        self.last_received = None
        self.last_processed = None
        self.payloads_received = 0
        self.payloads_processed = 0
        self._first = False
        self.started_at = datetime.now()

    def process_request(self, request, client_address: Tuple[str, int]) -> None:
        # this is a very weird workaround
        # but the first call seems to make two requests
        if self._first:
            self.payloads_received += 1
            self.last_received = datetime.now()
        super().process_request(request, client_address)
        if not self._first:
            self._first = True
        else:
            self.payloads_processed += 1
            self.last_processed = datetime.now()

    def handle_error(self, request, client_address):
        logger.error("Failed processing request from {}".format(client_address), exc_info=True)


class ServiceClient:
    """
    A socket to a socketserver (``ServiceServer``) that receives JSON payloads.
    See ``serviceit.client`` for more info.
    """

    def __init__(
        self, port: int, socket_family: int = socket.AF_INET, socket_type: int = socket.SOCK_STREAM
    ):
        """
        Opens a new socket.
        Refer to ``serviceit.client``.

        Args:
            port: The port to send payloads. Must be a positive integer.
            socket_family: A bit flag. See the constructor for ``socket.socket``.
            socket_type: A bit flag. See the constructor for ``socket.socket``.
        """
        self.ip = "localhost"
        self.port = port
        self._last_sent = None
        self._payloads_sent = 0
        self._bytes_sent = 0
        self._socket = socket.socket(socket_family, socket_type)
        self._connect()
        self._open = True

    @property
    def payloads_sent(self) -> int:
        """
        Get N payloads sent.

        Returns:
            The number of payloads sent. Always up-to-date.
        """
        return self._payloads_sent

    @property
    def bytes_sent(self) -> int:
        """
        Get N bytes sent.

        Returns:
            The number of bytes sent. Always up-to-date.
        """
        return self._bytes_sent

    @property
    def last_sent(self) -> Optional[datetime]:
        """
        Get datetime of last packet.

        Returns:
            The datetime when the last packet was sent, or None if none were sent. Always up-to-date.
        """
        return self._last_sent

    def send(self, data: Json) -> None:
        """
        Sends a JSON payload to the server.

        Args:
            data: An arbitrary dict (Any to Any).
                  If you have a list (``[ {} ]``), loop and send each element instead.
        """
        self._connect()
        encoded = Payload(data).encode()
        self._socket.send(encoded)
        self._last_sent = datetime.now()
        logger.debug("Sent {} bytes".format(len(encoded)))
        self._payloads_sent += 1
        self._bytes_sent += len(encoded)

    def receive(self) -> Optional[Json]:
        """
        Reads data sent back from the server.
        WARNING: This may be out-of-order.
        WARNING: Be careful with this method, which may block.

        Returns:

            The response received as a dict (Any to Any).
        """
        rec = self._socket.recv(4096)
        if len(rec) == 0:
            return None
        else:
            return Payload.decode(rec)

    @property
    def is_open(self) -> bool:
        """
        Return whether this socket is open.

        Returns:
            Whether ``self.close()`` was called.
            It's possible for the socket to be closed even if this returns ``True``.
        """
        return self._open

    def close(self) -> None:
        """
        Closes this socket.
        """
        self._socket.close()
        self._open = False

    def _connect(self):
        self._socket.close()
        self._open = False
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((self.ip, self.port))
        self._open = True

    def __repr__(self) -> str:
        """
        Returns a representation string, which has the memory address.
        """
        return "{}@{}:{}:{}(sent={} @ {})".format(
            self.__class__.__name__,
            self.ip,
            self.port,
            "open" if self._open else "closed",
            self.payloads_sent,
            hex(id(self)),
        )

    def __str__(self) -> str:
        """
        Returns a human-readable string.
        """
        return "{}@{}:{}:{}(sent={})".format(
            self.__class__.__name__,
            self.ip,
            self.port,
            "open" if self._open else "closed",
            self.payloads_sent,
        )


class ServiceServer:
    """
    A socketserver that receives JSON payloads.
    See ``serviceit.server`` for more info.
    """

    def __init__(
        self,
        receiver: Optional[Callable[[Json], Optional[Json]]],
        port: int,
        poll_interval: float = 0.001,
    ):
        """
        Creates a new ``ServiceServer``, which listens on a new thread and spawns an additional thread per request.
        Refer to ``serviceit.server``.
        """

        class H(Handler):
            def receive(self, payload: Json):
                receiver(payload)

        ip = "localhost"
        self.poll_interval = poll_interval
        self._handler_class = H
        self._server = Server((ip, port), self._handler_class)
        self.ip, self.port = self._server.server_address
        self._server_thread = threading.Thread(
            target=self._server.serve_forever, kwargs=dict(poll_interval=poll_interval)
        )
        self._server_thread.setDaemon(True)
        self._server_thread.start()
        self._open = True
        logger.info("Started service at {}:{}.".format(self.ip, self.port))

    @property
    def started_at(self) -> datetime:
        """
        Get when the server started.

        Returns:
            The datetime the server was created.
        """
        return self._server.started_at

    @property
    def last_received(self) -> Optional[datetime]:
        """
        Get when the last packet was received.

        Returns:
            The datetime of the last payload received and retrieved by polling, or None if no payloads were received.
            This value is not guaranteed to be up-to-date, since the statistic lives on another thread.
        """
        return self._server.last_received

    @property
    def last_processed(self) -> Optional[datetime]:
        """
        Get when the last package finished processing.

        Returns:
            The datetime of the last payload for which processing finished, or None if no payloads were processed.
            This value is not guaranteed to be up-to-date, since the statistic lives on another thread.
        """
        return self._server.last_processed

    @property
    def payloads_received(self) -> int:
        """
        Get the total N payloads received.

        Returns:
            The number of JSON payloads received and retrieved by polling.
            This number is not guaranteed to be up-to-date, since the statistic lives on another thread.
        """
        return self._server.payloads_received

    @property
    def payloads_processed(self) -> int:
        """
        Get the total N payloads processed.

        Returns:
            The number of JSON payloads for which processing finished.
            This number is not guaranteed to be up-to-date, since the statistic lives on another thread.
        """
        return self._server.payloads_processed

    @property
    def bytes_processed(self) -> int:
        """
        Get the total N bytes processed.

        Returns:
            The number of bytes processed.
            This number is not guaranteed to be up-to-date, since the statistic lives on another thread.
            In practice, it seems to lag behind ``payloads_processed``.
        """
        return self._server.bytes_processed[0]

    def client(self) -> ServiceClient:
        """
        Opens a socket to this server.
        In general, you would want to get a client from somewhere without access to this ``ServiceServer``.
        In some ways, this method is a little pointless, but it's useful for testing.

        Returns:
            A new ``ServiceClient`` instance.
        """
        return ServiceClient(self.port)

    @property
    def is_open(self) -> bool:
        """
        Returns whether the socket is open.

        Returns:
            In theory, whether this server is accepting connections.
            Specifically, whether ``self.close()`` was called.
            In practice, this may be out-of-date, and the server may have died in other ways.
        """
        return self._open

    def close(self) -> None:
        """
        Shuts down this server, closing the connect.
        WARNING: Currently does not stop the polling thread.
        """
        self._open = False
        self._server.shutdown()
        # TODO
        # self._server_thread.

    def __repr__(self) -> str:
        """
        Returns a representation string, which has the memory address.
        """
        return "{}@{}:{}:{}(started={},processed={} @ {})".format(
            self.__class__.__name__,
            self.ip,
            self.port,
            "open" if self._open else "closed",
            self.started_at,
            self.payloads_processed,
            hex(id(self)),
        )

    def __str__(self) -> str:
        """
        Returns a human-readable string.
        """
        return "{}@{}:{}:{}(started={},processed={})".format(
            self.__class__.__name__,
            self.ip,
            self.port,
            "open" if self._open else "closed",
            self.started_at,
            self.payloads_processed,
        )


__all__ = ["ServiceServer", "ServiceClient", "Json", "Responder"]
