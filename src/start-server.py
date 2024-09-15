import argparse
import socket
from lib.constants import BUFFSIZE
from lib.logger import logger
import traceback
import sys
from lib.exceptions import *


def get_args():
    port = (int)(args.PORT)
    validate_port(port)
    path = args.PATH
    validate_directory(path)
    verbose = args.VERBOSE
    quiet = args.QUIET
    ip = args.ADDR
    return verbose, quiet, ip, port, path


def client_handler(data, address):
    # Aca tengo que ver que me pide el cliente
    # puede ser upload o download, ya comienza la etapa del protocolo
    print("client handler")


def main():
    
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
    
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind((ip, port))
    except InvalidPortException as e:
        logger.error(f"{e}")
        sys.exit(1)
    clients_connected = []
    
    try:
        while True:
            data, client_address = server_socket.recvfrom(BUFFSIZE)
            if client_address not in clients_connected:
                print(f"New connection to: {client_address}\nData: {data}")
                clients_connected.append(client_address[1])
                client_handler(data, client_address)
            else:
                print("por que el cliente me sigue enviando mensajes y no lo agarro el handler?")
    except KeyboardInterrupt:   
        print("Server stopped.")
    except Exception as e:
        print(f"Error: {e}")


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
