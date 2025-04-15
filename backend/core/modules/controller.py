import os
import logging
import ipaddress
from typing import List
from django.apps import apps
from core.modules.dhcp import DHCPServer
from core.modules.tftp import TFTPServer
from core.modules.utils.host_network_manager import HostNetworkManager
from core.modules.utils.restconf import RestconfWrapper
from core.models import Interface, Site, Router, VPN, VRF, RouteTarget
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
            self.logger.info(f"Enabling interface {interface.name} on router {interface.router}")

            # If the interface is a subinterface, we need to enable the parent interface first
            if interface.category == 'logical':
                parent_interface = Interface.objects.get(
                    router=interface.router,
                    name=interface.name.split('.')[0]
                )
                self.enable_interface(parent_interface)

            # Send PATCH request to the router
            result = self.restconf.patch(
                ip_address=interface.router.management_ip_address,
                path=f"ietf-interfaces:interfaces/interface={interface.name}/enabled",
                data={"enabled": True}
            )
            
            if result is not None:
                interface.enabled = True
                interface.save()
                self.logger.info(f"Successfully enabled interface {interface.name} on {interface.router}")
                return True
            else:
                self.logger.error(f"Failed to enable interface {interface.name} on {interface.router}")
                return False
                
        except Exception as exception:
            self.logger.error(f"Error enabling interface {interface.name}: {str(exception)}")
            return False

    def disable_interface(self, interface: Interface) -> bool:
        try:
            self.logger.info(f"Disabling interface {interface.name} on router {interface.router}")
            
            # Send PATCH request to the router
            result = self.restconf.patch(
                ip_address=interface.router.management_ip_address,
                path=f"ietf-interfaces:interfaces/interface={interface.name}/enabled",
                data={"enabled": False}
            )
            
            if result is not None:
                interface.enabled = False
                interface.save()
                self.logger.info(f"Successfully disabled interface {interface.name} on {interface.router}")
                return True
            else:
                self.logger.error(f"Failed to disable interface {interface.name} on {interface.router}")
                return False
                
        except Exception as exception:
            self.logger.error(f"Error disabling interface {interface.name}: {str(exception)}")
            return False

    def create_or_update_interface(self, interface: Interface) -> bool:
        try:
            self.logger.debug(f"Updating interface {interface.name} on router {interface.router}")
            
            # Build payload based on interface attributes
            payload = {
                "name": interface.index,
                "vrf": {"forwarding": interface.vrf.name} if interface.vrf else {},
                "ip": {
                    "helper-address": [
                        {
                            "address": interface.dhcp_helper_address
                        }
                    ] if interface.dhcp_helper_address else []
                }
            }

            # Add description if available
            if interface.description:
                payload["description"] = interface.description

            # Add VLAN configuration for subinterfaces
            if interface.category == 'logical' and interface.vlan:
                payload["encapsulation"] = {
                    "dot1Q": {
                        "vlan-id": interface.vlan
                    }
                }

            # Configure IP addressing based on method
            if interface.addressing == "static":
                payload["ip"]["address"] = {
                    "primary": {
                        "address": interface.ip_address,
                        "mask": interface.subnet_mask
                    } if interface.ip_address and interface.subnet_mask else {}
                }
            elif interface.addressing == "dhcp":
                payload["ip"]["address"] = {
                    "dhcp": {}
                }
            
            payload = {
                "interface": {
                    interface.type: [
                        payload
                    ]
                }
            }

            # Send PATCH request to update the interface configuration
            result = self.restconf.patch(
                ip_address=interface.router.management_ip_address,
                path=f"Cisco-IOS-XE-native:native/interface/",
                data=payload
            )
            
            if result is not None:
                # Update enable/disable state if needed
                if interface.enabled:
                    self.enable_interface(interface)
                else:
                    self.disable_interface(interface)
                # Update the database
                interface.save()
                self.logger.info(f"Successfully updated interface {interface.name} on {interface.router}")
                return True
            else:
                self.logger.error(f"Failed to update interface {interface.name} on {interface.router}")
                return False
                
        except Exception as exception:
            self.logger.error(f"Error updating interface {interface.name}: {str(exception)}")
            return False

    def get_or_create_subinterface(self, interface: Interface, vlan: int) -> Interface:
        # Check if the interface is physical first
        if interface.category != 'physical':
            self.logger.error("Cannot create subinterface on a non-physical interface")
            return None
        
        try:
            subinterface, new = Interface.objects.get_or_new(router=interface.router, name=f"{interface.name}.{vlan}")
            subinterface.vlan = vlan
            subinterface.mac_address = interface.mac_address
            success = self.create_or_update_interface(subinterface)

            if success:
                self.logger.info(f"Successfully created subinterface {subinterface.name} on {interface.router}")
                return subinterface

            self.logger.error(f"Failed creating subinterface {subinterface.name} on {interface.router}")
            return None
        except Exception as exception:
            self.logger.error(f"Error creating subinterface: {str(exception)}")
            return None

    def delete_interface(self, interface: Interface) -> bool:
        # Check if the interface exists in the database
        if not interface.pk:
            self.logger.warning(f"Cannot delete a non existing interface")
            return False

        # Check if the interface is physical
        if interface.category == 'physical':
            self.logger.warning(f"Cannot delete physical interface {interface.name} from {interface.router}")
            return False

        try:
            # Send DELETE request to remove the interface
            result = self.restconf.delete(
                ip_address=interface.router.management_ip_address,
                path=f"Cisco-IOS-XE-native:native/interface/{interface.type}={interface.index}"
            )
            
            if result is not None:
                # Delete the interface from the database
                interface.delete()
                self.logger.info(f"Successfully deleted interface {interface.name} from {interface.router}")
                return True
            else:
                self.logger.error(f"Failed to delete interface {interface.name} from {interface.router}")
                return False
                
        except Exception as exception:
            self.logger.error(f"Error deleting interface {interface.name}: {str(exception)}")
            return False

    def unassign_vrf(self, interface: Interface) -> bool:
        # Check if the interface exists in the database
        if not interface.pk:
            self.logger.warning(f"Cannot unassign VRF from a non existing interface")
            return False

        try:
            self.logger.info(f"Unassigning VRF from interface {interface.name} on router {interface.router}")
            
            # Send DELETE request to remove the VRF assignment
            result = self.restconf.delete(
                ip_address=interface.router.management_ip_address,
                path=f"Cisco-IOS-XE-native:native/interface/{interface.type}={interface.index}/vrf/"
            )
            
            if result is not None:
                interface.vrf = None
                interface.save()
                self.logger.info(f"Successfully unassigned VRF {interface.name} on {interface.router}")
                return True
            else:
                self.logger.error(f"Failed to unassign VRF from {interface.name} on {interface.router}")
                return False
                
        except Exception as exception:
            self.logger.error(f"Error unassigning VRF from {interface.name} on {interface.router}: {str(exception)}")
            return False

    def create_or_update_vrf(self, vrf: VRF) -> bool:
        try:
            self.logger.debug(f"Updating VRF {vrf}")

            # Prepare the payload with VRF configuration
            payload = {
                "name": vrf.name,
                "address-family": {
                    "ipv4": {}
                },
                "route-target": {
                    "export": [
                        {"asn-ip": rt} for rt in vrf.export_targets
                    ] if vrf.export_targets else [],
                    "import": [
                        {"asn-ip": rt} for rt in vrf.import_targets
                    ] if vrf.import_targets else []
                }
            }

            # Add route distinguisher if available
            if vrf.route_distinguisher:
                payload["rd"] = vrf.route_distinguisher

            payload = {
                "definition": [payload]
            }

            # Send PATCH request to the router
            result = self.restconf.patch(
                ip_address=vrf.router.management_ip_address,
                path=f"Cisco-IOS-XE-native:native/vrf/definition/",
                data=payload
            )
            
            if result is not None:
                vrf.save()
                self.logger.info(f"Successfully configured VRF {vrf.name} on {vrf.router}")
                return True
            else:
                self.logger.error(f"Failed to configure VRF {vrf.name} on {vrf.router}")
                return False
                
        except Exception as exception:
            self.logger.error(f"Error configuring VRF {vrf.name}: {str(exception)}")
            return False

    def delete_vrf(self, vrf: VRF) -> bool:
        # Check if the VRF exists in the database
        if not vrf.pk:
            self.logger.warning(f"Cannot delete a non existing VRF")
            return False

        try:
            self.logger.info(f"Deleting VRF {vrf.name} from router {vrf.router}")
            
            # Send DELETE request to the router
            result = self.restconf.delete(
                ip_address=vrf.router.management_ip_address,
                path=f"Cisco-IOS-XE-native:native/vrf/definition={vrf.name}/address-family/ipv4"
            )

            result = result and self.restconf.delete(
                ip_address=vrf.router.management_ip_address,
                path=f"Cisco-IOS-XE-native:native/vrf/definition={vrf.name}"
            )
            
            if result is not None:
                vrf.delete()
                self.logger.info(f"Successfully deleted VRF {vrf.name} from {vrf.router}")
                return True
            else:
                self.logger.error(f"Failed to delete VRF {vrf.name} from {vrf.router}")
                return False
                
        except Exception as exception:
            self.logger.error(f"Error deleting VRF {vrf.name}: {str(exception)}")
            return False

    def assign_interface(self, interface: Interface, site: Site) -> bool:
        # Validate inputs
        if not interface.pk or not site.pk:
            self.logger.error("Cannot assign interface with a non-existing interface or a non-existing site")
            return False

        # Get system settings
        settings = get_settings()
        if not settings:
            self.logger.error("Cannot assign interface: No system settings found")
            return False

        # Add route to site's DHCP scope
        route_added = False
        dhcp_scope = ipaddress.IPv4Network(
            f'{site.dhcp_scope.network}/{site.dhcp_scope.subnet_mask}', 
            strict=False
        )

        try:
            # Add route via router's management IP
            route_added = HostNetworkManager.add_route(str(dhcp_scope), interface.router.management_ip_address, settings.host_interface_id)
            
            if not route_added:
                HostNetworkManager.delete_route(str(dhcp_scope), settings.host_interface_id)
                self.logger.error(f"Cannot assign interface: Failed to add route for DHCP scope {dhcp_scope}")
                return False

            # Activate DHCP scope
            site.dhcp_scope.is_active = True
            site.dhcp_scope.save()

            # Determine first usable IP in the /30 scope
            first_ip = str(list(dhcp_scope.hosts())[0])

            # Get management VRF
            management_vrf = VRF.objects.get(name=settings.management_vrf, router=interface.router)
            if not management_vrf:
                HostNetworkManager.delete_route(str(dhcp_scope), settings.host_interface_id)
                self.logger.error(f"Cannot assign interface: No maangement VRF found")
                return False

            interface.vrf = management_vrf 
            interface.addressing = "static"
            interface.ip_address = first_ip
            interface.subnet_mask = site.dhcp_scope.subnet_mask
            interface.dhcp_helper_address = settings.host_address
            interface.enabled = True
        
            if not self.create_or_update_interface(interface):
                HostNetworkManager.delete_route(str(dhcp_scope), settings.host_interface_id)
                self.logger.error(f"Cannot assign interface: Failed to configure interfaces")
                return False

            # Configure site VRF on PE router
            site_vrf, new = VRF.objects.get_or_new(
                router=interface.router,
                name=f"site-{site.id}"
            )
            site_vrf.route_distinguisher = f"{settings.bgp_as}:{site.id}"

            if not self.create_or_update_vrf(site_vrf):
                HostNetworkManager.delete_route(str(dhcp_scope), settings.host_interface_id)
                self.logger.error(f"Failed creating or updating VRF {site_vrf}")
                return False

            # Update site in database
            site.assigned_interface = interface
            site.vrf = site_vrf
            site.save()

            self.logger.info(f"Successfully assigned interface {interface.name} to site {site.name}")
            return True

        except Exception as exception:
            if route_added:
                HostNetworkManager.delete_route(str(dhcp_scope), settings.host_interface_id)
            self.logger.error(f"Error assigning interface to site: {str(exception)}")
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
            
            subinterface = self.get_or_create_subinterface(interface, 10)

            interface.addressing = "static"
            interface.ip_address = None
            interface.subnet_mask = None
            interface.dhcp_helper_address = None
            interface.enabled = False

            if not self.create_or_update_interface(interface) or not self.delete_interface(subinterface):
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

            self.logger.info(f"Successfully unassigned interface {interface.name} from site {site.name}")
            return True

        except Exception as exception:
            self.logger.error(f"Error unassigning interface from site: {str(exception)}")
            return False

    def list_router_ospf_processes(self, router: Router) -> List[int]:
        try:            
            # Query the router for OSPF configuration
            result = self.restconf.get(
                ip_address=router.management_ip_address,
                path="Cisco-IOS-XE-native:native/router/router-ospf"
            )
            
            process_ids = []
            
            if result and 'Cisco-IOS-XE-ospf:router-ospf' in result:
                ospf_config = result['Cisco-IOS-XE-ospf:router-ospf']['ospf']
                
                # Get global OSPF processes
                if 'process-id' in ospf_config:
                    for process in ospf_config['process-id']:
                        process_ids.append(process['id'])
                
                # Get VRF-specific OSPF processes
                if 'process-id-vrf' in ospf_config:
                    for process in ospf_config['process-id-vrf']:
                        process_ids.append(process['id'])
            
            self.logger.debug(f"Found OSPF processes on {router}: {process_ids}")
            return process_ids
        
        except Exception as exception:
            self.logger.error(f"Error listing OSPF processes on {router}: {str(exception)}")
            return []

    def create_or_update_ospf_process(self, router: Router, process_id: int, vrf_name: str = None, networks: List[dict] = None, router_id: str = None) -> bool:
        try:
            self.logger.debug(f"Configuring OSPF process {process_id} on router {router}")
            
            # Build the payload
            process_config = {
                "id": process_id
            }
            
            # Add router ID if provided
            if router_id:
                process_config["router-id"] = router_id
            
            # Add networks if provided
            if networks and len(networks) > 0:
                process_config["network"] = networks
            
            # Determine the path and full payload based on whether this is VRF-specific
            if vrf_name:
                process_config["vrf"] = vrf_name
                payload = {
                    "ospf": {
                        "process-id-vrf": [process_config]
                    }
                }
            else:
                payload = {
                    "ospf": {
                        "process-id": [process_config]
                    }
                }

            # Send the configuration to the router
            result = self.restconf.patch(
                ip_address=router.management_ip_address,
                path="Cisco-IOS-XE-native:native/router/router-ospf/ospf/",
                data=payload
            )
            
            if result is not None:
                self.logger.info(f"Successfully configured OSPF process {process_id} on {router}")
                return True
            else:
                self.logger.error(f"Failed to configure OSPF process {process_id} on {router}")
                return False
                
        except Exception as exception:
            self.logger.error(f"Error configuring OSPF process {process_id} on {router}: {str(exception)}")
            return False

    def enable_routing(self, site):
        self.logger.info(f"Enabling routing for site {site}")
        
        # Get required objects
        if not site.assigned_interface or not site.router:
            self.logger.error(f"Site {site} is missing assigned interface or router")
            return False
        
        settings = get_settings()
        pe_router = site.assigned_interface.router
        ce_router = site.router
        pe_interface = site.assigned_interface
        ce_interface = site.assigned_interface.connected_interfaces.first()
        dhcp_scope = ipaddress.IPv4Network(
            f'{site.dhcp_scope.network}/{site.dhcp_scope.subnet_mask}', 
            strict=False
        )
        
        # Verify required ojbects
        if None in [pe_router, ce_router, pe_interface, ce_interface]:
            self.logger.error(f"A required object is missing")
            return False

        # Verify router roles
        if pe_router.role != 'PE':
            self.logger.error(f"Router {pe_router} is not a PE router")
            return False
        
        if ce_router.role != 'CE':
            self.logger.error(f"Router {ce_router} is not a CE router")
            return False

        # Configure management VRF on CE router
        ce_management_vrf, new = VRF.objects.get_or_new(
            router=ce_router,
            name=settings.management_vrf
        )
        ce_management_vrf.route_distinguisher = None

        if not self.create_or_update_vrf(ce_management_vrf):
            self.logger.error(f"Failed creating or updating management VRF on {ce_router}")
            return False
        
        # Determine IP addressing for the link
        link_network = ipaddress.IPv4Network(f'{site.link_network}/30', strict=False)
        pe_ip = str(link_network[1])
        ce_ip = str(link_network[-2])
        subnet_mask = str(link_network.netmask)
        
        # Create or update CE subinterface
        ce_subinterface = self.get_or_create_subinterface(ce_interface, 10)
        if not ce_subinterface:
            self.logger.error(f"Failed getting or updating CE subinterface {ce_subinterface}")
            return False

        # Configure CE subinterface
        ce_subinterface.addressing = "dhcp"
        ce_subinterface.vrf = ce_management_vrf
        ce_subinterface.enabled = True
        if not self.create_or_update_interface(ce_subinterface):
            self.logger.error(f"Failed updating CE subinterface {ce_subinterface}")
            return False

        # Configure PE interface with the correct routing configuration
        pe_interface.addressing = "static"
        pe_interface.ip_address = pe_ip
        pe_interface.subnet_mask = subnet_mask
        pe_interface.enabled = True
        pe_interface.vrf = site.vrf
        pe_interface.dhcp_helper_address = None
        
        if not self.create_or_update_interface(pe_interface):
            self.logger.error(f"Failed updating PE interface {pe_interface} with routing configuration")
            return False

        # Configure PE subinterface to reestablish connection with the CE router
        pe_subinterface = self.get_or_create_subinterface(pe_interface, 10)
        if not pe_subinterface:
            self.logger.error(f"Failed getting or updating PE subinterface {pe_subinterface}")
            return False

        pe_management_vrf = VRF.objects.get(router=pe_router, name=settings.management_vrf)
        pe_subinterface.addressing = "static"
        pe_subinterface.ip_address = str(list(dhcp_scope.hosts())[0])
        pe_subinterface.subnet_mask = site.dhcp_scope.subnet_mask
        pe_subinterface.vrf = pe_management_vrf
        pe_subinterface.dhcp_helper_address = settings.host_address
        pe_subinterface.enabled = True

        if not self.create_or_update_interface(pe_subinterface):
            self.logger.error(f"Failed updating PE subinterface {pe_subinterface}")
            return False

        # Finally configure the CE interface with the correct routing configuration
        ce_interface.addressing = "static"
        ce_interface.ip_address = ce_ip
        ce_interface.subnet_mask = subnet_mask
        ce_interface.enabled = True
        ce_interface.vrf = None
        ce_interface.dhcp_helper_address = None

        if not self.create_or_update_interface(ce_interface):
            self.logger.error(f"Failed updating CE interface {ce_interface}")
            return False

        # Configure OSPF routing between PE and CE routers
    
        # For PE router: Use a unique process ID or reuse an existing one in the site VRF
        pe_ospf_processes = self.list_router_ospf_processes(pe_router)
        if not site.ospf_process_id:
            site.ospf_process_id = max(pe_ospf_processes) + 1
            site.save()
        
        # Create OSPF network advertisement for the link between PE and CE
        networks = [{
            "ip": "0.0.0.0",
            "wildcard": "255.255.255.255",
            "area": 0
        }]
        
        # Configure OSPF on PE router in the site VRF
        if not self.create_or_update_ospf_process(
            router=pe_router,
            process_id=site.ospf_process_id,
            vrf_name=site.vrf.name,
            networks=networks,
            router_id="1.1.1.1"
        ):
            self.logger.error(f"Failed configuring OSPF on PE router {pe_router}")
            return False
        
        # For CE router: Use OSPF process 1
        if not self.create_or_update_ospf_process(
            router=ce_router,
            process_id=1,
            networks=networks,
            router_id="2.2.2.2"
        ):
            self.logger.error(f"Failed configuring OSPF on CE router {ce_router}")
            return False
        
        self.logger.info(f"Successfully configured routing for site {site}")
        return True

    def add_site_to_vpn(self, site, vpn) -> bool:
        try:
            self.logger.info(f"Adding site {site} to VPN {vpn}")
            
            # Get system settings
            settings = get_settings()
            if not settings:
                self.logger.error("Cannot add site to VPN: No settings settings found")
                return False

            # Verify site has PE-CE routing configured
            if not site.assigned_interface or not site.vrf or not site.ospf_process_id:
                self.logger.error(f"Site {site} is not properly configured")
                return False

            # Get all sites in the VPN (excluding the new one)
            existing_sites = vpn.sites.all()

            # Configure route targets for the new site's VRF
            export_rt, created = RouteTarget.objects.update_or_create(
                vrf=site.vrf,
                value=site.vrf.route_distinguisher,
                target_type='export'
            )
            export_rt.save()

            # Import route targets from existing sites
            for other_site in existing_sites:
                # Add import RT for the new site
                import_rt, created = RouteTarget.objects.update_or_create(
                    vrf=site.vrf,
                    value=other_site.vrf.route_distinguisher,
                    target_type='import'
                )
                import_rt.save()

                # Add import RT for the existing site
                import_rt, created = RouteTarget.objects.update_or_create(
                    vrf=other_site.vrf,
                    value=site.vrf.route_distinguisher,
                    target_type='import'
                )
                import_rt.save()

            # Update all VRF configurations on routers
            if not self.create_or_update_vrf(site.vrf):
                self.logger.error(f"Failed to update VRF configuration for site {site}")
                return False

            # Update existing sites' VRF configurations
            for other_site in existing_sites:
                if not self.create_or_update_vrf(other_site.vrf):
                    self.logger.error(f"Failed to update VRF configuration for site {other_site}")
                    return False

            # Enable route redistribution
            payload =  {
                "bgp": {
                    "id": settings.bgp_as,
                    "address-family": {
                        "with-vrf": {
                            "ipv4": [
                                {
                                    "af-name": "unicast",
                                    "vrf": [
                                        {
                                            "name": site.vrf.name,
                                            "ipv4-unicast": {
                                                "redistribute-vrf": {
                                                    "ospf": [
                                                        {
                                                            "id": site.ospf_process_id
                                                        }
                                                    ]
                                                }
                                            }
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                }
            }

            result = self.restconf.patch(
                site.assigned_interface.router.management_ip_address,
                f"Cisco-IOS-XE-native:native/router/bgp={settings.bgp_as}/",
                payload
            )

            if result is None:
                self.logger.error(f"Failed redistributing site's OSPF process {site.ospf_process_id} into BGP")
                return False

            payload = {
                "process-id-vrf": {
                    "id": site.ospf_process_id,
                    "vrf": site.vrf.name,
                    "redistribute": {
                        "bgp": [
                            {
                                "as": settings.bgp_as,
                                "subnets": [None]
                            }
                        ]
                    }
                }
            }

            result = self.restconf.patch(site.assigned_interface.router.management_ip_address, f"Cisco-IOS-XE-native:native/router/router-ospf/ospf/process-id-vrf/", payload)

            if result is None:
                self.logger.error(f"Failed redistributing BGP into site's OSPF process {site.ospf_process_id}")
                return False

            # Update database
            vpn.sites.add(site)
            vpn.save()

            self.logger.info(f"Successfully added site {site} to VPN {vpn}")
            return True
            
        except Exception as exception:
            self.logger.error(f"Error adding site {site} to VPN {vpn}: {str(exception)}")
            return False

    def remove_site_from_vpn(self, site, vpn) -> bool:
        try:
            self.logger.info(f"Removing site {site} from VPN {vpn}")
            
            # Get the site's VRF
            site_vrf = site.vrf
            if not site_vrf:
                self.logger.error(f"Site {site} does not have a VRF configured")
                return False

            # Update the VRF configuration on the router
            if not self.create_or_update_vrf(site_vrf):
                self.logger.error(f"Failed to update VRF configuration for site {site}")
                return False

            # Remove route redistribution
            # TODO: Implement route redistribution removal

            self.logger.info(f"Successfully removed site {site} from VPN {vpn}")
            return True
            
        except Exception as exception:
            self.logger.error(f"Error removing site {site} from VPN {vpn}: {str(exception)}")
            return False

    def delete_vpn(self, vpn) -> bool:
        try:
            self.logger.info(f"Deleting VPN {vpn}")

            # Delete the VPN object
            vpn.delete()
            self.logger.info(f"Successfully deleted VPN {vpn}")
            return True
            
        except Exception as exception:
            self.logger.error(f"Error deleting VPN {vpn}: {str(exception)}")
            return False

NetworkController = _NetworkController()
NetworkController.initialize()
