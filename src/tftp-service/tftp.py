import socket
import os
import struct

tftp_root = "./tftp_files"
tftp_port = 69
tftp_block_size = 512
tftp_timeout = 10

def handle_tftp_request(sock, addr, data):
    opcode = int.from_bytes(data[:2], byteorder='big')
    parts = data[2:].split(b'\x00')
    
    if len(parts) < 2:
        return 
    
    filename, mode = parts[0].decode(), parts[1].decode()
    filepath = os.path.join(tftp_root, filename)
    
    if opcode == 1:  
        if os.path.exists(filepath):
            with open(filepath, 'rb') as file:
                block_num = 1
                while True:
                    chunk = file.read(tftp_block_size)
                    response = struct.pack('!HH', 3, block_num) + chunk
                    sock.sendto(response, addr)
                    
                    
                    try:
                        ack, _ = sock.recvfrom(4)
                        ack_opcode, ack_block = struct.unpack('!HH', ack)
                        if ack_opcode != 4 or ack_block != block_num:
                            print("ACK incorrect, arrêt de la transmission")
                            break
                    except socket.timeout:
                        print("Timeout, ACK non reçu")
                        break
                    
                    if len(chunk) < tftp_block_size:
                        break  
                    
                    block_num += 1
                
                print(f"File {filename} sent to {addr}")
        else:
            error_msg = struct.pack('!HH', 5, 1) + b'File not found\x00'
            sock.sendto(error_msg, addr)
    else:
        error_msg = struct.pack('!HH', 5, 4) + b'Unsupported operation\x00'
        sock.sendto(error_msg, addr)

def tftp_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("192.168.119.1", tftp_port))  
    sock.settimeout(tftp_timeout) 
    
    print("TFTP Server running on port ",tftp_port)
    
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            handle_tftp_request(sock, addr, data)
        except socket.timeout:
            pass  # 

if __name__ == "__main__":
    os.makedirs(tftp_root, exist_ok=True)
    tftp_server()
