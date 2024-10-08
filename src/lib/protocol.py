## Parametros del protocolo del programa

# Cuanto leemos de un archivo como maximo
READ_SIZE = 4096

# Cuanto tiempo en segundos usamos de timeout
TIMEOUT = 0.05

# Cuantos timeouts seguidos antes de que tomemos el otro lado de la conexion como muerto
MAX_TIMES_TIMEOUT = 50

# Codigos Numericos
OPERATION_UPLOAD = 0
OPERATION_DOWNLOAD = 1

# Limitacion de nuestro protocolo
MAX_FILE_SIZE = 2**32 - 1


class UnknownMessageException(Exception):
    pass


class Message:
    type: int
    uid: int

    # Nunca se usa, todas las clases hijas deben implementarlo
    def write(self) -> bytes:
        return bytes()

    @classmethod
    def read(cls, value: bytes):  # devuelve una subinstancia
        _type = value[0]
        if _type == Start.type:
            return Start.read(value)
        if _type == Data.type:
            return Data.read(value)
        if _type == ACK.type:
            return ACK(int.from_bytes(value[1:5], 'big'))
        if _type == NACK.type:
            return NACK(int.from_bytes(value[1:5], 'big'))
        if _type == Error.type:
            return Error.read(value)
        raise UnknownMessageException("Mensaje recivido desconocido")


class Start(Message):
    type = 1  # 1b
    uid = 0  # 4b, uid siempre 0
    operation: int  # 1b, 0 indica subida, 1 indica download
    file_size: int  # 1b
    # Mandar codificado utf-8
    file_name: str  # tamaño variable, entre [4b - 4Gb]

    def __init__(self, operation, file_size, file_name):
        self.operation = operation
        self.file_size = file_size
        self.file_name = file_name

    def write(self) -> bytes:
        return self.type.to_bytes(1, 'big') + \
            self.uid.to_bytes(4, 'big') + \
            self.operation.to_bytes(1, 'big') + \
            self.file_size.to_bytes(4, 'big') + \
            self.file_name.encode('utf8')

    @classmethod
    def read(cls, value: bytes):  # devuelve esta clase
        operation = value[5]
        file_size = int.from_bytes(value[6:10], 'big')
        file_name = value[10:].decode('utf8')
        return Start(operation, file_size, file_name)


# Tamaño de data 64kb siempre
class Data(Message):
    # uid es incremental y identifica que numero de paquete es
    type = 2
    data: bytes

    def __init__(self, uid, data):
        self.uid = uid
        self.data = data

    @classmethod
    def read(cls, value: bytes):
        uid = int.from_bytes(value[1:5], 'big')
        return Data(uid, value[5:])

    def write(self) -> bytes:
        return self.type.to_bytes(1, 'big') + \
            self.uid.to_bytes(4, 'big') + \
            self.data


class ACK(Message):
    type = 3

    # uid del siguiente paquete que esperamos
    def __init__(self, uid):
        self.uid = uid

    def write(self) -> bytes:
        return self.type.to_bytes(1, 'big') + \
            self.uid.to_bytes(4, 'big')


class NACK(Message):
    type = 4

    # uid indica cual paquete reenviar
    def __init__(self, uid):
        self.uid = uid

    def write(self) -> bytes:
        return self.type.to_bytes(1, 'big') + \
            self.uid.to_bytes(4, 'big')


class Error(Message):
    type = 5
    uid = 0
    error_type: int
    FILE_NOT_FOUND = 1

    def __init__(self, uid, error_type):
        self.uid = uid
        self.error_type = error_type

    def write(self) -> bytes:
        return self.type.to_bytes(1, 'big') + \
            self.uid.to_bytes(4, 'big') + \
            self.error_type.to_bytes(1, 'big')

    @classmethod
    def read(cls, value: bytes):
        uid = int.from_bytes(value[1:5], 'big')
        error_type = value[5]
        return Error(uid, error_type)

    @classmethod
    def get_error_msg(cls, error_type):
        if error_type == cls.FILE_NOT_FOUND:
            return 'Archivo no encontrado'
        return 'Ocurrio un error desconocido al intentar obtener el archivo'

class SACK(Message):
    type = 6

    def __init__(self, uid, received_blocks):
        self.uid = uid
        self.received_blocks = received_blocks

    def write(self):
        sack_data = ",".join(f"{start}-{end}" for start, end in self.received_blocks)
        return sack_data.encode()

    @classmethod
    def read(cls, data: bytes):
        base_message = Message.read(data)
        sack_data = data[len(base_message):].decode()
        blocks = [(int(start), int(end)) for start, end in (block.split('-') for block in sack_data.split(','))]
        return SACK(base_message.uid, blocks)