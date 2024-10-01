from queue import Queue, Empty
from socket import socket, timeout

from lib.constants import MAX_PACKET_SIZE
from lib.logger import logger

class MessageQueue:
    _socket: socket

    def __init__(self, sock, addr):
        self._socket = sock
        self.addr = addr

    def set_timeout(self, seconds):
        return self._socket.settimeout(seconds)

    def send(self, message):
        return self._socket.sendto(message, self.addr)

    def recv(self) -> bytes:
        try:
            ret = self._socket.recvfrom(MAX_PACKET_SIZE)[0]
        except Exception as e:
            logger.error(f"Error: {e}")
        return ret


class ThreadedMessageQueue(MessageQueue):
    queue: Queue
    timeout: int

    def __init__(self, sock, addr, que: Queue):
        super().__init__(sock, addr)
        self.queue = que
        self.timeout = 1

    def set_timeout(self, seconds):
        self.timeout = seconds
        return self._socket.settimeout(seconds)

    def send(self, message):
        return self._socket.sendto(message, self.addr)

    def recv(self) -> bytes:
        try:
            return self.queue.get(timeout=self.timeout)
        except Empty:
            raise timeout
