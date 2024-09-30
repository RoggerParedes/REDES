from socket import socket, AF_INET, SOCK_DGRAM
import argparse
import os
import sys

from lib.logger import logger
from lib.checksum import generate_checksum
from lib.constants import MAX_FILE_SIZE
from lib.exceptions import InvalidPortException, validate_port
from lib.constants import OPERATION_DOWNLOAD
from lib.protocol import Start
from lib.message_queue import MessageQueue
from lib.stop_and_wait import upload


def get_args():
    parser = argparse.ArgumentParser(
        description="<command description>",
        usage="upload [-h] [-v | -q] [-H ADDR] [-p PORT] [-s FILEPATH] \
            [-n FILENAME]"
    )
    parser.add_argument('-v', '--verbose', action='store_true',
                        help="increase output verbosity")
    parser.add_argument('-q', '--quiet', action='store_true',
                        help="decrease output verbosity")
    parser.add_argument('-H', '--host', type=str, required=True,
                        help="server IP address")
    parser.add_argument('-p', '--port', type=int, required=True,
                        help="server port")
    parser.add_argument('-s', '--src', type=str, required=True,
                        help="source file path")
    parser.add_argument('-n', '--name', type=str, required=True,
                        help="file name")
    return parser.parse_args()


def read_file(filepath):
    try:
        with open(filepath, "r") as f:
            data = f.read()
        return data
    except FileNotFoundError:
        raise Exception(
            "La ruta del archivo es inválida o el archivo no existe."
        )


if __name__ == "__main__":
    args = get_args()
    logger.set_level_args(args.quiet, args.verbose)
    logger.info(f"Iniciando carga del archivo en {args.host}:{args.port}")

    try:
        validate_port(int(args.port))
    except InvalidPortException:
        sys.exit(1)

    server_addr = (args.host, int(args.port))
    sock = socket(AF_INET, SOCK_DGRAM)
    size = os.path.getsize(args.src)
    if size > MAX_FILE_SIZE:
        logger.error("El archivo es demasiado grande. Maximo tamanio es 4GB")
        sock.close()
    queue = MessageQueue(sock, server_addr)
    packet = Start(OPERATION_DOWNLOAD, size, args.name).write()
    packet = generate_checksum(packet)
    queue.send(packet)
    try:
        with open(args.src, 'rb+') as file:
            upload(queue, file)
    except OSError:
        logger.error(
            f"Error el archivo que intentas subir cuya ruta es: \
            {args.src} no existe "
        )
        sock.close()

    sock.close()
