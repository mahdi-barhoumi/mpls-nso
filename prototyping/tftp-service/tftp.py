import socket
import os
import struct
from threading import Thread

# TFTP Opcodes
TFTP_RRQ = 1    # Read Request
TFTP_DATA = 3   # Data Packet
TFTP_ACK = 4    # Acknowledgement
TFTP_ERROR = 5  # Error Packet

# TFTP Error Codes
TFTP_ERROR_FILE_NOT_FOUND = 1
TFTP_ERROR_ACCESS_VIOLATION = 2
TFTP_ERROR_ILLEGAL_OPERATION = 4
TFTP_ERROR_UNKNOWN_TRANSFER_ID = 5

class TFTPServer:
    def __init__(self, root_dir, server_ip, port=69, max_block_size=512):
        # Convert relative path to absolute path
        self.root_dir = os.path.abspath(root_dir)
        self.server_ip = server_ip
        self.port = port
        self.max_block_size = max_block_size
        
        # Ensure root directory exists
        os.makedirs(self.root_dir, exist_ok=True)
        
        # Create main listening socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.server_ip, self.port))
    
    def send_error_packet(self, client_socket, client_address, error_code, error_message):
        error_packet = struct.pack('!HH', TFTP_ERROR, error_code)
        error_packet += error_message.encode('ascii') + b'\x00'
        client_socket.sendto(error_packet, client_address)
    
    def handle_read_request(self, filename, mode, client_socket, client_address):
        full_path = os.path.realpath(os.path.normpath(os.path.join(self.root_dir, filename)))

        if not full_path.startswith(self.root_dir):
            self.send_error_packet(client_socket, client_address, TFTP_ERROR_ACCESS_VIOLATION, "Access denied")
            return

        try:
            with open(full_path, 'rb') as file:
                block_number = 1
                while True:
                    data = file.read(self.max_block_size)

                    # Create data packet
                    packet = struct.pack('!HH', TFTP_DATA, block_number) + data
                    retries = 3

                    while retries > 0:
                        client_socket.sendto(packet, client_address)
                        try:
                            client_socket.settimeout(5)  # Timeout for ACK
                            response, addr = client_socket.recvfrom(1024)

                            # Verify response is from the same client
                            if addr != client_address:
                                self.send_error_packet(client_socket, addr, TFTP_ERROR_UNKNOWN_TRANSFER_ID, "Wrong transfer ID")
                                return

                            # Check for ACK
                            op, recv_block = struct.unpack('!HH', response[:4])
                            if op == TFTP_ACK and recv_block == block_number:
                                break  # ACK received, move to next block

                        except socket.timeout:
                            retries -= 1

                    if retries == 0:
                        print(f"Transfer of {filename} failed due to missing ACK from {client_address}")
                        return

                    if len(data) < self.max_block_size:
                        # Last block was sent successfully and ACK received
                        print(f"Successfully transferred {filename} to {client_address}")
                        return  # Exit function after last block

                    block_number += 1

        except FileNotFoundError:
            self.send_error_packet(client_socket, client_address, TFTP_ERROR_FILE_NOT_FOUND, f"File {filename} not found")
        except PermissionError:
            self.send_error_packet(client_socket, client_address, TFTP_ERROR_ACCESS_VIOLATION, "Permission denied")
        except Exception as e:
            self.send_error_packet(client_socket, client_address, TFTP_ERROR_ILLEGAL_OPERATION, str(e))

    
    def process_request(self, data, client_address):
        try:
            # Parse opcode
            opcode, = struct.unpack('!H', data[:2])
            
            # Extract filename and mode
            filename_end = data.find(b'\x00', 2)
            mode_end = data.find(b'\x00', filename_end + 1)
            
            filename = data[2:filename_end].decode('ascii')
            mode = data[filename_end+1:mode_end].decode('ascii').lower()
            
            # Create a new socket for this transfer
            transfer_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            transfer_socket.bind((self.server_ip, 0))  # Random port
            
            # Only handle read requests
            if opcode == TFTP_RRQ:
                self.handle_read_request(filename, mode, transfer_socket, client_address)
            
            transfer_socket.close()
        
        except Exception as e:
            print(f"Error processing request: {e}")
    
    def run(self):
        print(f'TFTP Server running on {self.server_ip}:{self.port}')
        print(f'Serving files from {self.root_dir}')
        
        try:
            self.sock.settimeout(3)
            while True:
                try:
                    # Receive incoming request
                    data, addr = self.sock.recvfrom(1024)
                    
                    # Process request in a separate thread
                    Thread(target=self.process_request, args=(data, addr)).start()
                
                except socket.timeout:
                    continue
        
        except KeyboardInterrupt:
            print('Stopping TFTP Server...')
        
        finally:
            self.sock.close()

if __name__ == '__main__':
    server = TFTPServer(
        root_dir='./tftp_files',
        server_ip='192.168.100.1',
        port=69,
        max_block_size=512
    )
    server.run()