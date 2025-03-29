import os
import logging
import ipaddress
from django.apps import apps
from core.modules.dhcp import DHCPServer
from core.modules.tftp import TFTPServer
from core.modules.utils.host_network_manager import HostNetworkManager
from core.modules.utils.restconf import RestconfWrapper
from core.models import Interface, Site, Router
from core.settings import get_settings

class _NetworkController:
    def __init__(self):
        self.logger = logging.getLogger('networkcontroller')
        self.dhcp_server = DHCPServer()
        self.tftp_server = TFTPServer()
        self.start_dhcp_server()
        self.start_tftp_server()

    def start_dhcp_server(self):
        # Ensure settings are loaded
        settings = get_settings()
        if not settings:
            self.logger.warning("Cannot start DHCP server: No system settings found")
            return False

        try:
            # Start DHCP server with settings
            return self.dhcp_server.start(
                server_ip=settings.host_address,
                tftp_server_ip=settings.host_address,
                main_scope_address=settings.dhcp_provider_network_address,
                main_scope_subnet_mask=settings.dhcp_provider_network_subnet_mask,
                lease_time=settings.dhcp_lease_time
            )
        except Exception as e:
            self.logger.error(f"DHCP server start failed: {e}")
            return False

    def stop_dhcp_server(self):
        try:
            return self.dhcp_server.stop()
        except Exception as e:
            self.logger.error(f"DHCP server stop failed: {e}")
            return False

    def is_dhcp_server_running(self):
        return self.dhcp_server.is_running()

    def get_dhcp_server_status(self):
        return self.dhcp_server.get_status()

    def get_active_dhcp_leases(self):
        return self.dhcp_server.get_active_leases()

    def start_tftp_server(self):
        settings = get_settings()
        if not settings:
            self.logger.warning("Cannot start TFTP server: No system settings found")
            return False

        try:
            return self.tftp_server.start(
                root_dir=os.path.join(apps.get_app_config('core').path, 'data\\tftp-files'),
                server_ip=settings.host_address,
                port=69,
                max_block_size=512
            )

        except Exception as e:
            self.logger.error(f"TFTP server start failed: {e}")
            return False

    def stop_tftp_server(self):
        try:
            return self.tftp_server.stop()
        except Exception as e:
            self.logger.error(f"TFTP server stop failed: {e}")
            return False

    def get_tftp_server_status(self):
        return self.tftp_server.get_status()

    def get_tftp_files_list(self):
        return self.tftp_server.get_files_list()

    def is_tftp_server_running(self):
        return self.tftp_server.is_running()

    def upload_tftp_file(self, uploaded_file):
        if not self.is_tftp_server_running():
            raise Exception('TFTP server is not running')

        if not self.tftp_server.root_dir:
            raise Exception('TFTP server root directory not set')

        filename = uploaded_file.name
        file_path = os.path.join(self.tftp_server.root_dir, filename)

        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        return filename

    def delete_tftp_file(self, filename):
        if not self.is_tftp_server_running():
            raise Exception('TFTP server is not running')

        if not self.tftp_server.root_dir:
            raise Exception('TFTP server root directory not set')

        file_path = os.path.realpath(os.path.normpath(os.path.join(self.tftp_server.root_dir, filename)))

        if not file_path.startswith(self.tftp_server.root_dir):
            raise Exception('Access denied')

        if not os.path.exists(file_path):
            raise Exception(f'File {filename} not found')

        os.remove(file_path)
        return filename

    def assign_interface(self, interface: Interface, site: Site) -> bool:
        # Validate inputs
        if not interface or not site:
            self.logger.error("Invalid interface or site")
            return False

        print(site.assigned_interface)
        if site.assigned_interface is not None:
            self.logger.warning("Cannot assign interface: Interface already assigned to site")
            return False

        # TODO: Fix this shit
        # if interface.site is not None:
        #     self.logger.warning("Cannot assign interface: Interface already assigned to another site")
        #     return False

        # Get system settings
        settings = get_settings()
        if not settings:
            self.logger.error("Cannot assign interface: No system settings found")
            return False

        # Add route to site's DHCP scope
        dhcp_scope = ipaddress.IPv4Network(
            f'{site.dhcp_scope.network}/{site.dhcp_scope.subnet_mask}', 
            strict=False
        )
            
        try:
            # Add route via router's management IP
            route_added = HostNetworkManager.add_route(
                str(dhcp_scope), 
                interface.router.management_ip_address, 
                settings.host_interface_id
            )
            
            if not route_added:
                self.logger.error(f"Cannot assign interface: Failed to add route for DHCP scope {dhcp_scope}")
                return False

            # Activate DHCP scope (this might involve database operations)
            site.dhcp_scope.is_active = True
            site.dhcp_scope.save()

            # Configure interface via RESTCONF
            restconf = RestconfWrapper()
            
            # Determine first usable IP in the /30 scope
            first_ip = list(dhcp_scope.hosts())[0]
            
            # Prepare interface configuration
            interface_config = {
                "Cisco-IOS-XE-native:GigabitEthernet": { 
                    "name": interface.name.split('GigabitEthernet')[-1],
                    "vrf": {
                        "forwarding": settings.management_vrf
                    },
                    "ip": {
                        "address": {
                            "primary": {
                                "address": str(first_ip),
                                "mask": site.dhcp_scope.subnet_mask
                            }
                        },
                        "helper-address": [
                            {
                                "address": settings.host_address
                            }
                        ]
                    }
                }
            }

            # Send RESTCONF configuration
            result = restconf.put(
                interface.router.management_ip_address, 
                f"Cisco-IOS-XE-native:native/interface/GigabitEthernet={interface.name.split('GigabitEthernet')[-1]}", 
                interface_config
            )
        
            if result is None:
                HostNetworkManager.delete_route(
                    str(dhcp_scope), 
                    settings.host_interface_id
                )
                self.logger.error(f"Cannot assign interface: Failed to configure interface {interface.name} via RESTCONF")
                return False

            # Update site in database
            site.assigned_interface = interface
            site.save()

            # Update interface in database
            interface.ip_address = str(first_ip)
            interface.subnet_mask = site.dhcp_scope.subnet_mask
            interface.save()

            self.logger.info(f"Successfully attached site {site.name} to interface {interface.name}")
            return True

        except Exception as e:
            if route_added:
                HostNetworkManager.delete_route(
                    str(dhcp_scope), 
                    settings.host_interface_id
                )
            self.logger.error(f"Error assigning interface to site: {str(e)}")
            return False

    def unassign_interface(self, interface: Interface, site: Site) -> bool:
        # Validate inputs
        if not interface or not site:
            self.logger.error("Invalid interface or site")
            return False

        if site.assigned_interface != interface:
            self.logger.warning("Interface is not assigned to this site")
            return False

        # Get system settings
        settings = get_settings()
        if not settings:
            self.logger.error("Cannot unassign interface: No system settings found")
            return False

        dhcp_scope = ipaddress.IPv4Network(
            f'{site.dhcp_scope.network}/{site.dhcp_scope.subnet_mask}', 
            strict=False
        )

        try:
            # Configure interface via RESTCONF to remove IP and helper config
            restconf = RestconfWrapper()
            interface_config = {
                "Cisco-IOS-XE-native:GigabitEthernet": {
                    "name": interface.name.split('GigabitEthernet')[-1],
                    "vrf": {
                        "forwarding": settings.management_vrf
                    }
                }
            }

            # Send RESTCONF configuration
            result = restconf.put(
                interface.router.management_ip_address,
                f"Cisco-IOS-XE-native:native/interface/GigabitEthernet={interface.name.split('GigabitEthernet')[-1]}",
                interface_config
            )

            if result is None:
                self.logger.error(f"Failed to clear interface {interface.name} configuration via RESTCONF")
                return False

            # Remove route to site's DHCP scope
            HostNetworkManager.delete_route(str(dhcp_scope), settings.host_interface_id)

            # Deactivate DHCP scope
            site.dhcp_scope.is_active = False
            site.dhcp_scope.save()

            # Update site in database
            site.assigned_interface = None
            site.save()

            # Clear interface IP configuration
            interface.ip_address = "0.0.0.0"
            interface.subnet_mask = "0.0.0.0"
            interface.save()

            self.logger.info(f"Successfully unassigned interface {interface.name} from site {site.name}")
            return True

        except Exception as e:
            self.logger.error(f"Error unassigning interface from site: {str(e)}")
            return False

NetworkController = _NetworkController()
