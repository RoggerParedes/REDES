import argparse
from queue import Queue
from socket import socket, AF_INET, SOCK_DGRAM, timeout, SHUT_RD
from time import sleep
from typing import BinaryIO
from lib.constants import *
from lib.logger import logger
from lib.checksum import verify_checksum, generate_checksum
import traceback
import sys
from lib.exceptions import *
import threading
from lib.protocol import *
from message_queue import MessageQueue, ThreadedMessageQueue

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
    logger.info(f"Iniciando carga del archivo {file_name} ubicado en {file_dir}")

def download(queue: MessageQueue, fd: BinaryIO, size):
    logger.info(f"Iniciando descarga del archivo con tamanio {size}.")

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
        self.clients = {} # Lista de clientes con [addr, queue, thread]
        self.running = False
        self.thread = threading.Thread(target=self._run)
    
    def start(self):
        self.thread.start()
    
    def _run(self):
        self.running = True
        while self.running:
            try:
                data, addr = self.sock.recvfrom(MAX_PACKET_SIZE)
                checksum, data_recv = verify_checksum(data) 
                if not checksum:
                    continue

                message = Message.read(data_recv)
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

            except Exception as e:
                logger.error(f"Ocurrio un error inesperado: {e}")
    
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
        logger.info('Frenando la ejecucion del servidor')

def main():
    try:
        verbose, quiet, ip, port, path = get_args()
        if verbose:
            print("Output increased...")
            logger.set_level(2)
        elif quiet:
            print("Output decreased...")
            logger.set_level(1)
        else:
            print("Default output...")
            logger.set_level(2)
    except InvalidPortException:
        #logger.error(f"{e}")
        sys.exit(1)
    except InvalidDirectoryException:
        sys.exit(1)

    server_socket = socket(AF_INET, SOCK_DGRAM)
    try:
        server_socket.bind((ip, port))
    except OSError as e:
        logger.error(f"No se puedo conectar al puerto indicado: {e}")
        sys.exit(1)
    
    server_socket.settimeout(TIMEOUT)
    
    listener = ClientHandler(server_socket, path)
    listener.start()
    try:
        key = ''
        while key != 'q':
            try:
                key = input('Introduzca q para finalizar con la ejecucion del '
                        'servidor\n')
            except EOFError: # Esto ocurre solo si lo estamos corriendo fuera de la consola
                sleep(1)
    except KeyboardInterrupt:
        logger.debug('Interrupcion por teclado detectada')
    except Exception as e:
        logger.error(f"Ocurrio un error inesperado: {e}")
    listener.stop()

    server_socket.close()


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
                        help="service IP address", action="store", type=str)
    parser.add_argument("-p", "--port", dest="PORT", required=True,
                        help="service port", action="store", type=int)
    parser.add_argument("-s", "--storage", dest="PATH", required=True,
                        help="storage dir path", action="store", type=str)
    args = parser.parse_args()
    try:
        main()
        logger.info("Cerrando servidor...")
        sys.exit(0)
    except Exception as e:
        #traceback.print_exc()
        print(e)
        sys.exit(1)
