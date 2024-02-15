import socket
import struct
import time


if __name__ == '__main__':
    # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # s.connect(('192.168.0.100', 9100))
    try: 
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        print ("Socket successfully created")
    except socket.error as err: 
        print ("socket creation failed with error %s" %(err))
    
    # default port for socket 
    port = 9100
    host_ip = '192.168.0.100'
       
    # connecting to the server 
    client.connect((host_ip, port)) 
    
    print ("the socket has successfully connected to google") 
    
    
    data_out = bytearray("H\x03",'ascii')

    client.send(data_out)