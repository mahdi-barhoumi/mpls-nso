import socket
import struct
import logging
import ipaddress
from threading import Thread, Event
from datetime import timedelta
from django.utils import timezone
from core.models import DHCPLease, DHCPScope
from core.modules.discovery_scheduler import DiscoveryScheduler
from core.settings import get_settings

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

class _DHCPServer:
    def __init__(self): 
        self.server_ip = None
        self.tftp_server_ip = None
        self.main_scope_address = None
        self.main_scope_subnet_mask = None
        self.config_filename = None
        self.lease_time = 4294967295  # Maximum possible lease time (effectively permanent)
        self.running = False
        self.sock = None
        self.server_thread = None
        self.stop_event = Event()
        self.logger = logging.getLogger('dhcp')
    
    def ip_to_int(self, ip):
        return struct.unpack('!I', socket.inet_aton(ip))[0]
    
    def int_to_ip(self, ip_int):
        return socket.inet_ntoa(struct.pack('!I', ip_int))
    
    def get_active_leases_from_db(self):
        return DHCPLease.objects.filter(active=True)
    
    def get_lease_by_mac(self, mac_address):
        try:
            return DHCPLease.objects.get(mac_address=mac_address)
        except DHCPLease.DoesNotExist:
            return None
    
    def get_available_ip(self, client_mac, relay_ip=None):
        # First, check if client already has a lease
        existing_lease = self.get_lease_by_mac(client_mac)
        if existing_lease:
            # Find the scope this IP belongs to
            ip_obj = ipaddress.ip_address(existing_lease.ip_address)
            
            # Check secondary scopes first
            for scope in DHCPScope.objects.all():
                network = ipaddress.IPv4Network(f"{scope.network}/{scope.subnet_mask}", strict=False)
                if ip_obj in network:
                    return existing_lease.ip_address, scope.subnet_mask
            
            # If not in any secondary scope, must be in main scope
            return existing_lease.ip_address, self.main_scope_subnet_mask
        
        # Get all active leases
        active_leases = set(lease.ip_address for lease in self.get_active_leases_from_db())
        
        # If no relay agent is involved, only check the main scope
        if not relay_ip or relay_ip == '0.0.0.0':
            network = ipaddress.IPv4Network(f"{self.main_scope_address}/{self.main_scope_subnet_mask}", strict=False)
            
            # Normal IP allocation for main scope
            for ip in network.hosts():
                ip_str = str(ip)
                
                # Skip server IP
                if (ip_str == self.server_ip or 
                    ip_str in active_leases):
                    continue
                
                return ip_str, self.main_scope_subnet_mask
            
            return None, None
        
        # If relay agent is involved, find the matching secondary scope
        secondary_scopes = DHCPScope.objects.all()
        for scope in secondary_scopes:
            # Check if the scope is active
            if not scope.is_active:
                continue

            network = ipaddress.IPv4Network(f"{scope.network}/{scope.subnet_mask}", strict=False)
            
            # Check if relay IP is in this scope
            if ipaddress.ip_address(relay_ip) in network:
                # Offer the last host address of this scope
                last_host = str(list(network.hosts())[-1])
                
                # Check if last host is available
                if last_host not in active_leases:
                    return last_host, scope.subnet_mask
                
                # If last host is not available, return None
                return None, None
        
        # If no matching scope found for relay IP
        return None, None
    
    def create_or_update_lease(self, mac_address, ip_address, hostname=None):
        updated = DHCPLease.objects.filter(mac_address=mac_address).update(
            ip_address=ip_address,
            hostname=hostname or 'Unknown',
            active=True,
            last_updated=timezone.now()
        )
        
        if not updated:
            DHCPLease.objects.create(
                mac_address=mac_address,
                ip_address=ip_address,
                hostname=hostname or 'Unknown',
                active=True,
                last_updated=timezone.now()
            )
    
    def delete_lease(self, mac_address):
        # Instead of deleting, mark as inactive
        DHCPLease.objects.filter(mac_address=mac_address).update(active=False)
    
    def create_dhcp_packet(self, client_packet, message_type, yiaddr='0.0.0.0', subnet_mask=None):
        xid = client_packet[4:8]
        client_mac = client_packet[28:34]
        giaddr = client_packet[24:28]
        
        # If no specific subnet mask is provided, use the main one
        if subnet_mask is None:
            subnet_mask = self.main_scope_subnet_mask
        
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
        packet += struct.pack('!BB4s', DHCP_SUBNET_MASK, 4, socket.inet_aton(subnet_mask))
        packet += struct.pack('!BB4s', DHCP_ROUTER, 4, socket.inet_aton(self.server_ip))
        packet += struct.pack('!BB4s', DHCP_DNS, 4, socket.inet_aton(self.server_ip))
        packet += struct.pack('!BB4s', DHCP_TFTP_SERVER_IP, 4, socket.inet_aton(self.tftp_server_ip))
        
        packet += struct.pack('!BB', DHCP_BOOTFILE, len(self.config_filename))
        packet += self.config_filename.encode('ascii')
        
        packet += struct.pack('!B', DHCP_END)
        
        if len(packet) < 300:
            packet += b'\x00' * (300 - len(packet))
            
        return packet
    
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
        
        # If a relay agent is involved, pass its IP
        ip_to_offer, subnet_mask = self.get_available_ip(client_mac, relay_ip=giaddr if giaddr != '0.0.0.0' else None)
        
        if not ip_to_offer:
            self.logger.warning(f'No available IP addresses for client {client_mac} (Hostname: {hostname})')
            return
        
        self.logger.info(f'Offering IP {ip_to_offer}/{subnet_mask} to client {client_mac} (Hostname: {hostname})')
        
        offer_packet = self.create_dhcp_packet(data, DHCP_OFFER, ip_to_offer, subnet_mask)
        
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
        giaddr = socket.inet_ntoa(data[24:28])
        
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
        
        # If a relay agent is involved, pass its IP
        available_ip, subnet_mask = self.get_available_ip(
            client_mac, 
            relay_ip=giaddr if giaddr != '0.0.0.0' else None
        )
        
        if available_ip and (not requested_ip or available_ip == requested_ip):
            # Check if this is the first time this MAC has received a lease
            is_first_time = not self.get_lease_by_mac(client_mac)
            self.create_or_update_lease(
                mac_address=client_mac,
                ip_address=available_ip,
                hostname=hostname
            )
            
            self.logger.info(f'Acknowledging IP {available_ip}/{subnet_mask} to client {client_mac} (Hostname: {hostname})')
            
            # Schedule discovery with is_first_time flag
            DiscoveryScheduler.schedule_discovery(available_ip, is_first_time=is_first_time)
            
            ack_packet = self.create_dhcp_packet(data, DHCP_ACK, available_ip, subnet_mask)
            
            if giaddr != '0.0.0.0':
                self.sock.sendto(ack_packet, (giaddr, 67))
            else:
                self.sock.sendto(ack_packet, ('255.255.255.255', 68))
        else:
            self.logger.warning(f'Requested IP {requested_ip} not available for client {client_mac}')
            
            nak_packet = self.create_dhcp_packet(data, DHCP_NAK)
            
            if giaddr != '0.0.0.0':
                self.sock.sendto(nak_packet, (giaddr, 67))
            else:
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
        self.logger.info(f'Main scope: {self.main_scope_address}/{self.main_scope_subnet_mask}')
        
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
    
    def start(self, server_ip=None, tftp_server_ip=None, main_scope_address=None, main_scope_subnet_mask=None, config_filename=CONFIG_FILENAME):
        if self.running:
            self.logger.warning("DHCP server is already running")
            return False
        
        try:
            # Get system settings
            settings = get_settings()
            if not settings:
                self.logger.warning("Cannot start DHCP server: No system settings found")
                return False
            
            # Set server parameters using provided values or defaults from settings
            self.server_ip = server_ip or settings.host_address
            self.tftp_server_ip = tftp_server_ip or settings.host_address
            self.main_scope_address = main_scope_address or settings.dhcp_provider_network_address
            self.main_scope_subnet_mask = main_scope_subnet_mask or settings.dhcp_provider_network_subnet_mask
            self.config_filename = config_filename
            
            self.stop_event.clear()
            
            # Setup socket
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
                "main_scope": f"{self.main_scope_address}/{self.main_scope_subnet_mask}",
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
                'active': lease.is_active
            }
        return leases

DHCPServer = _DHCPServer()
DHCPServer.start()
