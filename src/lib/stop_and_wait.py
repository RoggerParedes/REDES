from socket import timeout
from typing import BinaryIO

from lib.checksum import generate_checksum, verify_checksum
from lib.protocol import Data, Message, ACK, NACK, READ_SIZE, TIMEOUT, MAX_TIMES_TIMEOUT
from lib.logger import logger
from lib.message_queue import MessageQueue
from lib.exceptions import DownloaderNotReadyError


def get_timeout():
    return TIMEOUT


# Estos métodos esperan que ya haya comenzado la comunicación
# reciben el socket abierto y un file descriptor abierto para ir escribiendo la data recv
def upload(queue: MessageQueue, fd: BinaryIO):
    queue.set_timeout(get_timeout())
    upload_count = 1
    timeout_count = 0
    data = fd.read(READ_SIZE)
    while data != b'':
        packet = Data(upload_count, data).write()
        packet = generate_checksum(packet)
        queue.send(packet)
        logger.debug(f"Esperamos ACK {upload_count}")
        try:
            receive = queue.recv()
            timeout_count = 0
            check, rec_data = verify_checksum(receive)
            if check:
                message = Message.read(rec_data)
                if message.type == ACK.type and message.uid == upload_count:
                    logger.debug(f"Recibimos ACK {upload_count}")
                    data = fd.read(READ_SIZE)
                    upload_count += 1
                # Caso donde el downloader no recibió start
                elif message.type == NACK.type and message.uid == 0:
                    raise DownloaderNotReadyError()
        except timeout as e:
            timeout_count += 1
            if timeout_count > MAX_TIMES_TIMEOUT:
                logger.error("La espera del ACK hizo timeout")
                raise e
    logger.info("Archivo enviado con exito.")


# El parámetro size aca espera el valor dado al principio
# de la comunicación el mensaje Start
def download(queue: MessageQueue, fd: BinaryIO, size):
    queue.set_timeout(get_timeout())
    read_count = 1
    timeout_count = 0
    rec_size = 0
    packet = b''
    while rec_size < size:
        read_flag = False
        try:
            receive = queue.recv()
            timeout_count = 0
            check, rec_data = verify_checksum(receive)
            if check:
                message = Message.read(rec_data)
                logger.debug(f"Recibimos uid {message.uid} y esperabamos {read_count}")
                if message.type == Data.type and message.uid == read_count:
                    rec_size += len(message.data)
                    fd.write(message.data)
                    read_flag = True
                    packet = ACK(read_count).write()
                    packet = generate_checksum(packet)
                    read_count += 1
                elif message.type == Data.type and message.uid < read_count:
                    read_flag = True
                    logger.debug(f"Reenviamos el ACK {message.uid} para sincronizar")
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
    logger.info("Archivo recibido con exito.")
