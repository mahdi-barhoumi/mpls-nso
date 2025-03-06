import json
import requests
from requests.auth import HTTPBasicAuth
import os
import concurrent.futures

# Disable SSL warnings
requests.packages.urllib3.disable_warnings()

class NetworkMapper:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.network_map = {}

    def query_router_lldp(self, ip):
        """
        Query a single router for LLDP information
        
        Args:
            ip (str): IP address of the router
        
        Returns:
            dict: Router LLDP information or None if query fails
        """
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
        """
        Process LLDP data and extract relevant network information
        
        Args:
            ip (str): IP address of the router
            hostname (str): Hostname of the router
            lldp_data (dict): Raw LLDP data from the router
        
        Returns:
            dict: Processed network information
        """
        if not lldp_data:
            return None
        
        # Extract chassis details
        state_details = lldp_data.get('Cisco-IOS-XE-lldp-oper:lldp-entries', {}).get('lldp-state-details', {})
        chassis_id = state_details.get('chassis-id')
        
        if not chassis_id:
            return None
        
        router_info = {
            'ip': ip,
            'hostname': hostname,
            'connected_routers': []
        }
        
        # Process connected routers
        for interface in lldp_data.get('Cisco-IOS-XE-lldp-oper:lldp-entries', {}).get('lldp-intf-details', []):
            if 'lldp-neighbor-details' in interface:
                for neighbor in interface['lldp-neighbor-details']:
                    connected_router = {
                        'local_interface': interface['if-name'],
                        'remote_chassis_id': neighbor.get('chassis-id'),
                        'remote_system_name': neighbor.get('system-name'),
                        'remote_port': neighbor.get('port-id')
                    }
                    router_info['connected_routers'].append(connected_router)
        
        return (chassis_id, router_info)

    def map_network(self, dhcp_leases_file):
        """
        Map the entire network by querying each router's LLDP information
        
        Args:
            dhcp_leases_file (str): Path to the DHCP leases JSON file
        """
        # Load DHCP leases
        with open(dhcp_leases_file, 'r') as f:
            dhcp_leases = json.load(f)
        
        # Use concurrent futures for faster querying
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Prepare futures for LLDP queries
            futures = {
                executor.submit(self.query_router_lldp, router_info['ip']): 
                (router_info['ip'], router_info['hostname']) 
                for router_info in dhcp_leases.values()
            }
            
            # Process results
            for future in concurrent.futures.as_completed(futures):
                ip, hostname = futures[future]
                try:
                    lldp_data = future.result()
                    result = self.process_lldp_data(ip, hostname, lldp_data)
                    
                    if result:
                        chassis_id, router_network_info = result
                        self.network_map[chassis_id] = router_network_info
                
                except Exception as e:
                    print(f"Error processing router {ip}: {e}")
        
        return self.network_map

    def save_network_map(self, output_file='network_map.json'):
        """
        Save the generated network map to a JSON file
        
        Args:
            output_file (str): Path to save the network map
        """
        with open(output_file, 'w') as f:
            json.dump(self.network_map, f, indent=4)
        print(f"Network map saved to {output_file}")

def main():
    # Configuration
    username = "mgmt"
    password = "mgmtapp"
    dhcp_leases_file = "../dhcp-service/dhcp_leases.json"
    
    # Initialize mapper
    mapper = NetworkMapper(username, password)
    
    # Map network
    network_map = mapper.map_network(dhcp_leases_file)
    
    # Save network map
    mapper.save_network_map()

if __name__ == "__main__":
    main()