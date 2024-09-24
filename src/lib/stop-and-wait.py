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
    syn_msg_encoded = syn_msg.build_msg()

    sock.sendto(syn_msg_encoded, address)
    print("SYN enviado")

    msg_recv = sock.recvfrom(BUFFSIZE)
    
    recv_seq_number = msg_recv.decode_msg()

    if recv_seq_number == seq_number: 
        with open(filepath, 'rb') as file_sent: #lee de a bytes
            while True:
                data = file_sent.read(BUFFSIZE)
                if not data: #terminó el archivo
                    break
                
                seq_number += 1
                
                data_msg = DATA(seq_number, data)
                data_msg_encoded = data_msg.encode_msg()

                sock.sendto(data_msg_encoded, address)

                #recvfrom()                


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