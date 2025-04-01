import re
import os
import logging
import ipaddress
from django.apps import apps
from core.modules.dhcp import DHCPServer
from core.modules.tftp import TFTPServer
from core.modules.utils.host_network_manager import HostNetworkManager
from core.modules.utils.restconf import RestconfWrapper
from core.models import Interface, Site, Router, VPN
from core.settings import get_settings

class _NetworkController:
    def __init__(self):
        self.logger = logging.getLogger('networkcontroller')
        self.dhcp_server = DHCPServer()
        self.tftp_server = TFTPServer()
        self.restconf = RestconfWrapper()
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

    def enable_interface(self, interface: Interface) -> bool:
        try:
            self.logger.debug(f"Enabling interface {interface.name} on router {interface.router.hostname}")
            
            # Prepare the payload with enabled=true
            payload = {
                "ietf-interfaces:interface": {
                    "enabled": True
                }
            }

            # Send PATCH request to the router
            result = self.restconf.patch(
                ip_address=interface.router.management_ip_address,
                path=f"ietf-interfaces:interfaces/interface={interface.name}",
                data=payload
            )
            
            if result is not None:
                self.logger.info(f"Successfully enabled interface {interface.name} on {interface.router.hostname}")
                return True
            else:
                self.logger.error(f"Failed to enable interface {interface.name} on {interface.router.hostname}")
                return False
                
        except Exception as exception:
            self.logger.error(f"Error enabling interface {interface.name}: {str(exception)}")
            return False

    def disable_interface(self, interface: Interface) -> bool:
        try:
            self.logger.info(f"Disabling interface {interface.name} on router {interface.router.hostname}")
            
            # Prepare the payload with enabled=false
            payload = {
                "ietf-interfaces:interface": {
                    "enabled": False
                }
            }
            
            # Send PATCH request to the router
            result = self.restconf.patch(
                ip_address=interface.router.management_ip_address,
                path=f"ietf-interfaces:interfaces/interface={interface.name}",
                data=payload
            )
            
            if result is not None:
                self.logger.info(f"Successfully disabled interface {interface.name} on {interface.router.hostname}")
                return True
            else:
                self.logger.error(f"Failed to disable interface {interface.name} on {interface.router.hostname}")
                return False
                
        except Exception as exception:
            self.logger.error(f"Error disabling interface {interface.name}: {str(exception)}")
            return False

    def assign_interface(self, interface: Interface, site: Site) -> bool:
        # Validate inputs
        if not interface or not site:
            self.logger.error("Invalid interface or site")
            return False

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

            self.enable_interface(interface)

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

            self.disable_interface(interface)

            self.logger.info(f"Successfully unassigned interface {interface.name} from site {site.name}")
            return True

        except Exception as e:
            self.logger.error(f"Error unassigning interface from site: {str(e)}")
            return False

    def setup_routing(self, site):
        self.logger.info(f"Setting up VPN routing for site {site}")
        
        # Get required objects
        if not site.assigned_interface or not site.router:
            self.logger.error(f"Site {site} is missing assigned interface or router")
            return False
        
        pe_router = site.assigned_interface.router
        ce_router = site.router
        settings = get_settings()
        
        # Verify router roles
        if pe_router.role != 'PE':
            self.logger.error(f"Router {pe_router.hostname} is not a PE router")
            return False
        
        if ce_router.role != 'CE':
            self.logger.error(f"Router {ce_router.hostname} is not a CE router")
            return False
        
        # Create VRF name and route distinguisher for PE only
        vrf_name = f"customer-{site.customer.id}"
        rd = f"{settings.bgp_as}:{site.customer.id}"
        rt = rd  # Using same value for route target
        
        # Initialize RESTCONF wrapper
        restconf = RestconfWrapper()
        
        # 1. Configure VRF on PE router only
        pe_vrf_data = {
            "Cisco-IOS-XE-native:definition": {
                "name": vrf_name,
                "rd": rd,
                "address-family": {
                    "ipv4": {
                        "route-target": {
                            "export-route-target": {
                                "without-stitching": [
                                    {
                                        "asn-ip": rt
                                    }
                                ]
                            },
                            "import-route-target": {
                                "without-stitching": [
                                    {
                                        "asn-ip": rt
                                    }
                                ]
                            }
                        }
                    }
                },
                "route-target": {
                    "export": [
                        {
                            "asn-ip": rt
                        }
                    ],
                    "import": [
                        {
                            "asn-ip": rt
                        }
                    ]
                }
            }
        }
        
        result = restconf.put(
            pe_router.management_ip_address, 
            f"Cisco-IOS-XE-native:native/vrf/definition={vrf_name}", 
            pe_vrf_data
        )
        
        if result is None:
            self.logger.error(f"Failed to configure VRF on PE router {pe_router.hostname}")
            return False
        
        # 2. Configure management VRF on CE router
        management_vrf_name = settings.management_vrf
        
        ce_mgmt_vrf_data = {
            "Cisco-IOS-XE-native:definition": {
                "name": management_vrf_name,
                "address-family": {
                    "ipv4": {}
                }
            }
        }
        
        result = restconf.put(
            ce_router.management_ip_address, 
            f"Cisco-IOS-XE-native:native/vrf/definition={management_vrf_name}", 
            ce_mgmt_vrf_data
        )
        
        if result is None:
            self.logger.error(f"Failed to configure management VRF on CE router {ce_router.hostname}")
            return False
        
        # 3. Determine IP addressing for the VPN link
        
        # Get all sites in this VPN
        vpn_sites = site.customer.sites.all()
        
        # Find index of current site in the VPN
        try:
            site_index = list(vpn_sites).index(site)
        except ValueError:
            site_index = 0
        
        # Calculate subnet based on site index (using 192.168.0.0/16 divided into /30 subnets)
        # Each /30 subnet has 4 addresses (0: network, 1: PE, 2: CE, 3: broadcast)
        base_network = ipaddress.IPv4Network('192.168.0.0/16')
        subnets = list(base_network.subnets(new_prefix=30))
        
        if site_index >= len(subnets):
            self.logger.error(f"Not enough subnets available for site {site}")
            return False
        
        current_subnet = subnets[site_index]
        pe_ip = str(current_subnet[1])
        ce_ip = str(current_subnet[2])
        subnet_mask = str(current_subnet.netmask)
        
        # 4. Configure PE subinterface with VRF
        # Parse interface name to get base and create subinterface
        pe_interface_name = site.assigned_interface.name
        
        # Extract interface type and number (e.g., "GigabitEthernet" and "5" from "GigabitEthernet5")
        match = re.match(r'([a-zA-Z]+)([0-9/]+)', pe_interface_name)
        
        if not match:
            self.logger.error(f"Cannot parse interface name: {pe_interface_name}")
            return False
        
        interface_type = match.group(1)
        interface_number = match.group(2)
        
        # Use customer ID for VLAN ID for simplicity
        vlan_id = 10
        subinterface_id = f"{interface_number}.{vlan_id}"
        
        # Configure PE subinterface with VRF
        pe_subinterface_data = {
            "interface": {
                interface_type: [
                    {
                        "name": subinterface_id,
                        "encapsulation": {
                            "dot1Q": {
                                "vlan-id": vlan_id
                            }
                        },
                        "vrf": {
                            "forwarding": vrf_name
                        },
                        "ip": {
                            "address": {
                                "primary": {
                                    "address": pe_ip,
                                    "mask": subnet_mask
                                }
                            }
                        }
                    }
                ]
            }
        }
        
        result = restconf.patch(
            pe_router.management_ip_address, 
            "Cisco-IOS-XE-native:native/interface/", 
            pe_subinterface_data
        )
        
        if result is None:
            self.logger.error(f"Failed to configure subinterface on PE router {pe_router.hostname}")
            return False
        
        # 5. Find appropriate CE interface for customer traffic
        ce_interface = site.assigned_interface.connected_interfaces.first()
        
        if not ce_interface:
            self.logger.error(f"No available interfaces on CE router {ce_router.hostname}")
            return False
        
        # Parse CE interface name
        match = re.match(r'([a-zA-Z]+)([0-9/]+)', ce_interface.name)
        
        if not match:
            self.logger.error(f"Cannot parse interface name: {ce_interface.name}")
            return False
        
        ce_interface_type = match.group(1)
        ce_interface_number = match.group(2)
        ce_subinterface_id = f"{ce_interface_number}.{vlan_id}"
        
        # 6. Configure the untagged CE interface for management VRF
        ce_mgmt_interface_data = {
            ce_interface_type: [
                {
                    "name": ce_interface_number,
                    "vrf": {
                        "forwarding": management_vrf_name
                    }
                    # Note: Keeping any existing IP configuration intact
                }
            ]
        }
        
        result = restconf.patch(
            ce_router.management_ip_address, 
            f"Cisco-IOS-XE-native:native/interface/{ce_interface_type}={ce_interface_number}", 
            ce_mgmt_interface_data
        )
        
        if result is None:
            self.logger.error(f"Failed to configure management VRF on CE interface {ce_interface.name}")
            return False

        # 7. Configure CE subinterface for customer traffic (in global routing table, not in VRF)
        ce_subinterface_data = {
            "interface": {
                ce_interface_type: [
                    {
                        "name": ce_subinterface_id,
                        "encapsulation": {
                            "dot1Q": {
                                "vlan-id": vlan_id
                            }
                        },
                        "ip": {
                            "address": {
                                "primary": {
                                    "address": ce_ip,
                                    "mask": subnet_mask
                                }
                            }
                        }
                    }
                ]
            }
        }
        
        result = restconf.patch(
            ce_router.management_ip_address, 
            "Cisco-IOS-XE-native:native/interface", 
            ce_subinterface_data
        )
        
        if result is None:
            self.logger.error(f"Failed to configure subinterface on CE router {ce_router.hostname}")
            return False
        
        # 8. Update the Interface models in the database
        # TODO
        
        # TODO: Configure OSPF routing between PE and CE routers
        # This will involve:
        # 1. Enabling OSPF process on both routers
        # 2. Configuring OSPF areas
        # 3. Redistributing routes between VRF and global routing table
        
        self.logger.info(f"Successfully configured routing for site {site}")
        return True

NetworkController = _NetworkController()
