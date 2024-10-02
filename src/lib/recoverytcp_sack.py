from socket import timeout
from typing import BinaryIO

from lib.checksum import verify_checksum, generate_checksum
from lib.message_queue import MessageQueue
from lib.protocol import TIMEOUT, Message, Data, ACK, SACK, NACK, MAX_TIMES_TIMEOUT, READ_SIZE
from lib.logger import logger


def download(queue: MessageQueue, fd: BinaryIO, size):
    logger.info("ALGORITMO -> RECOVERY TCP + SELECTIVE ACK")
    queue.set_timeout(TIMEOUT)
    read_count = 1
    timeout_count = 0
    rec_size = 0
    packet = b''
    sack_blocks = []  # Bloques de datos recibidos fuera de orden
    received_data = {}  # Almacena datos fuera de orden temporalmente
    while rec_size < size:
        read_flag = False
        try:
            receive = queue.recv()
            timeout_count = 0
            check, rec_data = verify_checksum(receive)
            if check:
                message = Message.read(rec_data)
                logger.debug(f"Recibimos uid {message.uid} y esperábamos {read_count}")
                if message.type == Data.type:
                    if message.uid == read_count:
                        rec_size += len(message.data)
                        fd.write(message.data)
                        read_flag = True
                        read_count += 1
                        while read_count in received_data:
                            fd.write(received_data[read_count])
                            rec_size += len(received_data[read_count])
                            del received_data[read_count]
                            read_count += 1
                        packet = ACK(read_count - 1).write()  # ACK el último UID correcto
                    elif message.uid > read_count:
                        received_data[message.uid] = message.data
                        sack_blocks.append((message.uid, message.uid + len(message.data)))
                        packet = SACK(sack_blocks).write()  # Enviar SACK con bloques recibidos
                elif message.uid < read_count:
                    read_flag = True
                    logger.debug(f"Reenviamos el ACK {message.uid} para sincronizar")
                    packet = ACK(message.uid).write()
            if not read_flag:
                packet = NACK(read_count).write()  # NACK si no se recibió el paquete esperado
            queue.send(generate_checksum(packet))
            logger.info("Descarga {:,.3f}%".format((rec_size / size) * 100))
        except timeout as e:
            timeout_count += 1
            if timeout_count > MAX_TIMES_TIMEOUT:
                logger.error("La espera de datos hizo timeout")
                raise e
    logger.info("Archivo recibido con éxito.")


def upload(queue: MessageQueue, fd: BinaryIO):
    logger.info("ALGORITMO -> RECOVERY TCP + SELECTIVE ACK")
    queue.set_timeout(TIMEOUT)
    upload_count = 1
    timeout_count = 0
    data = fd.read(READ_SIZE)
    unacked_data = {}  # Datos no confirmados por ACK
    while data != b'' or unacked_data:
        if data:
            packet = Data(upload_count, data).write()
            packet = generate_checksum(packet)
            queue.send(packet)
            unacked_data[upload_count] = data  # Guardamos los datos enviados
            data = fd.read(READ_SIZE)
            upload_count += 1
        logger.debug(f"Esperamos ACK o SACK {upload_count - 1}")
        try:
            receive = queue.recv()
            timeout_count = 0
            check, rec_data = verify_checksum(receive)
            if check:
                message = Message.read(rec_data)
                if message.type == ACK.type:
                    # Confirmamos el ACK, removemos el paquete de unacked_data
                    if message.uid in unacked_data:
                        logger.debug(f"Recibimos ACK {message.uid}")
                        del unacked_data[message.uid]
                elif message.type == SACK.type:
                    # Retransmitimos los bloques perdidos indicados por el SACK
                    logger.debug(f"Recibimos SACK con bloques {message.received_blocks}")
                    for start, end in message.received_blocks:
                        for uid in range(start, end):
                            if uid in unacked_data:
                                packet = Data(uid, unacked_data[uid]).write()
                                packet = generate_checksum(packet)
                                queue.send(packet)
        except timeout as e:
            timeout_count += 1
            if timeout_count > MAX_TIMES_TIMEOUT:
                logger.error("La espera del ACK o SACK hizo timeout")
                raise e
    logger.info("Archivo enviado con exito.")