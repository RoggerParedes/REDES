from lib.logger import logger
import os


class DownloaderNotReadyError(Exception):
    pass


class InvalidPortException(Exception):
    def __init__(self):
        logger.error('Puerto Invalido: debe ingresar un puerto que:\
              \n1) Sea mayor a 1024 \
              \n2) Sea distinto al 8080 y 8443\
              \n3) Sea menor a 65535 valor maximo de un puerto')


class InvalidDirectoryException(Exception):
    def __init__(self):
        logger.error('El directorio ingresado para almacenar los archivos no existe')


def validate_port(port: int):
    used_ports = list(range(0, 1024))
    used_ports.append(8080)
    used_ports.append(8443)
    if port in used_ports or port > 65535 or port < 0:
        raise InvalidPortException()


def validate_directory(directory):
    if not os.path.exists(directory):
        raise InvalidDirectoryException()

def validate_file(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"El archivo en '{path}' no existe.")