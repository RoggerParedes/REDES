import argparse
import os
import sys
from asyncio import timeout
from importlib.metadata import files
from socket import socket, AF_INET, SOCK_DGRAM

from lib.checksum import generate_checksum
from lib.exceptions import InvalidPortException, validate_port, validate_directory, InvalidDirectoryException, \
    validate_file
from lib.logger import logger
from lib.message_queue import MessageQueue
from lib.protocol import MAX_FILE_SIZE, OPERATION_DOWNLOAD, Start
from lib.version import upload


def get_args():
    parser = argparse.ArgumentParser(
        prog='upload',
        usage='upload [ - h ] [ - v | -q ] [ - H ADDR ] [ - p PORT ] [ - s FILEPATH ] [ - n FILENAME ]',
        description='< command description >',
        add_help=False
    )
    parser.add_argument('-h', '--help', action='help', help='show this help message and exit')
    parser.add_argument('-v', '--verbose', action='store_true', help='increase output verbosity')
    parser.add_argument('-q', '--quiet', action='store_true', help='decrease output verbosity')
    parser.add_argument('-H', '--host', metavar='ADDR', help='server IP address', required=True)
    parser.add_argument('-p', '--port', metavar='PORT', type=int, help='server port', required=True)
    parser.add_argument('-s', '--src', metavar='FILEPATH', help='source file path', required=True)
    parser.add_argument('-n', '--name', metavar='FILENAME', help='file name', required=True)
    return parser.parse_args()

def main(host, port, src, name):

    server_addr = (host, int(port))
    client_socket = socket(AF_INET, SOCK_DGRAM)

    file_size = os.path.getsize(src+name)
    if file_size > MAX_FILE_SIZE:
        logger.error(f"Tamanio maximo {2**32+1}. Tamanio actual {file_size}")
        client_socket.close()
        sys.exit(1)

    queue = MessageQueue(client_socket, server_addr)
    packet_init = Start(OPERATION_DOWNLOAD, file_size, name).write()
    packet_init = generate_checksum(packet_init)
    queue.send(packet_init)

    try:
        with open(src+name, 'rb') as file:
            upload(queue, file)
    except TimeoutError:
        logger.error(f"El servidor en la direccion {host}:{port} no responde. Verifique direcciones.")
        client_socket.close()
        sys.exit(1)
    except OSError:
        client_socket.close()
        logger.error(f"Ocurrio un error al abrir el archivo {src+name}.")
        sys.exit(1)
    client_socket.close()

if __name__ == "__main__":
    args = get_args()
    logger.set_level_args(args.quiet, args.verbose)
    logger.info(f"Iniciando carga del archivo {args.src+args.name} en el servidor {args.host}:{args.port}")
    try:
        validate_port(int(args.port))
        validate_file(args.src+args.name)
    except InvalidPortException:
        sys.exit(1)
    except FileNotFoundError:
        sys.exit(1)

    try:
        main(args.host, args.port, args.src, args.name)
        sys.exit(0)
    except Exception as e:
        logger.error(e)
        sys.exit(1)
