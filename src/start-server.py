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
import os

def get_args():
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
    parser.add_argument("-c", "--config", dest="CONFIG", required=True,
                        help="path to the configuration file", action="store", type=str)
    args = parser.parse_args()
    return args

def read_protocol_from_file(config_path):
    """Función para leer el protocolo desde un archivo de configuración."""
    protocol = None
    try:
        with open(config_path, 'r') as config_file:
            for line in config_file:
                if line.startswith('protocol='):
                    protocol = line.split('=')[1].strip()
                    break
        if protocol not in ['gobackn', 'stopandwait', 'selectiverepeat']:
            raise ValueError(f"Protocolo inválido: {protocol}")
        return protocol
    except FileNotFoundError:
        logger.error(f"No se encontró el archivo de configuración: {config_path}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Error en el archivo de configuración: {e}")
        sys.exit(1)

def start_upload_gobackn(queue, file_dir, file_name):
    logger.info(f"Iniciando carga del archivo {file_name} utilizando Go-Back-N ubicado en {file_dir}")

def start_upload_stopandwait(queue, file_dir, file_name):
    logger.info(f"Iniciando carga del archivo {file_name} utilizando Stop-and-Wait ubicado en {file_dir}")

def start_upload_selectiverepeat(queue, file_dir, file_name):
    logger.info(f"Iniciando carga del archivo {file_name} utilizando Selective Repeat ubicado en {file_dir}")


def download_gobackn(queue: MessageQueue, fd: BinaryIO, size):
    logger.info(f"Iniciando descarga del archivo con tamaño {size} utilizando Go-Back-N.")

def download_stopandwait(queue: MessageQueue, fd: BinaryIO, size):
    logger.info(f"Iniciando descarga del archivo con tamaño {size} utilizando Stop-and-Wait.")

def download_selectiverepeat(queue: MessageQueue, fd: BinaryIO, size):
    logger.info(f"Iniciando descarga del archivo con tamaño {size} utilizando Selective Repeat.")


def new_connection(queue: ThreadedMessageQueue, directory: str, message_start: Start, protocol: str):
    logger.info(f"Nueva conexión desde {queue.addr} utilizando el protocolo {protocol}")
    file_dir = os.path.join(directory, message_start.file_name)
    
    if message_start.operation == OPERATION_UPLOAD:
        if protocol == 'gobackn':
            start_upload_gobackn(queue, file_dir, message_start.file_name)
        elif protocol == 'stopandwait':
            start_upload_stopandwait(queue, file_dir, message_start.file_name)
        elif protocol == 'selectiverepeat':
            start_upload_selectiverepeat(queue, file_dir, message_start.file_name)
    
    if message_start.operation == OPERATION_DOWNLOAD:
        with open(file_dir, 'wb+') as file:
            try:
                if protocol == 'gobackn':
                    download_gobackn(queue, file, message_start.file_size)
                elif protocol == 'stopandwait':
                    download_stopandwait(queue, file, message_start.file_size)
                elif protocol == 'selectiverepeat':
                    download_selectiverepeat(queue, file, message_start.file_size)
            except timeout:
                pass

class ClientHandler:

    def __init__(self, sock: socket, directory, protocol):
        self.sock = sock
        self.directory = directory
        self.protocol = protocol  # Guardar el protocolo seleccionado
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
                        args=(queue, self.directory, message, self.protocol)  # Pasar protocolo
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
                    logger.debug("El servidor deja de escuchar nuevas conexiones")

            except Exception as e:
                logger.error(f"Ocurrió un error inesperado: {e}")
    
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
        args = get_args()
        verbose, quiet, ip, port, path = args.VERBOSE, args.QUIET, args.ADDR, args.PORT, args.PATH
        config_path = args.CONFIG
        
        # Leer el protocolo desde el archivo de configuración
        protocol = read_protocol_from_file(config_path)

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
        sys.exit(1)
    except InvalidDirectoryException:
        sys.exit(1)

    server_socket = socket(AF_INET, SOCK_DGRAM)
    try:
        server_socket.bind((ip, port))
    except OSError as e:
        logger.error(f"No se pudo conectar al puerto indicado: {e}")
        sys.exit(1)
    clients_connected = []
    
    server_socket.settimeout(TIMEOUT)
    
    listener = ClientHandler(server_socket, path, protocol)  # Pasar el protocolo al manejador
    listener.start()
    try:
        key = ''
        while key != 'q':
            try:
                key = input('Introduzca q para finalizar con la ejecución del servidor\n')
            except EOFError:
                sleep(1)
    except KeyboardInterrupt:
        logger.debug('Interrupción por teclado detectada')
    except Exception as e:
        logger.error(f"Ocurrió un error inesperado: {e}")
    listener.stop()

    server_socket.close()


if __name__ == "__main__":
    try:
        main()
        logger.info("Cerrando servidor...")
        sys.exit(0)
    except Exception as e:
        print(e)
        sys.exit(1)