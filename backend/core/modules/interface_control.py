import json
import logging
import requests
import concurrent.futures
from django.utils import timezone
from django.conf import settings
from requests.auth import HTTPBasicAuth
from core.models import DHCPLease


class InterfaceControl:
    def __init__(self, username, password, port=443):
        self.logger = logging.getLogger('Interface')
        self.username = username
        self.password = password
        self.port = port
        self.network_map = {}

    def connect_to_router(self, router_ip):
        """Connects to the router and retrieves interface information."""
        base_url = f"https://{router_ip}:{self.port}/restconf/data"
        auth = HTTPBasicAuth(self.username, self.password)
        headers = {
            'Accept': 'application/yang-data+json',
            'Content-Type': 'application/yang-data+json'
        }

        try:
            response = requests.get(
                f"{base_url}/ietf-interfaces:interfaces",
                auth=auth,
                headers=headers,
                verify=False
            )
            response.raise_for_status()
            self.logger.info(f"Successfully connected to router at {router_ip}")
            return {
                'success': True,
                'router_ip': router_ip,
                'data': response.json()
            }
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to connect to router at {router_ip}: {str(e)}")
            return {
                'success': False,
                'router_ip': router_ip,
                'error': str(e)
            }
    def enable_all_interfaces(self, router_ip):
        """
        Enables all interfaces on the specified router.
        
        Args:
            router_ip (str): IP address of the router
            
        Returns:
            dict: A dictionary containing the operation result
        """
        base_url = f"https://{router_ip}:{self.port}/restconf/data"
        auth = HTTPBasicAuth(self.username, self.password)
        headers = {
            'Accept': 'application/yang-data+json',
            'Content-Type': 'application/yang-data+json'
        }
        
        # First get all interfaces
        connection_result = self.connect_to_router(router_ip)
        if not connection_result['success']:
            return connection_result
        
        interfaces_data = connection_result['data']
        interface_list = interfaces_data.get('ietf-interfaces:interfaces', {}).get('interface', [])
        
        success_count = 0
        failed_interfaces = []
        
        # Update each interface to enabled state
        for interface in interface_list:
            interface_name = interface.get('name')
            try:
                # Create a copy of the original interface data and just update the enabled property
                interface_copy = interface.copy()
                interface_copy['enabled'] = True
                
                # Make the PUT request to update the interface
                response = requests.put(
                    f"{base_url}/ietf-interfaces:interfaces/interface={interface_name}",
                    auth=auth,
                    headers=headers,
                    data=json.dumps({"ietf-interfaces:interface": interface_copy}),
                    verify=False
                )
                response.raise_for_status()
                success_count += 1
                self.logger.info(f"Successfully enabled interface {interface_name} on router {router_ip}")
            except requests.exceptions.RequestException as e:
                failed_interfaces.append({
                    'name': interface_name,
                    'error': str(e)
                })
                self.logger.error(f"Failed to enable interface {interface_name} on router {router_ip}: {str(e)}")
        
        return {
            'success': len(failed_interfaces) == 0,
            'router_ip': router_ip,
            'total_interfaces': len(interface_list),
            'enabled_count': success_count,
            'failed_interfaces': failed_interfaces
        }

    def disable_all_interfaces(self, router_ip):
        """
        Disables all interfaces on the specified router.
        
        Args:
            router_ip (str): IP address of the router
            
        Returns:
            dict: A dictionary containing the operation result
        """
        base_url = f"https://{router_ip}:{self.port}/restconf/data"
        auth = HTTPBasicAuth(self.username, self.password)
        headers = {
            'Accept': 'application/yang-data+json',
            'Content-Type': 'application/yang-data+json'
        }
        
        # First get all interfaces
        connection_result = self.connect_to_router(router_ip)
        if not connection_result['success']:
            return connection_result
        
        interfaces_data = connection_result['data']
        interface_list = interfaces_data.get('ietf-interfaces:interfaces', {}).get('interface', [])
        
        success_count = 0
        failed_interfaces = []
        
        # Update each interface to disabled state
        for interface in interface_list:
            interface_name = interface.get('name')
            try:
                # Create a copy of the original interface data and just update the enabled property
                interface_copy = interface.copy()
                interface_copy['enabled'] = False
                
                # Make the PUT request to update the interface
                response = requests.put(
                    f"{base_url}/ietf-interfaces:interfaces/interface={interface_name}",
                    auth=auth,
                    headers=headers,
                    data=json.dumps({"ietf-interfaces:interface": interface_copy}),
                    verify=False
                )
                response.raise_for_status()
                success_count += 1
                self.logger.info(f"Successfully disabled interface {interface_name} on router {router_ip}")
            except requests.exceptions.RequestException as e:
                failed_interfaces.append({
                    'name': interface_name,
                    'error': str(e)
                })
                self.logger.error(f"Failed to disable interface {interface_name} on router {router_ip}: {str(e)}")
        
        return {
            'success': len(failed_interfaces) == 0,
            'router_ip': router_ip,
            'total_interfaces': len(interface_list),
            'disabled_count': success_count,
            'failed_interfaces': failed_interfaces
        }
    
    def process_all_routers(self):
        """Retrieves interface information from all active DHCP leases."""
        dhcp_leases = DHCPLease.objects.filter(expiry_time__gt=timezone.now())

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self.connect_to_router, lease.ip_address): lease.ip_address for lease in dhcp_leases}

            results = []
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Error processing router {futures[future]}: {e}")
    

        return results
    def get_interface_status(self, interface_name):
        """
        Get the status of a specific interface across all routers.
        
        Args:
            interface_name (str): Name of the interface to check
            
        Returns:
            dict: A dictionary containing the status results
        """
        dhcp_leases = DHCPLease.objects.filter(expiry_time__gt=timezone.now())
        results = []
        found = False
        
        for lease in dhcp_leases:
            router_ip = lease.ip_address
            connection_result = self.connect_to_router(router_ip)
            
            if not connection_result['success']:
                results.append({
                    'router_ip': router_ip,
                    'success': False,
                    'error': connection_result.get('error', 'Failed to connect to router')
                })
                continue
                
            interfaces_data = connection_result['data']
            interface_list = interfaces_data.get('ietf-interfaces:interfaces', {}).get('interface', [])
            
            # Find the specific interface
            interface_info = None
            for interface in interface_list:
                if interface.get('name') == interface_name:
                    interface_info = interface
                    found = True
                    break
                    
            if interface_info:
                results.append({
                    'router_ip': router_ip,
                    'success': True,
                    'interface': interface_info
                })
            else:
                results.append({
                    'router_ip': router_ip,
                    'success': False,
                    'error': f"Interface '{interface_name}' not found on router {router_ip}"
                })
        
        if found:
            return {
                'success': True,
                'interface_name': interface_name,
                'routers': results
            }
        else:
            return {
                'success': False,
                'error': f"Interface '{interface_name}' not found on any router",
                'routers': results
            }
    