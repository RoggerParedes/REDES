BUFFSIZE = 1024
TIMEOUT = 1
MAX_PACKET_SIZE = 65536  # maximo que permite la red


""" PROTOCOLO """

# Lectura del archivo
READ_SIZE = 64536

# Cuantos timeouts seguidos antes de que tomemos el otro lado de la conexion
# como muerto
MAX_TIMES_TIMEOUT = 3 # A eleccion

# Codigos Numericos
OPERATION_UPLOAD = 0
OPERATION_DOWNLOAD = 1

# Limitacion de nuestro protocolo
MAX_FILE_SIZE = 2**32 - 1  # 4 Gb
