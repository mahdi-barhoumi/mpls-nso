import socket
import struct
import time
import random
import os
import logging
from threading import Thread, Event
from datetime import datetime, timedelta
from django.utils import timezone
from core.models import DHCPLease
from core.settings import Settings

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

# Fixed config filename
CONFIG_FILENAME = "router-confg"

class DHCPServer:
    def __init__(self): 
        self.server_ip = None
        self.start_ip = None
        self.end_ip = None
        self.subnet_mask = None
        self.tftp_server_ip = None
        self.config_filename = CONFIG_FILENAME
        self.lease_time = None
        self.sock = None
        self.running = False
        self.stop_event = Event()
        self.server_thread = None
        self.logger = logging.getLogger('dhcp')
    
    def ip_to_int(self, ip):
        return struct.unpack('!I', socket.inet_aton(ip))[0]
    
    def int_to_ip(self, ip_int):
        return socket.inet_ntoa(struct.pack('!I', ip_int))
    
    def get_active_leases_from_db(self):
        return DHCPLease.objects.filter(expiry_time__gt=timezone.now())
    
    def get_lease_by_mac(self, mac_address):
        try:
            return DHCPLease.objects.get(mac_address=mac_address, expiry_time__gt=timezone.now())
        except DHCPLease.DoesNotExist:
            return None
    
    def create_or_update_lease(self, mac_address, ip_address, hostname, lease_time_seconds):
        expiry_time = timezone.now() + timedelta(seconds=lease_time_seconds)
        
        updated = DHCPLease.objects.filter(mac_address=mac_address).update(
            ip_address=ip_address,
            hostname=hostname,
            expiry_time=expiry_time,
            last_updated=timezone.now()
        )
        
        if not updated:
            DHCPLease.objects.create(
                mac_address=mac_address,
                ip_address=ip_address,
                hostname=hostname,
                expiry_time=expiry_time,
                last_updated=timezone.now()
            )
    
    def delete_lease(self, mac_address):
        DHCPLease.objects.filter(mac_address=mac_address).delete()
    
    def get_available_ip(self, client_mac, requested_ip=None):
        existing_lease = self.get_lease_by_mac(client_mac)
        if existing_lease:
            return existing_lease.ip_address
            
        if requested_ip:
            requested_ip_int = self.ip_to_int(requested_ip)
            if self.start_ip <= requested_ip_int <= self.end_ip:
                if not DHCPLease.objects.filter(ip_address=requested_ip, expiry_time__gt=timezone.now()).exclude(mac_address=client_mac).exists():
                    return requested_ip
        
        allocated_ips = set(lease.ip_address for lease in self.get_active_leases_from_db() if lease.mac_address != client_mac)
        
        for ip_int in range(self.start_ip, self.end_ip + 1):
            ip = self.int_to_ip(ip_int)
            if ip not in allocated_ips:
                return ip
                
        return None
    
    def create_dhcp_packet(self, client_packet, message_type, yiaddr='0.0.0.0'):
        xid = client_packet[4:8]
        client_mac = client_packet[28:34]
        giaddr = client_packet[24:28]
        
        packet = b''
        packet += b'\x02'
        packet += b'\x01'
        packet += b'\x06'
        packet += b'\x00'
        packet += xid
        packet += b'\x00\x00'
        packet += b'\x80\x00'
        packet += b'\x00\x00\x00\x00'
        packet += socket.inet_aton(yiaddr)
        packet += socket.inet_aton(self.server_ip)
        packet += giaddr
        
        packet += client_mac + b'\x00' * 10
        packet += b'\x00' * 64
        packet += b'\x00' * 128
        packet += b'\x63\x82\x53\x63'
        
        packet += struct.pack('!BBB', DHCP_MESSAGE_TYPE, 1, message_type)
        packet += struct.pack('!BB4s', DHCP_SERVER_ID, 4, socket.inet_aton(self.server_ip))
        packet += struct.pack('!BBI', DHCP_LEASE_TIME, 4, self.lease_time)
        packet += struct.pack('!BB4s', DHCP_SUBNET_MASK, 4, socket.inet_aton(self.subnet_mask))
        packet += struct.pack('!BB4s', DHCP_ROUTER, 4, socket.inet_aton(self.server_ip))
        packet += struct.pack('!BB4s', DHCP_DNS, 4, socket.inet_aton(self.server_ip))
        packet += struct.pack('!BB4s', DHCP_TFTP_SERVER_IP, 4, socket.inet_aton(self.tftp_server_ip))
        
        packet += struct.pack('!BB', DHCP_BOOTFILE, len(self.config_filename))
        packet += self.config_filename.encode('ascii')
        
        packet += struct.pack('!B', DHCP_END)
        
        if len(packet) < 300:
            packet += b'\x00' * (300 - len(packet))
            
        return packet
    
    def process_dhcp_discover(self, data, addr, giaddr):
        self.logger.info('Processing DHCP DISCOVER')
        client_mac = data[28:34].hex(':')
        
        hostname = 'Unknown'
        options_start = data.find(b'\x63\x82\x53\x63') + 4
        i = options_start
        
        while i < len(data) and data[i] != DHCP_END:
            option = data[i]
            if option == DHCP_HOSTNAME:
                length = data[i+1]
                hostname = data[i+2:i+2+length].decode('utf-8', errors='ignore')
                break
            elif option == 0:
                i += 1
                continue
            else:
                length = data[i+1]
                i += 2 + length
        
        ip_to_offer = self.get_available_ip(client_mac)
        if not ip_to_offer:
            self.logger.warning(f'No available IP addresses for client {client_mac}')
            return
        
        self.logger.info(f'Offering IP {ip_to_offer} to client {client_mac} (Hostname: {hostname})')
        
        offer_packet = self.create_dhcp_packet(data, DHCP_OFFER, ip_to_offer)
        
        if giaddr != '0.0.0.0':
            self.logger.info(f'Sending offer via relay agent at {giaddr}')
            self.sock.sendto(offer_packet, (giaddr, 67))
        else:
            self.sock.sendto(offer_packet, ('255.255.255.255', 68))
    
    def process_dhcp_request(self, data, addr):
        self.logger.info('Processing DHCP REQUEST')
        client_mac = data[28:34].hex(':')
        
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
            elif option == 0:
                i += 1
                continue
            else:
                length = data[i+1]
                i += 2 + length
        
        available_ip = self.get_available_ip(client_mac, requested_ip)
        
        if available_ip and (not requested_ip or available_ip == requested_ip):
            self.create_or_update_lease(
                mac_address=client_mac,
                ip_address=available_ip,
                hostname=hostname,
                lease_time_seconds=self.lease_time
            )
            
            self.logger.info(f'Acknowledging IP {available_ip} to client {client_mac} (Hostname: {hostname})')
            
            ack_packet = self.create_dhcp_packet(data, DHCP_ACK, available_ip)
            self.sock.sendto(ack_packet, ('255.255.255.255', 68))
        else:
            self.logger.warning(f'Requested IP {requested_ip} not available for client {client_mac}')
            
            nak_packet = self.create_dhcp_packet(data, DHCP_NAK)
            self.sock.sendto(nak_packet, ('255.255.255.255', 68))
    
    def process_dhcp_release(self, data, addr):
        self.logger.info('Processing DHCP RELEASE')
        client_mac = data[28:34].hex(':')
        
        lease = self.get_lease_by_mac(client_mac)
        if lease:
            released_ip = lease.ip_address
            hostname = lease.hostname
            self.logger.info(f'Client {client_mac} (Hostname: {hostname}) released IP {released_ip}')
            
            self.delete_lease(client_mac)
    
    def parse_dhcp_options(self, data):
        options = {}
        options_start = data.find(b'\x63\x82\x53\x63') + 4
        i = options_start
        
        while i < len(data) and data[i] != DHCP_END:
            option = data[i]
            if option == 0:
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
        if len(data) < 240:
            return
            
        if data[236:240] != b'\x63\x82\x53\x63':
            return
            
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
    
    def server_loop(self):
        self.logger.info(f'DHCP server running on {self.server_ip}')
        self.logger.info(f'Offering IP range: {self.int_to_ip(self.start_ip)} - {self.int_to_ip(self.end_ip)}')
        
        try:
            self.sock.settimeout(1)
            while not self.stop_event.is_set():
                try:
                    data, addr = self.sock.recvfrom(1024)
                    self.process_packet(data, addr)
                except socket.timeout:
                    continue
        
        except Exception as e:
            self.logger.error(f'Error in DHCP server: {e}')
            
        finally:
            if self.sock:
                self.sock.close()
                self.sock = None
            self.running = False
            self.logger.info('DHCP server stopped')
    
    def start(self):
        if self.running:
            self.logger.warning("DHCP server is already running")
            return False
        
        try:
            # Get settings from the Settings model
            settings = Settings.get_settings()
            
            # Set server parameters from settings
            self.server_ip = settings.host_ip
            self.start_ip = self.ip_to_int(settings.dhcp_ip_range_start)
            self.end_ip = self.ip_to_int(settings.dhcp_ip_range_end)
            self.subnet_mask = settings.host_subnet_mask
            self.tftp_server_ip = settings.host_ip  # Using host IP as TFTP server IP
            self.lease_time = settings.dhcp_lease_time
            self.stop_event.clear()
            
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.sock.bind((self.server_ip, 67))
            
            self.running = True
            self.server_thread = Thread(target=self.server_loop, daemon=True)
            self.server_thread.start()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start DHCP server: {e}")
            if self.sock:
                self.sock.close()
                self.sock = None
            self.running = False
            return False
    
    def stop(self):
        if not self.running:
            self.logger.warning("DHCP server is not running")
            return False
            
        self.logger.info("Stopping DHCP server...")
        self.stop_event.set()
        
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=5)
            
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None
            
        self.running = False
        return True
    
    def is_running(self):
        return self.running
    
    def get_status(self):
        status = {
            "running": self.running,
            "config": {
                "server_ip": self.server_ip,
                "ip_range": f"{self.int_to_ip(self.start_ip) if self.start_ip else None} - {self.int_to_ip(self.end_ip) if self.end_ip else None}",
                "subnet_mask": self.subnet_mask,
                "lease_time": self.lease_time,
                "tftp_server_ip": self.tftp_server_ip
            } if self.running else None
        }
        return status
    
    def get_active_leases(self):
        leases = {}
        for lease in self.get_active_leases_from_db():
            leases[lease.mac_address] = {
                'ip': lease.ip_address,
                'hostname': lease.hostname,
                'expiry': lease.expiry_time.timestamp()
            }
        return leases
