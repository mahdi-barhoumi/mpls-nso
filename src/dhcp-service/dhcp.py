import socket
import struct
import json
import time
import random
import os
from threading import Thread

# DHCP Message Type Options
DHCP_DISCOVER = 1
DHCP_OFFER = 2
DHCP_REQUEST = 3
DHCP_ACK = 5
DHCP_NAK = 6
DHCP_RELEASE = 7

# DHCP Options
DHCP_MESSAGE_TYPE = 53
DHCP_SERVER_ID = 54
DHCP_REQUESTED_IP = 50
DHCP_LEASE_TIME = 51
DHCP_SUBNET_MASK = 1
DHCP_ROUTER = 3
DHCP_DNS = 6
DHCP_HOSTNAME = 12
DHCP_END = 255
DHCP_BOOTFILE = 67
DHCP_TFTP_SERVER_NAME = 66
DHCP_TFTP_SERVER_IP = 150 

class DHCPServer:
    def __init__(self, server_ip, start_ip, end_ip, subnet_mask, config_filename, tftp_server_ip, tftp_server_name=None, lease_time=86400, lease_file='dhcp_leases.json'):
        self.server_ip = server_ip
        self.start_ip = self.ip_to_int(start_ip)
        self.end_ip = self.ip_to_int(end_ip)
        self.subnet_mask = subnet_mask
        self.tftp_server_ip = tftp_server_ip
        self.tftp_server_name = tftp_server_name
        self.config_filename = config_filename
        self.lease_time = lease_time  # 24 hours in seconds
        self.lease_file = lease_file
        self.leases = self.load_leases()
        
        # Create socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.bind((server_ip, 67))
    
    def ip_to_int(self, ip):
        return struct.unpack('!I', socket.inet_aton(ip))[0]
    
    def int_to_ip(self, ip_int):
        return socket.inet_ntoa(struct.pack('!I', ip_int))
    
    def load_leases(self):
        if not os.path.exists(self.lease_file):
            return {}
        try:
            with open(self.lease_file, 'r') as f:
                leases = json.load(f)
                
                # Convert to the format we use internally
                result = {}
                for mac, lease_data in leases.items():
                    # Check if lease is still valid
                    if lease_data['expiry'] > time.time():
                        result[mac] = lease_data
                
                return result
        except Exception as e:
            print(f'Error loading leases: {e}')
            return {}
    
    def save_leases(self):
        try:
            with open(self.lease_file, 'w') as f:
                json.dump(self.leases, f, indent=2)
        except Exception as e:
            print(f'Error saving leases: {e}')
    
    def get_available_ip(self, client_mac, requested_ip=None):
        # Check if client already has a lease
        if client_mac in self.leases and self.leases[client_mac]['expiry'] > time.time():
            return self.leases[client_mac]['ip']
            
        # Check if the requested IP is available and in our range
        if requested_ip:
            requested_ip_int = self.ip_to_int(requested_ip)
            if (self.start_ip <= requested_ip_int <= self.end_ip and 
                not any(lease['ip'] == requested_ip for mac, lease in self.leases.items() 
                        if mac != client_mac and lease['expiry'] > time.time())):
                return requested_ip
        
        # Allocate a new IP
        allocated_ips = {lease['ip'] for mac, lease in self.leases.items() 
                        if mac != client_mac and lease['expiry'] > time.time()}
        
        for ip_int in range(self.start_ip, self.end_ip + 1):
            ip = self.int_to_ip(ip_int)
            if ip not in allocated_ips:
                return ip
                
        return None  # No available IPs
    
    def create_dhcp_packet(self, client_packet, message_type, yiaddr='0.0.0.0'):
        # Extract data from client packet
        xid = client_packet[4:8]  # Transaction ID
        client_mac = client_packet[28:34]  # Client MAC address
        giaddr = client_packet[24:28]  # Gateway IP address
        
        # Create DHCP packet
        packet = b''
        packet += b'\x02'  # Message type: Boot Reply
        packet += b'\x01'  # Hardware type: Ethernet
        packet += b'\x06'  # Hardware address length: 6
        packet += b'\x00'  # Hops: 0
        packet += xid  # Transaction ID
        packet += b'\x00\x00'  # Seconds elapsed: 0
        packet += b'\x80\x00'  # Flags: Broadcast
        packet += b'\x00\x00\x00\x00'  # Client IP: 0.0.0.0
        packet += socket.inet_aton(yiaddr)  # Your IP
        packet += socket.inet_aton(self.server_ip)  # Server IP
        packet += giaddr  # Preserve the original gateway IP
        
        # Client hardware address (MAC + padding)
        packet += client_mac + b'\x00' * 10
        
        # Server name (64 bytes, padded with zeros)
        packet += b'\x00' * 64
        
        # Boot file name (128 bytes, padded with zeros)
        packet += b'\x00' * 128
        
        # Magic cookie: DHCP
        packet += b'\x63\x82\x53\x63'
        
        # DHCP message type
        packet += struct.pack('!BBB', DHCP_MESSAGE_TYPE, 1, message_type)
        
        # DHCP server identifier
        packet += struct.pack('!BB4s', DHCP_SERVER_ID, 4, socket.inet_aton(self.server_ip))
        
        # Lease time
        packet += struct.pack('!BBI', DHCP_LEASE_TIME, 4, self.lease_time)
        
        # Subnet mask
        packet += struct.pack('!BB4s', DHCP_SUBNET_MASK, 4, socket.inet_aton(self.subnet_mask))
        
        # Router (gateway)
        packet += struct.pack('!BB4s', DHCP_ROUTER, 4, socket.inet_aton(self.server_ip))
        
        # DNS server (using the DHCP server as DNS server)
        packet += struct.pack('!BB4s', DHCP_DNS, 4, socket.inet_aton(self.server_ip))
        
        # TFTP Server IP
        packet += struct.pack('!BB4s', DHCP_TFTP_SERVER_IP, 4, socket.inet_aton(self.tftp_server_ip))
        
        # TFTP Server Name
        packet += struct.pack('!BB', DHCP_TFTP_SERVER_NAME, len(self.tftp_server_name))
        packet += self.tftp_server_name.encode('ascii')
        
        # Config File Name
        packet += struct.pack('!BB', DHCP_BOOTFILE, len(self.config_filename))
        packet += self.config_filename.encode('ascii')
        
        # End option
        packet += struct.pack('!B', DHCP_END)
        
        # Pad to minimum size if needed
        if len(packet) < 300:
            packet += b'\x00' * (300 - len(packet))
            
        return packet
    
    def process_dhcp_discover(self, data, addr, giaddr):
        print('Processing DHCP DISCOVER')
        client_mac = data[28:34].hex(':')
        
        # Extract hostname from options
        hostname = 'Unknown'
        options_start = data.find(b'\x63\x82\x53\x63') + 4
        i = options_start
        
        while i < len(data) and data[i] != DHCP_END:
            option = data[i]
            if option == DHCP_HOSTNAME:
                length = data[i+1]
                hostname = data[i+2:i+2+length].decode('utf-8', errors='ignore')
                break
            elif option == 0:  # Padding
                i += 1
                continue
            else:
                length = data[i+1]
                i += 2 + length
        
        # Get an available IP address
        ip_to_offer = self.get_available_ip(client_mac)
        if not ip_to_offer:
            print(f'No available IP addresses for client {client_mac}')
            return
        
        print(f'Offering IP {ip_to_offer} to client {client_mac} (Hostname: {hostname})')
        
        # Create and send DHCP OFFER
        offer_packet = self.create_dhcp_packet(data, DHCP_OFFER, ip_to_offer)
        
        # If giaddr is not 0.0.0.0, send to relay agent instead of broadcasting
        if giaddr != '0.0.0.0':
            print(f'Sending offer via relay agent at {giaddr}')
            self.sock.sendto(offer_packet, (giaddr, 67))
        else:
            self.sock.sendto(offer_packet, ('255.255.255.255', 68))
    
    def process_dhcp_request(self, data, addr):
        print('Processing DHCP REQUEST')
        client_mac = data[28:34].hex(':')
        
        # Extract hostname from options
        hostname = 'Unknown'
        requested_ip = None
        options_start = data.find(b'\x63\x82\x53\x63') + 4
        i = options_start
        
        while i < len(data) and data[i] != DHCP_END:
            option = data[i]
            if option == DHCP_HOSTNAME:
                length = data[i+1]
                hostname = data[i+2:i+2+length].decode('utf-8', errors='ignore')
                i += 2 + length
            elif option == DHCP_REQUESTED_IP:
                length = data[i+1]
                requested_ip = socket.inet_ntoa(data[i+2:i+2+length])
                i += 2 + length
            elif option == 0:  # Padding
                i += 1
                continue
            else:
                length = data[i+1]
                i += 2 + length
        
        # Check if the requested IP is available
        available_ip = self.get_available_ip(client_mac, requested_ip)
        
        if available_ip and (not requested_ip or available_ip == requested_ip):
            # Create lease with hostname
            self.leases[client_mac] = {
                'ip': available_ip,
                'hostname': hostname,  # Added hostname to lease info
                'expiry': time.time() + self.lease_time
            }
            self.save_leases()
            
            print(f'Acknowledging IP {available_ip} to client {client_mac} (Hostname: {hostname})')
            
            # Send DHCP ACK
            ack_packet = self.create_dhcp_packet(data, DHCP_ACK, available_ip)
            self.sock.sendto(ack_packet, ('255.255.255.255', 68))
        else:
            print(f'Requested IP {requested_ip} not available for client {client_mac}')
            
            # Send DHCP NAK
            nak_packet = self.create_dhcp_packet(data, DHCP_NAK)
            self.sock.sendto(nak_packet, ('255.255.255.255', 68))
    
    def process_dhcp_release(self, data, addr):
        print('Processing DHCP RELEASE')
        client_mac = data[28:34].hex(':')
        
        if client_mac in self.leases:
            released_ip = self.leases[client_mac]['ip']
            hostname = self.leases[client_mac].get('hostname', 'Unknown')
            print(f'Client {client_mac} (Hostname: {hostname}) released IP {released_ip}')
            del self.leases[client_mac]
            self.save_leases()
    
    def parse_dhcp_options(self, data):
        options = {}
        options_start = data.find(b'\x63\x82\x53\x63') + 4
        i = options_start
        
        while i < len(data) and data[i] != DHCP_END:
            option = data[i]
            if option == 0:  # Padding
                i += 1
                continue
            
            if i + 1 >= len(data):
                break
                
            length = data[i+1]
            value = data[i+2:i+2+length]
            options[option] = value
            i += 2 + length
        
        return options
    
    def process_packet(self, data, addr):
        if len(data) < 240:  # Minimum DHCP packet size
            return
            
        # Check for DHCP Magic Cookie
        if data[236:240] != b'\x63\x82\x53\x63':
            return
            
        # Extract giaddr (bytes 24-27 in the DHCP packet)
        giaddr = socket.inet_ntoa(data[24:28])
        
        options = self.parse_dhcp_options(data)
        
        if DHCP_MESSAGE_TYPE in options:
            message_type = options[DHCP_MESSAGE_TYPE][0]
            
            if message_type == DHCP_DISCOVER:
                self.process_dhcp_discover(data, addr, giaddr)
            elif message_type == DHCP_REQUEST:
                self.process_dhcp_request(data, addr)
            elif message_type == DHCP_RELEASE:
                self.process_dhcp_release(data, addr)
    
    def run(self):
        print(f'DHCP Server running on {self.server_ip}')
        print(f'Offering IP range: {self.int_to_ip(self.start_ip)} - {self.int_to_ip(self.end_ip)}')
        
        try:
            self.sock.settimeout(3)
            while True:
                try:
                    data, addr = self.sock.recvfrom(1024)
                    Thread(target=self.process_packet, args=(data, addr)).start()
                except socket.timeout:
                    continue
        
        except KeyboardInterrupt:
            print('Stopping DHCP Server...')
            
        finally:
            self.sock.close()

if __name__ == '__main__':
    server = DHCPServer(
        server_ip='192.168.100.1',
        start_ip='192.168.100.100',
        end_ip='192.168.100.200',
        subnet_mask='255.255.255.0',
        config_filename='router-confg', 
        tftp_server_ip='192.168.100.1',
        tftp_server_name=None,
        lease_time=86400,
        lease_file='dhcp_leases.json'
    )
    server.run()