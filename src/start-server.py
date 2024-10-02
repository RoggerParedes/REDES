import os
import argparse
import platform
from socket import socket, AF_INET, SOCK_DGRAM
from time import sleep
from lib.constants import TIMEOUT
from lib.logger import logger
import sys
from lib.exceptions import validate_port, validate_directory, \
    InvalidDirectoryException, InvalidPortException
from src.lib.client_handler import ClientHandler


def get_args():
    port = int(args.PORT)
    validate_port(port)
    path = args.PATH
    validate_directory(path)
    verbose = args.VERBOSE
    quiet = args.QUIET
    ip = args.ADDR
    return verbose, quiet, ip, port, path

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
                    "Introduzca 'q' para finalizar la ejecucion del servidor\nIntroduzca 'i' para ver informacion sobre el servidor.\nIntroduzca 'c' para limpiar la consola.\n")
                if key == 'i':
                    logger.info(f"Servidor corriendo en {ip}:{port}")
                    logger.info(f"Servidor almacenando archivos en {directory}\n##### Archivos almacenados #####")
                    files = os.listdir(directory)
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
        logger.error(e)
        sys.exit(1)
