class Message():
    def __init(self):
        print("mensaje")


class ACK(Message):
    def __init(self):
        print("ACK")
    
    def decode_msg(self):
        return self.decode().split("|")


class SYN(Message):
    def __init(self, filename, filesize, seq_number):
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

    #def decode_msg(self):



class DATA(Message):
    def __init(self, seq_number, data):
        self.seq_number = seq_number
        self.data = data

    def encode_msg(self, seq_number, data):
        return f"{self.seq_number}|{self.data}".encode()

class FIN(Message):
    def __init(self):
        """
        
        """