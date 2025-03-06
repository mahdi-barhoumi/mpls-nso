import requests
import concurrent.futures
from django.utils import timezone
from core.models import Router, RouterConnection, DHCPLease

# Disable SSL warnings
requests.packages.urllib3.disable_warnings()

class NetworkMapper:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.network_map = {}

    def query_router_lldp(self, ip):
        try:
            headers = {
                'accept': "application/yang-data+json",
                'content-type': "application/yang-data+json"
            }
            
            url = f"https://{ip}/restconf/data/Cisco-IOS-XE-lldp-oper:lldp-entries"
            
            response = requests.get(
                url, 
                auth=(self.username, self.password), 
                headers=headers, 
                verify=False, 
                timeout=10
            )
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            print(f"Error querying router {ip}: {e}")
            return None

    def process_lldp_data(self, ip, hostname, lldp_data):
        if not lldp_data:
            return None
        
        # Extract chassis details
        state_details = lldp_data.get('Cisco-IOS-XE-lldp-oper:lldp-entries', {}).get('lldp-state-details', {})
        chassis_id = state_details.get('chassis-id')
        
        if not chassis_id:
            return None
        
        router_data = {
            'ip_address': ip,
            'hostname': hostname or 'UnassignedRouter',
            'connections': []
        }
        
        # Process connected routers
        for interface in lldp_data.get('Cisco-IOS-XE-lldp-oper:lldp-entries', {}).get('lldp-intf-details', []):
            if 'lldp-neighbor-details' in interface:
                for neighbor in interface['lldp-neighbor-details']:
                    connection = {
                        'remote_chassis_id': neighbor.get('chassis-id'),
                        'remote_system_name': neighbor.get('system-name', ''),
                        'local_interface': interface['if-name'],
                        'remote_interface': neighbor.get('port-id')
                    }
                    router_data['connections'].append(connection)
        
        return (chassis_id, router_data)

    def map_network(self):
        # Get all active DHCP leases
        dhcp_leases = DHCPLease.objects.filter(expiry_time__gt=timezone.now())
        
        # Use concurrent futures for faster querying
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Prepare futures for LLDP queries
            futures = {
                executor.submit(self.query_router_lldp, lease.ip_address): 
                (lease.ip_address, lease.hostname) 
                for lease in dhcp_leases
            }
            
            # Process results
            for future in concurrent.futures.as_completed(futures):
                ip, hostname = futures[future]
                try:
                    lldp_data = future.result()
                    result = self.process_lldp_data(ip, hostname, lldp_data)
                    
                    if result:
                        chassis_id, router_data = result
                        self.network_map[chassis_id] = router_data
                
                except Exception as e:
                    print(f"Error processing router {ip}: {e}")
        
        return self.network_map

    def update_database(self):
        # Track statistics
        stats = {
            'routers_discovered': len(self.network_map),
            'connections_discovered': 0
        }
        
        # Clear out old data
        Router.objects.all().delete()
        
        # Create all routers and their connections
        for chassis_id, router_data in self.network_map.items():
            # Create the router
            router = Router.objects.create(
                chassis_id=chassis_id,
                ip_address=router_data['ip_address'],
                hostname=router_data['hostname']
            )
            
            # Create all connections for this router
            for connection in router_data['connections']:
                RouterConnection.objects.create(
                    router=router,
                    remote_chassis_id=connection['remote_chassis_id'],
                    remote_system_name=connection['remote_system_name'],
                    local_interface=connection['local_interface'],
                    remote_interface=connection['remote_interface']
                )
                stats['connections_discovered'] += 1
        
        return stats

    def discover_network(self):
        # Map the network
        self.map_network()
        
        # Update database
        stats = self.update_database()
        
        # Return combined results
        result = {
            'stats': stats,
            'network_map': self.get_network_map_dict()
        }
        
        return result
    
    def get_network_map_dict(self):
        result = {}
        
        for router in Router.objects.all():
            connections = []
            for conn in router.connections.all():
                connections.append({
                    'remote_chassis_id': conn.remote_chassis_id,
                    'remote_system_name': conn.remote_system_name,
                    'local_interface': conn.local_interface,
                    'remote_interface': conn.remote_interface
                })
            
            result[router.chassis_id] = {
                'ip_address': router.ip_address,
                'hostname': router.hostname,
                'connections': connections
            }
        
        return result
