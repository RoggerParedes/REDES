import argparse
import os
import sys
from socket import socket, AF_INET, SOCK_DGRAM, timeout

from lib.checksum import generate_checksum, verify_checksum
from lib.exceptions import validate_port, validate_directory, InvalidPortException, InvalidDirectoryException
from lib.logger import logger
from lib.message_queue import MessageQueue
from lib.protocol import Start, OPERATION_UPLOAD, Message, Error, MAX_TIMES_TIMEOUT
from lib.version import download


def get_args():
    parser = argparse.ArgumentParser(
        prog='download',
        usage='download [ - h ] [ - v | -q ] [ - H ADDR ] [ - p PORT ] [ - d FILEPATH ] [ - n FILENAME ]',
        description='< command description >',
        add_help=False
    )
    parser.add_argument('-h', '--help', action='help', help='show this help message and exit')
    parser.add_argument('-v', '--verbose', action='store_true', help='increase output verbosity')
    parser.add_argument('-q', '--quiet', action='store_true', help='decrease output verbosity')
    parser.add_argument('-H', '--host', metavar='ADDR', help='server IP address', required=True)
    parser.add_argument('-p', '--port', metavar='PORT', type=int, help='server port', required=True)
    parser.add_argument('-d', '--dst', metavar='FILEPATH', help='destination file path', required=True)
    parser.add_argument('-n', '--name', metavar='FILENAME', help='file name', required=True)
    return parser.parse_args()

def main(host, port, path_dest, name):
    logger.info(f"Comenzando descarga del archivo {name} en el servidor {host}:{port}")
    server_addr = (host, int(port))
    sock = socket(AF_INET, SOCK_DGRAM)
    queue = MessageQueue(sock, server_addr)
    queue.set_timeout(MAX_TIMES_TIMEOUT)

    try:
        packet = Start(OPERATION_UPLOAD, 0, name).write()
        packet = generate_checksum(packet)
        queue.send(packet)

        receive = queue.recv()
        check, rec_data = verify_checksum(receive)
        if check:
            message = Message.read(rec_data)
            if message.type == Start.type:
                with open(path_dest+name, 'wb+') as file:
                    download(queue, file, message.file_size)
            elif message.type == Error.type:
                logger.error(Error.get_error_msg(message.error_type))
    except TimeoutError:
        logger.error(f"Servidor en la direccion {host}:{port} no responde. Verifique direcciones.")
    sock.close()

if __name__ == "__main__":
    args = get_args()
    logger.set_level_args(args.quiet, args.verbose)
    try:
        validate_port(int(args.port))
        validate_directory(args.dst)
    except InvalidPortException:
        sys.exit(1)
    except InvalidDirectoryException:
        sys.exit(1)

    if not os.path.isdir(args.dst):
        logger.error('La direccion de destino debe ser una carpeta valida.')
        sys.exit(1)
    try:
        main(args.host, args.port, args.dst, args.name)
    except KeyboardInterrupt:
        logger.error('Descarga interrumpida')
        sys.exit(1)
