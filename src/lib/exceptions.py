from lib.logger import *
import os

def validate_port(port: int):
    if port < 1024 or port > 49151:
        raise InvalidPortException
    if port == 8080 or port == 8443:
        raise InvalidPortException


def validate_directory(path: str):
    print(f"Validando ruta: {path}")
    if os.path.exists(path):
        print("Ruta valida")
    else:
        raise InvalidDirectoryException


class InvalidPortException(Exception):
    def __init__(self):
        logger.error("Debe ingresar un puerto mayor a 1024, menor a 49151, distinto del 8080 y del 8443.")

class InvalidDirectoryException(Exception):
    def __init__(self):
        logger.error("Debe ingresar un directorio del servidor valido.")