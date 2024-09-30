import argparse
from queue import Queue
from socket import socket, AF_INET, SOCK_DGRAM, timeout, SHUT_RD
from time import sleep
# from typing import BinaryIO
from lib.constants import OPERATION_DOWNLOAD, OPERATION_UPLOAD, \
    MAX_FILE_SIZE, MAX_PACKET_SIZE, TIMEOUT
from lib.logger import logger
from lib.checksum import verify_checksum, generate_checksum
# import traceback
import sys
from lib.exceptions import validate_port, validate_directory, \
    InvalidDirectoryException, InvalidPortException
import threading
from lib.protocol import Start, Error, Message, NACK
from lib.message_queue import ThreadedMessageQueue
from lib.stop_and_wait import upload, download
import os


def get_args():
    port = (int)(args.PORT)
    validate_port(port)
    path = args.PATH
    validate_directory(path)
    verbose = args.VERBOSE
    quiet = args.QUIET
    ip = args.ADDR
    return verbose, quiet, ip, port, path


def start_upload(queue, file_dir, file_name):
    if not os.path.isfile(file_dir):
        logger.info(f'No se encuentra la ruta {file_dir}')
        packet = Error(0, Error.FILE_NOT_FOUND).write()
        packet = generate_checksum(packet)
        queue.send(packet)
        return

    size = os.path.getsize(file_dir)
    if size > MAX_FILE_SIZE:
        logger.error("El archivo es demasiado grande. El tamaño máximo es 4GB")
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
        # loop principal
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
        logger.debug('Cerrando las conexiones con todos los clientes')
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
        logger.info('Frenando la ejecución del servidor')


def main():
    try:
        verbose, quiet, ip, port, directory = get_args()
    except InvalidPortException:
        sys.exit(1)
    except InvalidDirectoryException:
        sys.exit(1)

    logger.set_level_args(quiet, verbose)
    logger.info(f"Iniciando servidor en {ip}:{port}")
    logger.info(f"Almacenamiento del servidor en {directory}")

    sock = socket(AF_INET, SOCK_DGRAM)
    try:
        sock.bind((ip, port))
    except OSError as exc:
        logger.error(f'No se pudo conectar al puerto indicado: {exc.strerror}')
        sys.exit(1)
    sock.settimeout(TIMEOUT)

    client_handler = ClientHandler(sock, directory)
    client_handler.start()
    try:
        key = ''
        while key != 'q':
            try:
                key = input(
                    'Introduzca q para finalizar la ejecucion del servidor\n')
            except EOFError:
                # Esto ocurre solo si lo estamos corriendo fuera de la consola
                sleep(1)
    except KeyboardInterrupt:
        logger.debug('Interrupción por teclado detectada')
    client_handler.stop()
    sock.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", dest="VERBOSE", required=False,
                       help="increase output verbosity",
                       action="store_true")
    group.add_argument("-q", "--quiet", dest="QUIET", required=False,
                       help="decrease output verbosity",
                       action="store_true")
    parser.add_argument("-H", "--host", dest="ADDR", required=True,
                        help="service IP address",
                        action="store", type=str)
    parser.add_argument("-p", "--port", dest="PORT", required=True,
                        help="service port",
                        action="store", type=int)
    parser.add_argument("-s", "--storage", dest="PATH", required=True,
                        help="storage dir path",
                        action="store", type=str)
    args = parser.parse_args()
    try:
        main()
        logger.info("Cerrando servidor...")
        sys.exit(0)
    except Exception as e:
        # traceback.print_exc()
        print(e)
        sys.exit(1)
