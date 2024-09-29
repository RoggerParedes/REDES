import socket
import time
from constants import *
from protocol import *
import os


# ver si el seq_num lo incrementamos de a 1 o por bytes
# dependiendo como esta implementado el resto

# agregar el tipo de mensaje al principio?

def receive_file(sock, filename, filesize):

    while True:
        msg_recv, client_address = sock.recvfrom(BUFFSIZE)
        syn_msg = SYN("", 0, 0)
        syn_msg.decode_msg(msg_recv)
        syn_seq_number = syn_msg.get_seq_number()

        ack_msg = ACK(syn_seq_number)
        sock.sendto(ack_msg.encode_msg(), client_address)
        print(f"ACK enviado para SYN: {syn_seq_number}")

        current_seq_number = syn_seq_number

        with open(filename, 'wb') as file_receiving:
            total_bytes_received = 0
            while total_bytes_received < filesize:
                try:
                    sock.settimeout(TIMEOUT)
                    msg_recv, _ = sock.recvfrom(BUFFSIZE)

                    data_msg = DATA(0, b"")
                    data_msg.decode_msg(msg_recv)
                    data_seq_number = data_msg.get_seq_number()
                    data_data = data_msg.get_data()

                    if data_seq_number == current_seq_number:
                        file_receiving.write(data_data)
                        total_bytes_received += len(data_data)
                        current_seq_number += 1

                        ack_msg = ACK(data_seq_number)
                        sock.sendto(ack_msg.encode_msg(), client_address)
                        print(f"ACK enviado para DATA: {data_seq_number}")
                    else:
                        ack_msg = ACK(current_seq_number)
                        sock.sendto(ack_msg.encode_msg(), client_address)
                        print(f"ACK reenviado para el último DATA: {current_seq_number}")

                except socket.timeout:
                    print("Timeout al recibir DATA, retransmitiendo...")

        fin_msg_recv, _ = sock.recvfrom(BUFFSIZE)
        fin_msg = FIN()
        fin_msg.decode_msg(fin_msg_recv)

        print("Recepción de archivo completa")
        break


    # escucho y agarro SYN
    # mando ACK
    # creo y abro el archivo 
    # escucho y agarro DATA, chequeo numero de secuencia
        # si coincide hago write y mando ACK
        # si no coincide mando ACK con el nro de secuencia anterior?
    # llega FIN


def send_file(sock, address, filename, filepath): #el "three-way handshake" tendríamos que hacerlo acá o en client_handdler
    
    
    #---------------------------------------------------------------
    seq_number = 0

    syn_msg = SYN(filename, os.path.getsize(filepath), seq_number)
    syn_msg_encoded = syn_msg.encode_msg()

    retries = 0

    while retries < 4:
        try:
            sock.sendto(syn_msg_encoded, address)
            print("SYN enviado")
            sock.settimeout(TIMEOUT)

            msg_recv, _ = sock.recvfrom(BUFFSIZE)
            ack_msg = ACK(0)
            ack_msg.decode_msg(msg_recv)

            if ack_msg.get_seq_num() != seq_number:
                print("Número de secuencia de ACK no coincide con SYN, abortando")
                break
            else:
                retries += 1
        
        except socket.timeout: 
            print("retransmite SYN por timeout")
            retries += 1

    if retries == 3:
        print("Falló la sincronización, abortando transmisión") #después de tres intentos aborta la transmisión
        return

    #---------------------------------------------------------------

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
                    ack_msg = ACK(0)
                    ack_msg.decode_msg(msg_recv)
                    
                    if ack_msg.get_seq_num() == seq_number:
                        break

                except socket.timeout: 
                    print("retransmite DATA por timeout")

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