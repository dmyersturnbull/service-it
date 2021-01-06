"""
Metadata for service-it.
"""

from pathlib import Path
import logging

from importlib.metadata import PackageNotFoundError
from importlib.metadata import metadata as __load

from serviceit.server import ServiceServer, ServiceClient, Responder

pkg = Path(__file__).absolute().parent.name
logger = logging.getLogger(pkg)
_metadata = None
try:
    metadata = __load(Path(__file__).absolute().parent.name)
    __status__ = "Development"
    __copyright__ = "Copyright 2020–2021"
    __date__ = "2020-08-24"
    __uri__ = metadata["home-page"]
    __title__ = metadata["name"]
    __summary__ = metadata["summary"]
    __license__ = metadata["license"]
    __version__ = metadata["version"]
    __author__ = metadata["author"]
    __maintainer__ = metadata["maintainer"]
    __contact__ = metadata["maintainer"]
except PackageNotFoundError:
    logger.error("Could not load metadata for serviceit. Is it not installed?")


def server(port: int, receiver: Responder, poll_interval: float = 0.001) -> ServiceServer:
    """
    Starts a new threaded socketserver on localhost that accepts JSON.
    The server will run on a new thread (python ``threading``), daemonized, and will spawn a new thread per request.

    Args:
        port: If 0, lets the kernel choose the port, which will then be accessible with ``my_server.port``.
        receiver: A function that receives JSON as a dict, processes the request.
                  May return ``None`` or a dict (Any to Any), which will be sent back to the client.
                  Note that the client will not be able to tell which packet packet the server is responding to.
                  In fact, it may even be from a different client.
                  Therefore, you should always include the original payload or a hash of it.
                  A good choice might be ``return dict(success=True, payload=payload)``.
                  The server will log requests, so there's no need to do that in ``receiver``.
        poll_interval: How often the server should poll for new payloads, in seconds

    Returns:
        A ``ServiceServer`` instance.
        It needs to be kept intact while the server accepts requests. Be nice to it.
        It will record statistics, including the number of payloads received and processed,
        and the number of bytes processed.
    """
    return ServiceServer(receiver, port, poll_interval=poll_interval)


def client(port: int) -> ServiceClient:
    """
    Opens a socket to the specified port on localhost.
    To work around problems, the socket will be closed and reopened per request.

    Args:
        port: The port on localhost. It must be a positive integer.

    Returns:
        A ``ServiceClient`` instance.
        You can call ``client.send(dictionary)`` to send JSON payloads.
        It will record statistics, including the number of payloads and bytes sent.
    """
    if port == 0:
        raise ValueError("Cannot use port==0 (let kernel choose) when creating a client")
    return ServiceClient(port)


__all__ = ["ServiceServer", "ServiceClient", "Responder", "server", "client"]
