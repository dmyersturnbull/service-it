"""
Metadata for service-it.
"""

import socket
from pathlib import Path, PurePath
from typing import Callable, Mapping, Any, Union

# importlib.metadata is compat with Python 3.8 only
from importlib_metadata import metadata as __load

from serviceit.server import Service

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


def resource(*nodes: Union[PurePath, str]) -> Path:
    """Gets a path of a resource file under resources/ directory."""
    return Path(Path(__file__).parent, "resources", *nodes)


def create(port: int, receiver: Callable[[Mapping[Any,Any]], None], daemon: bool = False):
    service = Service(receiver, port, daemon=daemon)
    return service

def send(port: int, data: Mapping[Any, Any]):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(('localhost', port))
        sock.sendall(bytes(data))
