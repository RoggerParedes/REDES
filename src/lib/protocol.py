class Message():
    def __init__(self):
        print("mensaje")


class ACK(Message):
    def __init__(self, seq_number):
        self.seq_number = seq_number
        #print("ACK")
    
    def encode_msg(self):
        return f"{self.seq_number}".encode()
    
    def decode_msg(self, msg_recv):
        #self.seq_number = 
        return int(msg_recv.decode())

    def get_seq_num(self):
        return self.seq_number

    

class SYN(Message):
    def __init__(self, filename, filesize, seq_number):
        self.filename = filename
        self.filesize = filesize
        self.seq_number = seq_number
        """
        El cliente le envia al servidor el nombre del archivo y el tamanio
        """
    def ret_filename(self):
        return self.filename
    
    def encode_msg(self):
        return f"{self.filename}|{self.filesize}|{self.seq_number}".encode()

    def decode_msg(self, msg_recv):

        decoded_msg = msg_recv.decode()

        parts = decoded_msg.split("|")
        
        self.filename = parts[0]
        self.filesize = int(parts[1])
        self.seq_number = int(parts[2])

    def get_seq_number(self):
        return self.seq_number

        



class DATA(Message):
    def __init__(self, seq_number, data):
        self.seq_number = seq_number
        self.data = data

    def encode_msg(self):
        return f"{self.seq_number}|{self.data.decode()}".encode()
    
    def decode_msg(self, msg_recv):
        decoded_msg = msg_recv.decode()

        parts = decoded_msg.split("|")
        
        self.seq_number = int(parts[0])
        self.data = parts[1]

    def get_seq_number(self):
        return self.seq_number      

    def get_data(self):
        return self.data



class FIN(Message):
    def __init__(self):
        """
        
        """
    def encode_msg(self):
        return "FIN".encode()
    
    def decode_msg(self, msg_recv):
        return msg_recv.decode()   #ver q hacemos c esta func si es necesario el return o no