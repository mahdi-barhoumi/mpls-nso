import logging
import ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.utils import timezone
from django.db import transaction
from core.modules.utils.restconf import RestconfWrapper
from core.models import DHCPLease, Router, VRF, RouteTarget, Interface, Site
from core.settings import get_settings

class _NetworkDiscoverer:
    def __init__(self, max_workers=5):
        self.logger = logging.getLogger('network-discoverer')
        self.max_workers = max_workers
        self.router_cache = {}  # Cache router objects to avoid duplicate DB queries
        self.interface_cache = {}  # Cache interface objects
        self.initialized = False
        # Track discovery statistics
        self.stats = {
            "discovered_devices": 0,
            "routers": {
                "created": 0,
                "updated": 0,
                "total": 0,
                "provider_core": 0,
                "provider_edge": 0,
                "customer_edge": 0
            },
            "vrfs": {
                "created": 0,
                "updated": 0,
                "removed": 0
            },
            "interfaces": {
                "created": 0,
                "updated": 0,
                "removed": 0
            },
            "connections": {
                "created": 0
            }
        }
        # Keep track of reachable routers
        self.reachable_routers = set()
    
    def initialize(self):
        if self.initialized:
            return
            
        settings = get_settings()
        if not settings:
            self.logger.warning("Cannot initialize discoverer: No system settings found")
            return

        # Create RESTCONF wrapper
        self.restconf = RestconfWrapper(max_retries=2, timeout=3)
        
        # Retrieve system settings
        self.settings = settings
        
        # Precompute DHCP sites network
        self.dhcp_sites_network = ipaddress.IPv4Network(
            f"{self.settings.dhcp_sites_network_address}/{self.settings.dhcp_sites_network_subnet_mask}", 
            strict=False
        )

        self.initialized = True

    def discover_network(self):
        self.logger.info("Starting network discovery process")
        
        # Reset statistics
        self.stats = {
            "discovered_devices": 0,
            "routers": {
                "created": 0,
                "updated": 0,
                "total": 0,
                "provider_core": 0,
                "provider_edge": 0,
                "customer_edge": 0
            },
            "vrfs": {
                "created": 0,
                "updated": 0,
                "removed": 0
            },
            "interfaces": {
                "created": 0,
                "updated": 0,
                "removed": 0
            },
            "connections": {
                "created": 0
            }
        }
        self.reachable_routers = set()
        
        # Get all active DHCP leases
        active_leases = DHCPLease.objects.filter(expiry_time__gt=timezone.now())
        self.logger.info(f"Found {active_leases.count()} active DHCP leases")
        
        # Process devices in parallel with thread pool
        discovered_devices = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_ip = {executor.submit(self.discover_ip, lease.ip_address): lease.ip_address for lease in active_leases}
            for future in as_completed(future_to_ip):
                ip_address = future_to_ip[future]
                try:
                    device_data = future.result()
                    if device_data:
                        discovered_devices.append(device_data)
                        self.stats["discovered_devices"] += 1
                except Exception as e:
                    self.logger.error(f"Error processing device at {ip_address}: {str(e)}")
        
        # Update connections between interfaces after discovery
        self.update_interface_connections()
        
        # Update router role counts
        self.stats["routers"]["total"] = len(self.reachable_routers)
        for router in self.reachable_routers:
            if router.role == 'P':
                self.stats["routers"]["provider_core"] += 1
            elif router.role == 'PE':
                self.stats["routers"]["provider_edge"] += 1
            elif router.role == 'CE':
                self.stats["routers"]["customer_edge"] += 1
        
        return self.stats
    
    def discover_ip(self, ip_address):
        try:
            self.logger.info(f"Processing device at {ip_address}")
            
            # Get LLDP information
            lldp_data = self.get_device_data(ip_address, "Cisco-IOS-XE-lldp-oper:lldp-entries")
            if not lldp_data:
                self.logger.warning(f"No LLDP data for {ip_address}, skipping")
                return None
            
            lldp_state = lldp_data.get('Cisco-IOS-XE-lldp-oper:lldp-entries', {}).get('lldp-state-details', {})
            chassis_id = lldp_state.get('chassis-id')
            hostname = lldp_state.get('system-name')
            
            if not chassis_id or not hostname:
                self.logger.warning(f"Incomplete LLDP data for {ip_address}, skipping")
                return None
            
            # Detect router role
            role = self.detect_router_role(ip_address)
            
            # Create or update router
            router = self.create_or_update_router(chassis_id, ip_address, hostname, role)
            
            # Add to reachable routers set
            self.reachable_routers.add(router)
            
            # Store router in cache
            self.router_cache[hostname] = router
            
            # If this is a CE router, try to assign it to its site
            if role == 'CE':
                self.assign_ce_to_site(router, ip_address)
            
            # Get device data
            device_data = self.fetch_device_data(ip_address)
            
            # Process VRFs
            if device_data.get('vrf_data'):
                self.process_vrfs(router, device_data['vrf_data'])
            
            # Process interfaces
            if device_data.get('native_interfaces'):
                self.process_interfaces(router, device_data['native_interfaces'], device_data['oper_interfaces'])
            
            return {
                "hostname": hostname,
                "role": role,
                "ip_address": ip_address,
                "chassis_id": chassis_id
            }
            
        except Exception as e:
            self.logger.error(f"Error processing device at {ip_address}: {str(e)}")
            return None
    
    def fetch_device_data(self, ip_address):
        # Get router data in parallel
        with ThreadPoolExecutor(max_workers=3) as executor:
            vrf_future = executor.submit(self.get_device_data, ip_address, "Cisco-IOS-XE-native:native/vrf/definition")
            native_interfaces_future = executor.submit(self.get_device_data, ip_address, "Cisco-IOS-XE-native:native/interface")
            oper_interfaces_future = executor.submit(self.get_device_data, ip_address, "Cisco-IOS-XE-interfaces-oper:interfaces")
            
            # Wait for all data to be fetched
            vrf_data = vrf_future.result()
            native_interfaces = native_interfaces_future.result()
            oper_interfaces_data = oper_interfaces_future.result()
        
        # Process operational interfaces data for easier access
        oper_interfaces = self.process_oper_interfaces(oper_interfaces_data)
        
        return {
            'vrf_data': vrf_data,
            'native_interfaces': native_interfaces,
            'oper_interfaces': oper_interfaces
        }
    
    def detect_router_role(self, ip_address):
        # Check if IP is in DHCP sites network
        try:
            ip = ipaddress.IPv4Address(ip_address)
            if ip in self.dhcp_sites_network:
                return 'CE'
        except ValueError:
            pass
        
        # Check if router has BGP config
        try:
            bgp_config = self.restconf.get(ip_address, "Cisco-IOS-XE-native:native/router/bgp")
            
            # Validate BGP configuration exists and is not empty
            if not bgp_config or 'Cisco-IOS-XE-bgp:bgp' not in bgp_config:
                return 'P'  # Default to Provider Core if no BGP config
            
            bgp_data = bgp_config.get('Cisco-IOS-XE-bgp:bgp', [{}])
            
            for bgp in bgp_data:
                # Check if BGP AS number matches system settings
                if str(bgp.get('id', '')) == str(self.settings.bgp_as):
                    return 'PE'
            
            # If BGP is configured but doesn't match AS, it might be a P router
            return 'P'
        
        except Exception as e:
            self.logger.warning(f"Error checking BGP config for {ip_address}: {str(e)}")
            
            # Default to Provider Core router in case of any errors
            return 'P'
    
    def get_device_data(self, ip_address, path):
        return self.restconf.get(ip_address, path)
    
    def process_oper_interfaces(self, oper_data):
        if not oper_data:
            return {}
        
        # Create a dictionary of interfaces with interface name as key for easier lookup
        interfaces_by_name = {}
        interfaces = oper_data.get('Cisco-IOS-XE-interfaces-oper:interfaces', {}).get('interface', [])
        for intf in interfaces:
            name = intf.get('name')
            if name:
                interfaces_by_name[name] = intf
        
        return interfaces_by_name
    
    def create_or_update_router(self, chassis_id, ip_address, hostname, role):
        router, created = Router.objects.update_or_create(
            chassis_id=chassis_id,
            defaults={
                'management_ip_address': ip_address,
                'hostname': hostname,
                'role': role
            }
        )
        
        if created:
            self.logger.info(f"Created new router: {hostname} (Role: {role})")
            self.stats["routers"]["created"] += 1
        else:
            self.logger.info(f"Updated existing router: {hostname} (Role: {role})")
            self.stats["routers"]["updated"] += 1
            
        return router
    
    def assign_ce_to_site(self, router, ip_address):
        try:
            # Convert IP address to IPv4Address object
            ce_ip = ipaddress.IPv4Address(ip_address)
            
            # Get all sites with their DHCP scopes
            sites = Site.objects.select_related('dhcp_scope').all()
            
            # Find the matching site
            for site in sites:
                if not site.dhcp_scope:
                    continue
                    
                # Create network from the site's DHCP scope
                network = ipaddress.IPv4Network(
                    f"{site.dhcp_scope.network}/{site.dhcp_scope.subnet_mask}", 
                    strict=False
                )
                
                # Check if CE IP is in this network
                if ce_ip in network:
                    # Assign router to site
                    site.router = router
                    site.save()
                    self.logger.info(f"Assigned CE router {router.hostname} to site {site}")
                    return
            
            self.logger.warning(f"No matching site found for CE router {router.hostname} with IP {ip_address}")
        
        except Exception as e:
            self.logger.error(f"Error assigning CE router {router.hostname} to site: {str(e)}")

    def process_vrfs(self, router, vrf_data):
        definitions = vrf_data.get('Cisco-IOS-XE-native:definition', [])
        
        # Create set of valid VRF names to later clean up deleted VRFs
        discovered_vrf_names = set()
        
        for vrf_def in definitions:
            vrf_name = vrf_def.get('name')
            if not vrf_name:
                continue
                
            discovered_vrf_names.add(vrf_name)
            
            # Extract route distinguisher
            rd = vrf_def.get('rd', None)
            
            # Create or update VRF
            vrf, created = VRF.objects.update_or_create(
                name=vrf_name,
                router=router,
                defaults={
                    'route_distinguisher': rd
                }
            )
            
            # Process route targets
            address_family = vrf_def.get('address-family', {})
            ipv4 = address_family.get('ipv4', {})
            route_target = ipv4.get('route-target', {})
            
            # Get existing route targets for this VRF
            existing_rts = set(RouteTarget.objects.filter(vrf=vrf).values_list('value', 'target_type'))
            discovered_rts = set()
            
            # Import route targets
            import_rts = route_target.get('import-route-target', {}).get('without-stitching', [])
            for rt in import_rts:
                rt_value = rt.get('asn-ip', '')
                if rt_value:
                    discovered_rts.add((rt_value, 'import'))
                    RouteTarget.objects.update_or_create(
                        vrf=vrf,
                        value=rt_value,
                        target_type='import'
                    )
            
            # Export route targets
            export_rts = route_target.get('export-route-target', {}).get('without-stitching', [])
            for rt in export_rts:
                rt_value = rt.get('asn-ip', '')
                if rt_value:
                    discovered_rts.add((rt_value, 'export'))
                    RouteTarget.objects.update_or_create(
                        vrf=vrf,
                        value=rt_value,
                        target_type='export'
                    )
            
            # Remove route targets that no longer exist
            for rt_value, target_type in existing_rts - discovered_rts:
                RouteTarget.objects.filter(vrf=vrf, value=rt_value, target_type=target_type).delete()
            
            if created:
                self.logger.info(f"Created new VRF: {vrf_name} with RD: {rd} on router {router.hostname}")
                self.stats["vrfs"]["created"] += 1
            else:
                self.logger.info(f"Updated existing VRF: {vrf_name} on router {router.hostname}")
                self.stats["vrfs"]["updated"] += 1
        
        # Clean up VRFs that no longer exist on the router
        removed_count = VRF.objects.filter(router=router).exclude(name__in=discovered_vrf_names).delete()[0]
        if removed_count > 0:
            self.logger.info(f"Removed {removed_count} VRFs that no longer exist on router {router.hostname}")
            self.stats["vrfs"]["removed"] += removed_count
    
    def process_interfaces(self, router, native_interfaces, oper_interfaces):
        self.logger.info(f"Processing interfaces for router {router.hostname}")
        
        # Dictionary to collect interface data before creating/updating
        interface_data = {}
        
        # Process operational interface data
        if oper_interfaces:
            for intf_name, oper_intf in oper_interfaces.items():
                # Add interface to our collection if not already there
                if intf_name not in interface_data:
                    interface_data[intf_name] = self.extract_interface_data_from_oper(router, intf_name, oper_intf)
        
        # Process native interface data to get additional configuration details
        discovered_interfaces = set()
        if native_interfaces and 'Cisco-IOS-XE-native:interface' in native_interfaces:
            native_intf_data = native_interfaces['Cisco-IOS-XE-native:interface']
            
            # Process each interface type (GigabitEthernet, Loopback, etc.)
            for intf_type, interfaces in native_intf_data.items():
                for intf in interfaces:
                    name_value = intf.get('name')
                    if name_value is None:
                        continue
                    
                    # Construct full interface name
                    name = f"{intf_type}{name_value}"
                    discovered_interfaces.add(name)
                    
                    # Create or update the interface data
                    self.update_interface_data_from_native(interface_data, router, name, intf)
        
        # Now create or update interfaces with the collected data
        self.save_interfaces(router, interface_data, discovered_interfaces)
    
    def extract_interface_data_from_oper(self, router, intf_name, oper_intf):
        # Extract base interface data from operational data
        data = {
            'router': router,
            'name': intf_name,
            'enabled': oper_intf.get('admin-status', 'if-state-down').replace('if-state-', '') == 'up',
            'description': oper_intf.get('description', ''),
            'mac_address': oper_intf.get('phys-address', '00:00:00:00:00:00'),
            'addressing': 'dhcp',  # Default, will be updated from native config if available
            'vrf': None,
            'vlan': None,
            'dhcp_helper_address': None
        }
        
        # Get IP address and subnet mask
        temp_ip = oper_intf.get('ipv4')
        temp_mask = oper_intf.get('ipv4-subnet-mask')
        
        # Set to null if equal to "0.0.0.0"
        data['ip_address'] = None if not temp_ip or temp_ip == "0.0.0.0" else temp_ip
        data['subnet_mask'] = None if not temp_mask or temp_mask == "0.0.0.0" else temp_mask
        
        # Get VRF info from operational data
        vrf_name = oper_intf.get('vrf')
        if vrf_name:
            try:
                vrf = VRF.objects.get(name=vrf_name, router=router)
                data['vrf'] = vrf
            except VRF.DoesNotExist:
                self.logger.warning(f"VRF {vrf_name} on router {router.hostname} not found")
        
        return data
    
    def update_interface_data_from_native(self, interface_data, router, name, intf):
        # Create entry if not already in our collection
        if name not in interface_data:
            interface_data[name] = {
                'router': router,
                'name': name,
                'enabled': 'shutdown' not in intf,
                'description': intf.get('description', ''),
                'mac_address': '00:00:00:00:00:00',  # Default, will be updated if found in oper data
                'addressing': 'dhcp',
                'ip_address': None,
                'subnet_mask': None,
                'vrf': None,
                'vlan': None,
                'dhcp_helper_address': None
            }
        else:
            # Update enabled status and description
            interface_data[name]['enabled'] = 'shutdown' not in intf
            interface_data[name]['description'] = intf.get('description', '')
        
        # Check for static IP configuration
        if 'ip' in intf and 'address' in intf['ip'] and 'primary' in intf['ip']['address']:
            interface_data[name]['addressing'] = 'static'
        
        # Get VRF information
        if 'vrf' in intf and 'forwarding' in intf['vrf']:
            vrf_name = intf['vrf']['forwarding']
            try:
                vrf = VRF.objects.get(name=vrf_name, router=router)
                interface_data[name]['vrf'] = vrf
            except VRF.DoesNotExist:
                self.logger.warning(f"VRF {vrf_name} on router {router.hostname} not found")
        
        # Get DHCP helper address if available
        if 'ip' in intf and 'helper-address' in intf['ip']:
            helpers = intf['ip']['helper-address']
            if helpers and len(helpers) > 0:
                interface_data[name]['dhcp_helper_address'] = helpers[0].get('address')
        
        # Get VLAN information for subinterfaces
        if 'encapsulation' in intf and 'dot1Q' in intf['encapsulation']:
            interface_data[name]['vlan'] = intf['encapsulation']['dot1Q'].get('vlan-id')
    
    def save_interfaces(self, router, interface_data, discovered_interfaces):
        with transaction.atomic():
            # Create or update interfaces
            for name, data in interface_data.items():
                try:
                    # Get or create a new interface object
                    interface, new = Interface.objects.get_or_new(
                        router=router,
                        name=name,
                    )
                    
                    # Only set MAC address for new interfaces (immutable field)
                    if new:
                        interface.mac_address = data['mac_address']
                        self.stats["interfaces"]["created"] += 1
                    else:
                        self.stats["interfaces"]["updated"] += 1
                    
                    # Update the interface with collected data
                    interface.description = data['description']
                    interface.enabled = data['enabled']
                    interface.addressing = data['addressing']
                    interface.ip_address = data['ip_address']
                    interface.subnet_mask = data['subnet_mask']
                    interface.dhcp_helper_address = data['dhcp_helper_address']
                    interface.vlan = data['vlan']
                    interface.vrf = data['vrf']
                    
                    # Save the interface
                    interface.save()
                    
                    # Add to interface cache for connection discovery later
                    key = f"{router.hostname}:{name}"
                    self.interface_cache[key] = interface
                    
                    if new:
                        self.logger.debug(f"Created new interface: {router.hostname} - {name}")
                    else:
                        self.logger.debug(f"Updated existing interface: {router.hostname} - {name}")
                
                except Exception as e:
                    self.logger.error(f"Error saving interface {name} on router {router.hostname}: {str(e)}")
            
            # Remove interfaces that no longer exist on the router
            if discovered_interfaces:
                removed_count = Interface.objects.filter(router=router).exclude(name__in=discovered_interfaces).delete()[0]
                if removed_count > 0:
                    self.logger.info(f"Removed {removed_count} interfaces that no longer exist on router {router.hostname}")
                    self.stats["interfaces"]["removed"] += removed_count
    
    def update_interface_connections(self):
        self.logger.info("Starting interface connection update")
        
        # Only process connections for routers that were reachable
        routers = list(self.reachable_routers)
        
        # Process connections in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.process_router_connections, router): router 
                      for router in routers}
            
            for future in as_completed(futures):
                router = futures[future]
                try:
                    future.result()
                except Exception as e:
                    self.logger.error(f"Error updating connections for router {router.hostname}: {str(e)}")
        
        self.logger.info("Finished interface connection update")
    
    def process_router_connections(self, router):
        try:
            # Get LLDP data
            lldp_data = self.get_device_data(router.management_ip_address, "Cisco-IOS-XE-lldp-oper:lldp-entries")
            if not lldp_data:
                return
            
            # Get LLDP interface details
            lldp_intf_details = lldp_data.get('Cisco-IOS-XE-lldp-oper:lldp-entries', {}).get('lldp-intf-details', [])
            
            # Get all interfaces for this router
            router_interfaces = {interface.name: interface for interface in Interface.objects.filter(router=router)}
            
            # Get routers by chassis ID for faster lookup (only use reachable routers)
            routers_by_chassis = {r.chassis_id: r for r in self.reachable_routers}
            
            # Process LLDP interface details
            for intf_detail in lldp_intf_details:
                local_interface_name = intf_detail.get('if-name')
                neighbor_details = intf_detail.get('lldp-neighbor-details', [])
                
                if not local_interface_name or not neighbor_details:
                    continue
                
                # Get the local interface
                local_interface = router_interfaces.get(local_interface_name)
                if not local_interface:
                    self.logger.warning(f"Local interface {router.hostname}:{local_interface_name} not found")
                    continue
                
                # Clear existing connections for this interface
                with transaction.atomic():
                    local_interface.connected_interfaces.clear()
                
                # Process each neighbor
                for neighbor in neighbor_details:
                    self.process_neighbor_connection(local_interface, neighbor, routers_by_chassis)
        
        except Exception as e:
            self.logger.error(f"Error processing connections for router {router.hostname}: {str(e)}")
    
    def process_neighbor_connection(self, local_interface, neighbor, routers_by_chassis):
        remote_system_name = neighbor.get('system-name')
        port_id = neighbor.get('port-id', '')
        remote_chassis_id = neighbor.get('chassis-id')
        
        if not (remote_system_name and port_id and remote_chassis_id):
            return
        
        # Normalize interface name (handle various formats)
        remote_interface_name = self.normalize_interface_name(port_id)
        
        # Find the remote router - only if it's reachable
        remote_router = routers_by_chassis.get(remote_chassis_id)
        if not remote_router:
            self.logger.warning(f"Remote router {remote_system_name} not found or not reachable")
            return
        
        # Find the remote interface
        try:
            remote_interface = Interface.objects.get(router=remote_router, name=remote_interface_name)
        except Interface.DoesNotExist:
            self.logger.warning(f"Remote interface {remote_system_name}:{remote_interface_name} not found")
            return
        
        # Create the connection
        with transaction.atomic():
            local_interface.connected_interfaces.add(remote_interface)
            self.logger.debug(f"Connected {local_interface} to {remote_interface}")
            self.stats["connections"]["created"] += 1
    
    def normalize_interface_name(self, port_id):
        # Common interface abbreviation mappings
        mappings = {
            'Gi': 'GigabitEthernet',
            'Te': 'TenGigabitEthernet',
            'Fa': 'FastEthernet',
            'Eth': 'Ethernet',
            'Lo': 'Loopback',
            'Po': 'Port-Channel',
            'Vl': 'Vlan'
        }
        
        # Check if port_id starts with any known abbreviation
        for abbr, full in mappings.items():
            if port_id.startswith(abbr):
                return port_id.replace(abbr, full, 1)
        
        return port_id

NetworkDiscoverer = _NetworkDiscoverer()
NetworkDiscoverer.initialize()
