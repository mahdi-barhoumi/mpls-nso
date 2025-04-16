import time
import logging
import platform
import subprocess
from typing import List, Dict, Optional, Union

class HostNetworkManagerError(Exception):
    pass

class _HostNetworkManager:
    def __init__(self):
        self.logger = logging.getLogger("host-network-manager")
        self.platform = platform.system().lower()
    
    def _run_command(self, command: List[str]) -> str:
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.SubprocessError as exception:
            error_message = f"Command '{' '.join(command)}' failed."
            self.logger.error(error_message)
            raise HostNetworkManagerError(error_message) from exception
    
    def list_interfaces(self) -> List[Dict[str, Union[int, str]]]:
        output = self._run_command(['netsh', 'interface', 'ipv4', 'show', 'interface'])
        
        interfaces = []
        for line in output.splitlines()[3:]:
            parts = line.split()
            if len(parts) >= 4:
                interfaces.append({
                    'id': int(parts[0]),
                    'state': parts[3],
                    'name': ' '.join(parts[4:])
                })
        
        return interfaces
    
    def list_routes(self) -> List[Dict[str, str]]:
        output = self._run_command(['netsh', 'interface', 'ipv4', 'show', 'route'])
        
        routes = []
        for line in output.splitlines()[3:]:
            parts = line.split()
            if len(parts) >= 6:
                routes.append({
                    'prefix': parts[3],
                    'id': parts[4],
                    'gateway': ' '.join(parts[5:])
                })
        
        return routes
    
    def add_route(self, prefix: str, gateway: str, interface: Union[int, str]) -> bool:
        # Check if route exists and delete it
        existing_routes = self.list_routes()
        for route in existing_routes:
            if route['prefix'] == prefix:
                self.delete_route(prefix, interface)
                break

        cmd = [
            'netsh', 'interface', 'ipv4', 'add', 'route', f'prefix={prefix}', f'nexthop={gateway}', f'interface={interface}'
        ]
        
        try:
            self._run_command(cmd)
            self.logger.info(f"Route added: {prefix} via {gateway}")
            return True

        except HostNetworkManagerError:
            return False
    
    def delete_route(self, prefix: str, interface: Union[int, str]) -> bool:
        cmd = [
            'netsh', 'interface', 'ipv4', 'delete', 'route', f'prefix={prefix}', f'interface={interface}'
        ]

        try:
            self._run_command(cmd)
            self.logger.info(f"Route deleted: {prefix}")
            return True

        except HostNetworkManagerError:
            return False
    
    def configure_interface(self, interface: Union[int, str], address: str, subnet_mask: str, default_gateway: Optional[str] = None) -> bool:
        cmd = [
            'netsh', 'interface', 'ipv4', 'set', 'address', f'name={interface}', 'static', f'address={address}', f'mask={subnet_mask}'
        ]
        
        if default_gateway:
            cmd.append(f'gateway={default_gateway}')
        
        try:
            self._run_command(cmd)
            time.sleep(5)
            self.logger.info(f"Interface {interface} configured: address={address} mask={subnet_mask}")
            return True

        except HostNetworkManagerError:
            return False

HostNetworkManager = _HostNetworkManager()
