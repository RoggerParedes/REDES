import os
from socket import socket, timeout, SHUT_RD
import threading
from queue import Queue

from lib.logger import logger
from lib.checksum import verify_checksum, generate_checksum
from lib.message_queue import MAX_PACKET_SIZE, ThreadedMessageQueue
from lib.protocol import Message, Start, NACK, OPERATION_UPLOAD, OPERATION_DOWNLOAD, Error, MAX_FILE_SIZE
from lib.version import upload, download


def start_upload(queue, file_dir, file_name):
    if not os.path.isfile(file_dir):
        logger.info(f'Ruta {file_dir} INVALIDA')
        packet = Error(0, Error.FILE_NOT_FOUND).write()
        packet = generate_checksum(packet)
        queue.send(packet)
        return

    size = os.path.getsize(file_dir)
    if size > MAX_FILE_SIZE:
        logger.error(f"El archivo es demasiado grande. Maximo 4GB")
        return
    packet = Start(OPERATION_DOWNLOAD, size, file_name).write()
    packet = generate_checksum(packet)
    queue.send(packet)
    with open(file_dir, 'rb+') as file:
        try:
            upload(queue, file)
        except timeout:
            pass


def new_connection(queue: ThreadedMessageQueue,
                   directory: str,
                   message_start: Start):
    logger.info(f"Nueva conexión desde {queue.addr}")
    file_dir = os.path.join(directory, message_start.file_name)
    if message_start.operation == OPERATION_UPLOAD:
        start_upload(queue, file_dir, message_start.file_name)
    if message_start.operation == OPERATION_DOWNLOAD:
        with open(file_dir, 'wb+') as file:
            try:
                download(queue, file, message_start.file_size)
            except timeout:
                pass


class ClientHandler:
    def __init__(self, sock: socket, directory):
        self.sock = sock
        self.directory = directory
        self.clients = {}  # : List[Tuple[addr, ThreadedMessageQueue, Thread]]
        self.running = False
        self.thread = threading.Thread(target=self._run)

    def start(self):
        self.thread.start()

    def _run(self):
        self.running = True
        # Loop que recibe nuevas conexiones
        while self.running:
            try:
                data, addr = self.sock.recvfrom(MAX_PACKET_SIZE)
                check, recv_data = verify_checksum(data)
                if not check:
                    continue

                message = Message.read(recv_data)
                if message.type == Start.type:
                    queue = ThreadedMessageQueue(self.sock, addr, Queue())
                    queue.set_timeout(5)
                    client = threading.Thread(
                        target=new_connection,
                        args=(queue, self.directory, message)
                    )
                    self.clients[addr] = (queue, client)
                    client.start()
                elif addr in self.clients:
                    self.clients[addr][0].que.put(data)
                else:
                    packet = NACK(0).write()
                    packet = generate_checksum(packet)
                    self.sock.sendto(packet, addr)
            except timeout:
                pass
            except OSError as exc:
                if self.running:
                    raise exc
                else:
                    logger.debug(
                        "El servidor deja de escuchar nuevas conexiones")

    def close_clients(self):
        for addr, client in self.clients.items():
            client[1].join()
            logger.debug(f"Cerrando conexión con {addr}")
        self.clients = {}

    def stop(self):
        self.running = False
        try:
            self.sock.shutdown(SHUT_RD)
        except OSError:
            pass
        self.sock.close()
        self.thread.join()
        self.close_clients()
        logger.info('Servidor apagado')