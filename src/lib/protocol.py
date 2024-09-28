class UnknownMessage(Exception):
    pass

class Message():
    type: int
    uid: int

    # toda clase hija la implemnta \ interface
    def write(self) -> bytes:
        return bytes()
    
    @classmethod
    def read(cls, value: bytes):
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
        raise UnknownMessage("Mensaje malformado.")

class Start(Message):
    type = 1
    uid = 0
    operation: int
    file_size: int
    file_name: str

    def __init__(self, operation, file_size, file_name) -> None:
        self.operation = operation
        self.file_size = file_size
        self.file_name = file_name
    
    def write(self) -> bytes:
        return self.type.to_bytes(1, 'big') + \
        self.uid.to_bytes(4, 'big') + \
        self.operation(1, 'big') + \
        self.file_size(4, 'big') + \
        self.file_name.encode('utf8')
        
    @classmethod
    def read(cls, value: bytes):
        operation = value[5]
        file_size = int.from_bytes(value[6:10], 'big')
        file_name = value[10:].decode('utf8')
        return Start(operation, file_size, file_name)

# tamanio fijo 65536
class Data(Message):
    # uid incremental
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

    # uid indica q paquete reenviar
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
            return 'file not found'
        return 'unknown error'
