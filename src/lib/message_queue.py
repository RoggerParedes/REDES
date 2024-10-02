from queue import Queue, Empty
from socket import socket, timeout


MAX_PACKET_SIZE = 64 * 1024 + 1


# Esta es la clase que utiliza el cliente para mandar los mensajes,
# es una manera simple de no estar usando
# el addr en upload download.
class MessageQueue:
    sock: socket

    def __init__(self, sock, addr):
        self.sock = sock
        self.addr = addr

    def set_timeout(self, seconds):
        return self.sock.settimeout(seconds)

    def send(self, message):
        return self.sock.sendto(message, self.addr)

    def recv(self) -> bytes:
        return self.sock.recvfrom(MAX_PACKET_SIZE)[0]


class ThreadedMessageQueue(MessageQueue):
    que: Queue
    timeout: int

    def __init__(self, sock, addr, que: Queue):
        super().__init__(sock, addr)
        self.que = que
        self.timeout = 1

    def set_timeout(self, seconds):
        self.timeout = seconds
        return self.sock.settimeout(seconds)

    def send(self, message):
        return self.sock.sendto(message, self.addr)

    def recv(self) -> bytes:
        try:
            return self.que.get(timeout=self.timeout)
        except Empty:
            raise timeout
