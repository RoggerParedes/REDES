import sys
import argparse
from socket import socket, AF_INET, SOCK_DGRAM
from lib.checksum import generate_checksum, verify_checksum
from lib.constants import OPERATION_UPLOAD
from lib.logger import logger
from lib.exceptions import validate_port, InvalidPortException
from lib.message_queue import MessageQueue
from lib.protocol import Error, Message, Start
from lib.stop_and_wait import download

def get_args():
    parser = argparse.ArgumentParser(description="<command description>")
    parser.add_argument('-v', '--verbose', action='store_true', help="increase output verbosity")
    parser.add_argument('-q', '--quiet', action='store_true', help="decrease output verbosity")
    parser.add_argument('-H', '--host', type=str, required=True, help="server IP address")
    parser.add_argument('-p', '--port', type=str, required=True, help="server port")
    parser.add_argument('-d', '--dst', type=str, required=True, help="destination file path")
    parser.add_argument('-n', '--name', type=str, required=True, help="file name")
    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()
    logger.set_level_args(args.quiet, args.verbose)

    try:
        validate_port(int(args.port))
    except InvalidPortException:
        sys.exit(1)
    
    logger.info(f"Comenzo la descarga del archivo {args.name} en la carpeta {args.dst} proveniente del servidor en {args.host}:{args.port}")
    server_addr = (args.host,int(args.port))
    client_socket = socket(AF_INET, SOCK_DGRAM)
    queue = MessageQueue(client_socket, server_addr)
    queue.set_timeout(3)

    try:
        packet = Start(OPERATION_UPLOAD, 0, args.name).write()
        packet_check = generate_checksum(packet)
        queue.send(packet_check)
        recv_packet = queue.recv()
        checksum, recv_data = verify_checksum(recv_packet)
        if checksum:
            message = Message.read(recv_data)
            if message.type == Start.type:
                with open(args.name, 'wb+') as file:
                    download(queue, file, message.file_size)
            elif message.type == Error.type:
                logger.error(Error.get_message_error(message.error_type))
    except socket.timeout:
        logger.error("El servidor no responde...")
    except Exception as e:
        logger.error(f"Ocurrio un error desconocido: {e}")
    client_socket.close()
