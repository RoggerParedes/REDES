import argparse
import os
import platform
import sys
import traceback
from socket import socket, AF_INET, SOCK_DGRAM
from time import sleep

from lib.client_handler import ClientHandler
from lib.exceptions import InvalidPortException, InvalidDirectoryException, validate_port, validate_directory
from lib.logger import logger
from lib.protocol import TIMEOUT


def get_args():
    parser = argparse.ArgumentParser(prog='start - server', description="<command description>")
    parser.add_argument('-v', '--verbose', action='store_true', help="increase output verbosity")
    parser.add_argument('-q', '--quiet', action='store_true', help="decrease output verbosity")
    parser.add_argument('-H', '--host', type=str, required=True, help="service IP address")
    parser.add_argument('-p', '--port', type=int, required=True, help="service port")
    parser.add_argument('-s', '--storage', type=str, required=True, help="storage dir path")
    return parser.parse_args()


def main():
    try:
        args = get_args()
        validate_port(args.port)
        validate_directory(args.storage)
    except InvalidPortException:
        sys.exit(1)
    except InvalidDirectoryException:
        sys.exit(1)
    logger.set_level_args(args.quiet, args.verbose)
    logger.info(f"Server addres {args.host}:{args.port}")
    logger.info(f"Server storage {args.storage}")

    server_socket = socket(AF_INET, SOCK_DGRAM)
    try:
        server_socket.bind((args.host, args.port))
    except OSError as e:
        logger.error(f"No se pudo conectar a la direccion indicada {args.host}:{args.port}")
        logger.error(e)
        sys.exit(1)
    server_socket.settimeout(TIMEOUT)

    client_handler = ClientHandler(server_socket, args.storage)
    client_handler.start()

    try:
        key = ''
        while key != 'q':
            try:
                key = input(
                    "Introduzca 'q' para finalizar la ejecucion del servidor\nIntroduzca 'i' para ver informacion sobre el servidor.\nIntroduzca 'c' para limpiar la consola.\n")
                if key == 'i':
                    logger.info(f"Servidor corriendo en {args.host}:{args.port}")
                    logger.info(f"Servidor almacenando archivos en {args.storage}\n##### Archivos almacenados #####")
                    files = os.listdir(args.storage)
                    for file in files:
                        logger.info(file)
                if key == 'c':
                    sistema_operativo = platform.system()
                    if sistema_operativo == "Windows":
                        os.system('cls')
                    else:
                        os.system('clear')
            except EOFError:
                sleep(1)
    except KeyboardInterrupt:
        logger.debug('Interrupcion por teclado detectada')
    client_handler.stop()
    server_socket.close()


if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except Exception as e:
        traceback.print_exc()
        logger.error(e)
        sys.exit(1)