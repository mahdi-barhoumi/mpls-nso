import re
import os
import logging
import ipaddress
from django.apps import apps
from core.modules.dhcp import DHCPServer
from core.modules.tftp import TFTPServer
from core.modules.utils.host_network_manager import HostNetworkManager
from core.modules.utils.restconf import RestconfWrapper
from core.models import Interface, Site, Router, VPN, VRF
from core.settings import get_settings

class _NetworkController:
    def __init__(self):
        self.logger = logging.getLogger('networkcontroller')
        self.initialized = False
        self.dhcp_server = None
        self.tftp_server = None
        self.restconf = None

    def initialize(self):
        if self.initialized:
            return
            
        settings = get_settings()
        if not settings:
            self.logger.warning("Cannot initialize controller: No system settings found")
            return False

        self.dhcp_server = DHCPServer()
        self.tftp_server = TFTPServer()
        self.restconf = RestconfWrapper()
        self.initialized = True
        
        # Start services
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

    # Below are the most important methods for the network controller 

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
                interface.enabled = True
                interface.save()
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
                interface.enabled = False
                interface.save()
                self.logger.info(f"Successfully disabled interface {interface.name} on {interface.router.hostname}")
                return True
            else:
                self.logger.error(f"Failed to disable interface {interface.name} on {interface.router.hostname}")
                return False
                
        except Exception as exception:
            self.logger.error(f"Error disabling interface {interface.name}: {str(exception)}")
            return False

    def update_interface(self, interface: Interface) -> bool:
        try:
            self.logger.info(f"Updating interface {interface.name} on router {interface.router.hostname}")
                
            # Construct the basic interface configuration
            interface_config = {
                f"Cisco-IOS-XE-native:interface": {
                    interface.type: [
                        {
                            "name": interface.index
                        }
                    ]
                }
            }
            
            # Add IP configuration if available
            if interface.ip_address and interface.subnet_mask:
                interface_config[f"Cisco-IOS-XE-native:interface"][interface.type][0]["ip"] = {
                    "address": {
                        "primary": {
                            "address": interface.ip_address,
                            "mask": interface.subnet_mask
                        }
                    }
                }
            
            # Add VRF configuration if available
            if interface.vrf:
                interface_config[f"Cisco-IOS-XE-native:interface"][interface.type][0]["vrf"] = {
                    "forwarding": interface.vrf.name
                }
            
            # Add VLAN configuration for subinterfaces
            if interface.category == 'logical' and interface.vlan:
                interface_config[f"Cisco-IOS-XE-native:interface"][interface.type][0]["encapsulation"] = {
                    "dot1Q": {
                        "vlan-id": interface.vlan
                    }
                }
            
            # Add admin status (enabled/disabled)
            if not interface.enabled:
                interface_config[f"Cisco-IOS-XE-native:interface"][interface.type][0]["shutdown"] = [None]
            
            # Send PATCH request to update interface configuration
            result = self.restconf.patch(
                ip_address=interface.router.management_ip_address,
                path=f"Cisco-IOS-XE-native:native/interface",
                data=interface_config
            )
            
            if result is not None:
                # Update was successful
                self.logger.info(f"Successfully updated interface {interface.name} on {interface.router.hostname}")
                return True
            else:
                self.logger.error(f"Failed to update interface {interface.name} on {interface.router.hostname}")
                return False
                
        except Exception as exception:
            self.logger.error(f"Error updating interface {interface.name}: {str(exception)}")
            return False

    def delete_interface(self, interface: Interface) -> bool:
        pass

    def merge_vrf(self, vrf: VRF) -> bool:
        try:
            self.logger.debug(f"Configuring VRF {vrf.name} on router {vrf.router.hostname}")
            
            # Prepare the payload with VRF configuration
            payload = {
                "definition": [
                    {
                        "name": vrf.name,
                        "rd": vrf.route_distinguisher,
                        "address-family": {
                            "ipv4": {}
                        },
                        "route-target": {
                            "export": [
                                {"asn-ip": rt} for rt in vrf.export_targets
                            ],
                            "import": [
                                {"asn-ip": rt} for rt in vrf.import_targets
                            ]
                        }
                    }
                ]
            }

            # Send PATCH request to the router
            result = self.restconf.patch(
                ip_address=vrf.router.management_ip_address,
                path=f"Cisco-IOS-XE-native:native/vrf/definition/",
                data=payload
            )
            
            if result is not None:
                vrf.save()
                self.logger.info(f"Successfully configured VRF {vrf.name} on {vrf.router.hostname}")
                return True
            else:
                self.logger.error(f"Failed to configure VRF {vrf.name} on {vrf.router.hostname}")
                return False
                
        except Exception as exception:
            self.logger.error(f"Error configuring VRF {vrf.name}: {str(exception)}")
            return False

    def delete_vrf(self, vrf: VRF) -> bool:
        try:
            self.logger.info(f"Deleting VRF {vrf.name} from router {vrf.router.hostname}")
            
            # Send DELETE request to the router
            result = self.restconf.delete(
                ip_address=vrf.router.management_ip_address,
                path=f"Cisco-IOS-XE-native:native/vrf/definition={vrf.name}"
            )
            
            if result is not None:
                vrf.delete()
                self.logger.info(f"Successfully deleted VRF {vrf.name} from {vrf.router.hostname}")
                return True
            else:
                self.logger.error(f"Failed to delete VRF {vrf.name} from {vrf.router.hostname}")
                return False
                
        except Exception as exception:
            self.logger.error(f"Error deleting VRF {vrf.name}: {str(exception)}")
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
                f"Cisco-IOS-XE-native:{interface.type}": { 
                    "name": interface.index,
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
                f"Cisco-IOS-XE-native:native/interface/{interface.type}={interface.index}", 
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

            self.logger.info(f"Successfully assigned interface {interface.name} to site {site.name}")
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
                f"Cisco-IOS-XE-native:{interface.type}": {
                    "name": interface.index,
                    "vrf": {
                        "forwarding": settings.management_vrf
                    }
                }
            }

            # Send RESTCONF configuration
            result = restconf.put(
                interface.router.management_ip_address,
                f"Cisco-IOS-XE-native:native/interface/{interface.type}={interface.index}",
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
        
        # 1. Configure site VRF on PE router
        site_vrf, new = VRF.objects.get_or_new(
            name=f"site-{site.id}",
            route_distinguisher=f"{settings.bgp_as}:{site.id}",
            router=pe_router
        )
        self.merge_vrf(site_vrf)
        
        # 2. Configure management VRF on CE router
        ce_mgmt_vrf_data = {
            "Cisco-IOS-XE-native:definition": {
                "name": settings.management_vrf,
                "address-family": {
                    "ipv4": {}
                }
            }
        }
        
        result = self.restconf.put(
            ce_router.management_ip_address, 
            f"Cisco-IOS-XE-native:native/vrf/definition={settings.management_vrf}", 
            ce_mgmt_vrf_data
        )
        
        if result is None:
            self.logger.error(f"Failed to configure management VRF on CE router {ce_router.hostname}")
            return False
        
        # 3. Determine IP addressing for the link
        
        link_network = ipaddress.IPv4Network(f'{site.link_network}/30', strict=False)
        pe_ip = str(link_network[1])
        ce_ip = str(link_network[-2])
        subnet_mask = str(link_network.netmask)
        
        # 4. Configure PE subinterface with VRF

        # Use customer ID for VLAN ID for simplicity
        vlan_id = 10

        pe_interface = site.assigned_interface
        pe_interface_type = pe_interface.type
        pe_interface_index = pe_interface.index
        pe_subinterface_index = f"{pe_interface_index}.{vlan_id}"
        
        # Configure PE subinterface with VRF
        pe_subinterface_data = {
            "interface": {
                pe_interface_type: [
                    {
                        "name": pe_subinterface_index,
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
        
        result = self.restconf.patch(
            pe_router.management_ip_address, 
            "Cisco-IOS-XE-native:native/interface/", 
            pe_subinterface_data
        )
        
        if result is None:
            self.logger.error(f"Failed to configure subinterface on PE router {pe_router.hostname}")
            return False
        
        # 5. Find appropriate CE interface for customer traffic
        ce_interface = site.assigned_interface.connected_interfaces.first()
        ce_interface_type = ce_interface.type
        ce_interface_index = ce_interface.index
        ce_subinterface_index = f"{ce_interface_index}.{vlan_id}"
        
        # 6. Configure the untagged CE interface for management VRF
        ce_mgmt_interface_data = {
            ce_interface_type: [
                {
                    "name": ce_interface_index,
                    "vrf": {
                        "forwarding": settings.management_vrf
                    },
                    "ip": {
                        "address": {
                            "dhcp": {}
                        }
                    }
                }
            ]
        }
        
        result = self.restconf.patch(
            ce_router.management_ip_address, 
            f"Cisco-IOS-XE-native:native/interface/{ce_interface_type}={ce_interface_index}", 
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
                        "name": ce_subinterface_index,
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
        
        result = self.restconf.patch(
            ce_router.management_ip_address, 
            "Cisco-IOS-XE-native:native/interface", 
            ce_subinterface_data
        )
        
        if result is None:
            self.logger.error(f"Failed to configure subinterface on CE router {ce_router.hostname}")
            return False
        
        # TODO: Configure OSPF routing between PE and CE routers
        # - Enabling OSPF process on both routers
        # - Redistributing routes between VRF and BGP
        # - Update the models in the database
        
        self.logger.info(f"Successfully configured routing for site {site}")
        return True

NetworkController = _NetworkController()
NetworkController.initialize()
