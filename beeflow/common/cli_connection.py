"""Special connection for communicating with cli.py."""
from contextlib import contextmanager
import socket
import os
import traceback

import jsonpickle


class BeeflowConnectionError(Exception):
    """Connection error class."""

    def __init__(self):
        """Create a new connection error class."""


class Server:
    """Socket server for use in cli.py."""

    def __init__(self, s):
        """Create a new server."""
        self.s = s

    def accept(self):
        """Accept a new connection or return None."""
        try:
            conn, _ = self.s.accept()
            return ClientConnection(conn)
        except BlockingIOError:
            # No clients right now
            return None


class ClientConnection:
    """Connection to a client from the server end."""

    def __init__(self, conn):
        """Create a new connection."""
        self.conn = conn
        self.conn.setblocking(False)

    def get(self):
        """Get and return the message."""
        try:
            return _recv_message(self.conn)
        except (ConnectionResetError, OSError) as err:
            traceback.print_exc()
            print(err)
            raise BeeflowConnectionError() from err

    def put(self, msg):
        """Put a response message (closes the socket when done)."""
        try:
            _send_message(self.conn, msg)
            self.conn.close()
        except (ConnectionResetError, OSError) as err:
            traceback.print_exc()
            raise BeeflowConnectionError() from err


@contextmanager
def server(path):
    """Create a new server connection."""
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.bind(path)
            s.listen(1)
            s.setblocking(False)
            yield Server(s)
    finally:
        # Need to remove the socket when done
        os.remove(path)


def send(path, msg):
    """Send a single message to the server and get a response."""
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        try:
            s.connect(path)
        except (FileNotFoundError, ConnectionRefusedError):
            return None
        # Send everything
        _send_message(s, msg)
        return _recv_message(s)


SIZE_BYTE_COUNT = 4
SIZE_BYTE_ORDER = 'big'


def _send_message(s, msg):
    """Send a message on the socket."""
    data = bytes(jsonpickle.encode(msg), encoding='utf-8')
    size = len(data).to_bytes(SIZE_BYTE_COUNT, byteorder=SIZE_BYTE_ORDER)
    s.sendall(b''.join([size, data]))


def _recv_message(s):
    """Receive a message on the socket."""
    # Get the message size
    size = []
    while len(size) < SIZE_BYTE_COUNT:
        buf = s.recv(SIZE_BYTE_COUNT)
        size.extend(buf)
    size = bytes(size)
    size = int.from_bytes(size, byteorder=SIZE_BYTE_ORDER)
    # Now get the message data
    data = []
    while len(data) < size:
        buf = s.recv(size)
        data.extend(buf)
    data = bytes(data)
    return jsonpickle.decode(str(data, encoding='utf-8'))
