import socket
import time
from constants import *
from protocol import *
import os




def receive_file(sock, filename, filesize):
    data, client_address = sock.recvfrom(BUFFSIZE)
    # chequear isInstance o suponemos que el primer mensaje siempre lo es?
    syn_message = SYN(filename, filesize)

    #ret_filename(syn_message)


    nro_seq, contenido = data.decode().split(":", 1)

    # escucho y agarro SYN
    # mando ACK
    # creo y abro el archivo 
    # escucho y agarro DATA, chequeo numero de secuencia
        # si coincide hago write y mando ACK
        # si no coincide mando ACK con el nro de secuencia anterior?
    # llega FIN


def send_file(sock, address, filename, filepath):
    
    seq_number = 0

    syn_msg = SYN(filename, os.path.getsize(filepath), seq_number)
    syn_msg_encoded = syn_msg.encode_msg()

    sock.sendto(syn_msg_encoded, address)
    print("SYN enviado")

    msg_recv, _ = sock.recvfrom(BUFFSIZE)
    ack_msg_seq_number = ACK.decode_msg(msg_recv)

    
    with open(filepath, 'rb') as file_sending: #lee de a bytes
        while True:
            data = file_sending.read(BUFFSIZE)
            if not data: #terminó el archivo
                break
            
            seq_number += 1
            
            data_msg = DATA(seq_number, data)
            data_msg_encoded = data_msg.encode_msg()
            
            while True: #retransmite hasta que llegue el ACK correcto
                try:
                    sock.sendto(data_msg_encoded, address)
                    print("DATA enviado")
                    sock.settimeout(TIMEOUT)

                    msg_recv, _ = sock.recvfrom(BUFFSIZE)
                    ack_msg_seq_number = ACK.decode_msg(msg_recv)
                    
                    if ack_msg_seq_number == seq_number:
                        break

                except socket.timeout: 
                    print("retransmite DATA por timeout")
                    continue

    fin_msg = FIN()
    sock.sendto(fin_msg.encode_msg(), address)
    print("FIN enviado")

    # mando SYN
    # espero respuesta
    # mando ACK
    
    # abro el archivo
    # armo msj data con tamaño BUFFSIZE
    # lo mando decodificado?
    # espero ACK
    # chequeo numero de ACK
    # si salta el timeout antes se vuelve a enviar el último paquete

    # cuando leí todo el archivo mando mensaje FIN