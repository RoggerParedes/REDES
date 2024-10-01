from socket import timeout
from typing import BinaryIO

from lib.checksum import generate_checksum, verify_checksum
from lib.protocol import Data, Message, ACK, NACK
from lib.constants import READ_SIZE, TIMEOUT, MAX_TIMES_TIMEOUT
from lib.logger import logger
from lib.message_queue import MessageQueue
from lib.exceptions import DownloaderNotReadyError


def get_timeout():
    return TIMEOUT


# en este punto la comunicación ya debe estar establecida
def upload(queue: MessageQueue, fd: BinaryIO):
    queue.set_timeout(get_timeout())
    logger.info("Comiendo subida de archivo")
    upload_count = 1
    timeout_count = 0
    data = fd.read(READ_SIZE)
    while data != b'':
        packet = Data(upload_count, data).write()
        packet = generate_checksum(packet)
        logger.debug(f"Enviando paquete {packet}")
        queue.send(packet)
        logger.debug(f"Se espera ACK {upload_count}")
        try:
            receive = queue.recv()
            timeout_count = 0
            check, rec_data = verify_checksum(receive)
            if check:
                message = Message.read(rec_data)
                logger.debug(
                    f"Se recibe paquete tipo {message.type} uid {message.uid}")
                if message.type == ACK.type and message.uid == upload_count:
                    data = fd.read(READ_SIZE)
                    upload_count += 1

                # Caso donde el downloader no recibe antes el start
                elif message.type == NACK.type and message.uid == 0:
                    raise DownloaderNotReadyError()
        except timeout as e:
            timeout_count += 1
            if timeout_count > MAX_TIMES_TIMEOUT:
                logger.error("La espera del ACK hizo timeout")
                raise e
    logger.info("Terminó la subida del archivo")


# size es el parametro que está al principio en start
def download(queue: MessageQueue, fd: BinaryIO, size):
    queue.set_timeout(get_timeout())
    logger.info("Comenzo la descarga del archivo")
    read_count = 1
    timeout_count = 0
    rec_size = 0
    while rec_size < size:
        read_flag = False
        try:
            receive = queue.recv()
            timeout_count = 0
            check, rec_data = verify_checksum(receive)
            if check:
                message = Message.read(rec_data)
                logger.debug(f"Se recibe paquete tipo {message.type} uid {message.uid} y se esperaba {read_count}")
                if message.type == Data.type and message.uid == read_count:
                    logger.debug("Se escribe la data")
                    rec_size += len(message.data)
                    fd.write(message.data)
                    read_flag = True
                    packet = ACK(read_count).write()
                    packet = generate_checksum(packet)
                    read_count += 1
                elif message.type == Data.type and message.uid < read_count:
                    read_flag = True
                    logger.debug(
                        f"Se reenvía el ACK {message.uid} si no era el último "
                        "que se esperaba")
                    packet = ACK(message.uid).write()
                    packet = generate_checksum(packet)

            if not read_flag:
                packet = NACK(read_count).write()
                packet = generate_checksum(packet)
            queue.send(packet)
        except timeout as e:
            timeout_count += 1
            if timeout_count > MAX_TIMES_TIMEOUT:
                logger.error("La espera de datos hizo timeout")
                raise e

    logger.info("Terminó la bajada del archivo")
