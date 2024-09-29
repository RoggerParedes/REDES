import socket
import time
from .constants import *

class GoBackNPackage:
    def __init__(self, package_id, data):
        self.package_id = package_id
        self.data = data
        self.is_ack = False
        self.timestamp = 0
        self.retry_count = 0

    def serialize(self):
        return self.package_id.to_bytes(ID_SIZE, byteorder='big') + self.data

    def set_timestamp(self):
        self.timestamp = time.time()

    def has_expired(self):
        return time.time() - self.timestamp > TIMEOUT

def go_back_n_send(s, f, send_address, log_level):
    window = []
    next_seq_num = 0
    base = 0
    s.settimeout(TIMEOUT)
    all_file_read = False
    log('Starting send with Go-Back-N', LogLevel.HIGH, log_level)

    while not all_file_read or len(window) > 0:
        # Enviar paquetes dentro del tamaño de ventana permitido
        while len(window) < MAX_WINDOW_SIZE and not all_file_read:
            data = f.read(CHUNK_SIZE - ID_SIZE)
            if not data:
                all_file_read = True
                break
            package = GoBackNPackage(next_seq_num, data)
            window.append(package)
            s.sendto(package.serialize(), send_address)
            package.set_timestamp()
            log(f'Sent package: {next_seq_num}', LogLevel.HIGH, log_level)
            next_seq_num += 1

        try:
            ack, _ = s.recvfrom(ID_SIZE)
            ack_num = int.from_bytes(ack, byteorder='big')
            log(f'Received ack: {ack_num}', LogLevel.HIGH, log_level)
            if ack_num >= base:
                slide = ack_num - base + 1
                window = window[slide:]  # Mueve la ventana
                base = ack_num + 1
        except socket.timeout:
            log('Timeout, resending all packets in the window', LogLevel.NORMAL, log_level)
            for package in window:
                s.sendto(package.serialize(), send_address)
                package.set_timestamp()
                log(f'Resent package: {package.package_id}', LogLevel.HIGH, log_level)

def go_back_n_receive(s, f, client_address, file_size, log_level):
    expected_seq_num = 0
    amount_received = 0
    s.settimeout(TIMEOUT)
    log('Starting receive with Go-Back-N', LogLevel.HIGH, log_level)

    while amount_received < file_size:
        try:
            packet, _ = s.recvfrom(CHUNK_SIZE)
            package_id = int.from_bytes(packet[:ID_SIZE], byteorder='big')
            data = packet[ID_SIZE:]

            if package_id == expected_seq_num:
                f.write(data)
                amount_received += len(data)
                expected_seq_num += 1
                log(f'Received and wrote package: {package_id}', LogLevel.HIGH, log_level)
            else:
                log(f'Out of order package received: {package_id}, expected: {expected_seq_num}', LogLevel.NORMAL, log_level)

            # Enviar ACK del último paquete recibido correctamente
            s.sendto(expected_seq_num.to_bytes(ID_SIZE, byteorder='big'), client_address)
        except socket.timeout:
            log('Timeout waiting for packet, resending ACK', LogLevel.NORMAL, log_level)
            s.sendto(expected_seq_num.to_bytes(ID_SIZE, byteorder='big'), client_address)
