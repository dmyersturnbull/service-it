"""
Metadata for service-it.
"""

import socket
from pathlib import Path
import logging
from typing import Callable, Mapping, Any

# importlib.metadata is compat with Python 3.8 only
from importlib_metadata import PackageNotFoundError, metadata as __load

from serviceit.server import ServiceServer, ServiceClient, Responder

logger = logging.getLogger('serviceit')

try:
    metadata = __load(Path(__file__).parent.name)
    __status__ = "Development"
    __copyright__ = "Copyright 2020"
    __date__ = "2020-05-25"
    __uri__ = metadata["home-page"]
    __title__ = metadata["name"]
    __summary__ = metadata["summary"]
    __license__ = metadata["license"]
    __version__ = metadata["version"]
    __author__ = metadata["author"]
    __maintainer__ = metadata["maintainer"]
    __contact__ = metadata["maintainer"]
except PackageNotFoundError:
    logger.error("Could not load metadata for serviceit")

def server(port: int, receiver: Responder) -> ServiceServer:
    service = ServiceServer(receiver, port)
    return service

def client(port: int) -> ServiceClient:
    if port == 0:
        raise ValueError("Cannot use port==0 (let kernel choose) when creating a client")
    return ServiceClient(port)
