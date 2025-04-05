import time
import logging
import ipaddress
from datetime import timedelta
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from django.utils import timezone
from django.db import transaction, OperationalError
from core.modules.utils.restconf import RestconfWrapper
from core.models import DHCPLease, DHCPScope, Router, VRF, RouteTarget, Interface, VPN, Site
from core.settings import get_settings

class NetworkDiscoverer:
    def __init__(self, max_workers=5):
        self.max_workers = max_workers
        self.router_cache = {}  # Cache router objects to avoid duplicate DB queries
        self.interface_cache = {}  # Cache interface objects
        
        # Setup logger within the class
        self.logger = logging.getLogger('discovery')
        
        # Create RESTCONF wrapper
        self.restconf = RestconfWrapper()
        
        # Retrieve system settings
        self.settings = get_settings()
        
        # Precompute DHCP sites network
        self.dhcp_sites_network = ipaddress.IPv4Network(
            f"{self.settings.dhcp_sites_network_address}/{self.settings.dhcp_sites_network_subnet_mask}", 
            strict=False
        )
        
    def discover_network(self):
        self.logger.info("Starting network discovery process")
        
        # Get all active DHCP leases
        active_leases = DHCPLease.objects.filter(expiry_time__gt=timezone.now())
        self.logger.info(f"Found {active_leases.count()} active DHCP leases")
        
        # Process each device sequentially to avoid database locking issues
        discovered_devices = []
        for lease in active_leases:
            try:
                device_data = self.process_device(lease)
                if device_data:
                    discovered_devices.append(device_data)
            except Exception as e:
                self.logger.error(f"Error processing device at {lease.ip_address}: {str(e)}")
        
        # Update connections between interfaces
        self.update_interface_connections()
        
        # Discover VPNs based on VRF route targets
        #vpn_count = self.discover_vpns()
        
        return {
            "discovered_devices": len(discovered_devices),
            "routers": {
                "total": Router.objects.count(),
                "provider_core": Router.objects.filter(role='P').count(),
                "provider_edge": Router.objects.filter(role='PE').count(),
                "customer_edge": Router.objects.filter(role='CE').count()
            },
            "vrfs": VRF.objects.count(),
            "interfaces": Interface.objects.count(),
        }
    
    def discover_vpns(self):
        self.logger.info("Starting VPN discovery process")
        
        # Group VRFs by their export route targets
        rt_to_vrfs = defaultdict(set)
        vrf_export_rts = {}
        
        # Get all VRFs and their route targets
        all_vrfs = VRF.objects.all().prefetch_related('route_targets')
        
        # First pass: Collect export RTs for each VRF
        for vrf in all_vrfs:
            export_rts = set(vrf.export_targets)
            vrf_export_rts[vrf.id] = export_rts
            
            # Map each export RT to the VRFs that export it
            for rt in export_rts:
                rt_to_vrfs[rt].add(vrf.id)
        
        # Group VRFs into potential VPNs based on route target relationships
        vpn_groups = []
        processed_vrfs = set()
        
        # First, handle VRFs that are related to other VRFs
        for vrf_id, export_rts in vrf_export_rts.items():
            if vrf_id in processed_vrfs:
                continue
                
            # Start a new potential VPN group with this VRF
            vpn_group = {vrf_id}
            processed_vrfs.add(vrf_id)
            
            # Find other VRFs that import this VRF's exports or export what this VRF imports
            related_vrfs = set()
            for rt in export_rts:
                # Add VRFs that export this RT
                related_vrfs.update(rt_to_vrfs[rt])
            
            # Add all related VRFs to this VPN group
            for related_vrf_id in related_vrfs:
                if related_vrf_id not in processed_vrfs:
                    vpn_group.add(related_vrf_id)
                    processed_vrfs.add(related_vrf_id)
            
            # Add this group regardless of size (allows single VRF VPNs)
            vpn_groups.append(vpn_group)
        
        # Now, process any VRFs that weren't included in any group yet
        for vrf in all_vrfs:
            if vrf.id not in processed_vrfs:
                # Create a single-VRF VPN group
                vpn_groups.append({vrf.id})
                processed_vrfs.add(vrf.id)
        
        # Create VPN objects for each VPN group
        vpn_count = 0
        for i, vpn_group in enumerate(vpn_groups):
            try:
                with transaction.atomic():
                    # Create a generic VPN name
                    vpn_name = f"Discovered VPN {i+1}"
                    
                    # Create or get the VPN
                    vpn, created = VPN.objects.get_or_create(
                        name=vpn_name,
                        discovered=True
                    )
                    
                    if created:
                        self.logger.info(f"Created new VPN: {vpn_name}")
                    else:
                        self.logger.info(f"Using existing VPN: {vpn_name}")
                    
                    # Associate VRFs with this VPN
                    VRF.objects.filter(id__in=vpn_group).update(vpn=vpn)
                    
                    self.logger.info(f"Associated {len(vpn_group)} VRFs with VPN: {vpn_name}")
                    vpn_count += 1
            except Exception as e:
                self.logger.error(f"Error creating VPN for group {i+1}: {str(e)}")
        
        self.logger.info(f"Finished VPN discovery, created/updated {vpn_count} VPNs")
        return vpn_count
    
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

    def process_device(self, lease):
        try:
            ip_address = lease.ip_address
            self.logger.info(f"Processing device at {ip_address}")
            
            # Get LLDP information
            lldp_data = self.get_lldp_data(ip_address)
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
            
            # Get VRF data
            vrf_data = None
            vrf_data = self.get_vrf_data(ip_address)
            
            # Get interfaces data (both native and operational)
            native_interfaces = self.get_native_interfaces_data(ip_address)
            oper_interfaces = self.get_interfaces_oper_data(ip_address)
            
            # Create or update router
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
            else:
                self.logger.info(f"Updated existing router: {hostname} (Role: {role})")
            
            # Store router in cache
            self.router_cache[hostname] = router
            
            # If this is a CE router, try to assign it to its site
            if role == 'CE':
                self.assign_ce_to_site(router, ip_address)
            
            # Process VRFs
            self.process_vrfs(router, vrf_data)
            
            # Process interfaces
            if native_interfaces:
                self.process_interfaces(router, native_interfaces, oper_interfaces)
            
            return {
                "hostname": hostname,
                "role": role,
                "ip_address": ip_address,
                "chassis_id": chassis_id
            }
            
        except Exception as e:
            self.logger.error(f"Error processing device at {lease.ip_address}: {str(e)}")
            return None
    
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

    def get_lldp_data(self, ip_address):
        return self.restconf.get(ip_address, "Cisco-IOS-XE-lldp-oper:lldp-entries")
    
    def get_vrf_data(self, ip_address):
        return self.restconf.get(ip_address, "Cisco-IOS-XE-native:native/vrf/definition")
    
    def get_native_interfaces_data(self, ip_address):
        return self.restconf.get(ip_address, "Cisco-IOS-XE-native:native/interface")
    
    def get_interfaces_oper_data(self, ip_address):
        oper_data = self.restconf.get(ip_address, "Cisco-IOS-XE-interfaces-oper:interfaces")
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
    
    def process_vrfs(self, router, vrf_data):
        definitions = vrf_data.get('Cisco-IOS-XE-native:definition', [])
        
        for vrf_def in definitions:
            vrf_name = vrf_def.get('name')
            
            # Skip management VRFs
            #if vrf_name == self.settings.management_vrf:
            #    continue
            
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
            
            # Import route targets
            import_rts = route_target.get('import-route-target', {}).get('without-stitching', [])
            for rt in import_rts:
                rt_value = rt.get('asn-ip', '')
                if rt_value:
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
                    RouteTarget.objects.update_or_create(
                        vrf=vrf,
                        value=rt_value,
                        target_type='export'
                    )
            
            if created:
                self.logger.info(f"Created new VRF: {vrf_name} with RD: {rd} on router {router.hostname}")
            else:
                self.logger.info(f"Updated existing VRF: {vrf_name} on router {router.hostname}")
    
    def process_interfaces(self, router, native_interfaces, oper_interfaces):
        self.logger.info(f"Processing interfaces for router {router.hostname}")
        
        # Combine all discovered interfaces
        discovered_interfaces = set()
        
        # Process each interface type in native interface data
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
                    
                    # Determine if interface is enabled or shutdown
                    enabled = 'shutdown' not in intf
                    
                    # Get interface description if available
                    description = intf.get('description', '')
                    
                    # Get VRF information
                    vrf_name = None
                    vrf = None
                    if 'vrf' in intf and 'forwarding' in intf['vrf']:
                        vrf_name = intf['vrf']['forwarding']
                        if vrf_name != self.settings.management_vrf:
                            try:
                                vrf = VRF.objects.get(name=vrf_name, router=router)
                            except VRF.DoesNotExist:
                                self.logger.warning(f"VRF {vrf_name} on router {router.hostname} not found")
                    
                    # Get IP address and subnet mask from operational data
                    ip_address = None
                    subnet_mask = None
                    addressing = 'dhcp'  # Default to DHCP if not found
                    
                    # Look up the interface in operational data
                    if name in oper_interfaces:
                        oper_intf = oper_interfaces[name]
                        
                        # Get IP address and subnet mask from operational data
                        temp_ip = oper_intf.get('ipv4')
                        temp_mask = oper_intf.get('ipv4-subnet-mask')
                        
                        # Set to null if equal to "0.0.0.0"
                        if temp_ip and temp_ip != "0.0.0.0":
                            ip_address = temp_ip
                            addressing = 'static'
                        
                        if temp_mask and temp_mask != "0.0.0.0":
                            subnet_mask = temp_mask
                    
                    # Get DHCP helper address if available
                    dhcp_helper_address = None
                    if 'ip' in intf and 'helper-address' in intf['ip']:
                        helpers = intf['ip']['helper-address']
                        if helpers and len(helpers) > 0:
                            dhcp_helper_address = helpers[0].get('address')
                    
                    # Get VLAN information for subinterfaces
                    vlan = None
                    if 'encapsulation' in intf and 'dot1Q' in intf['encapsulation']:
                        vlan = intf['encapsulation']['dot1Q'].get('vlan-id')
                    
                    # Get MAC address from operational data
                    mac_address = None
                    if name in oper_interfaces:
                        oper_intf = oper_interfaces[name]
                        mac_address = oper_intf.get('phys-address', '')
                    
                    # Create a temporary Interface object to check if it's new
                    interface, new = Interface.objects.get_or_new(
                        router=router,
                        name=name,
                    )
                    
                    # Update interface properties
                    if new:
                        # Only set MAC address when creating a new interface
                        # since it's an immutable field
                        interface.mac_address = mac_address
                    
                    interface.description = description
                    interface.enabled = enabled
                    interface.addressing = addressing
                    interface.ip_address = ip_address
                    interface.subnet_mask = subnet_mask
                    interface.dhcp_helper_address = dhcp_helper_address
                    interface.vlan = vlan
                    interface.vrf = vrf
                    
                    # Save the interface
                    try:
                        interface.save()
                        
                        # Add to interface cache
                        key = f"{router.hostname}:{name}"
                        self.interface_cache[key] = interface
                        
                        if created:
                            self.logger.debug(f"Created new interface: {router.hostname} - {name}")
                        else:
                            self.logger.debug(f"Updated existing interface: {router.hostname} - {name}")
                    except Exception as e:
                        self.logger.error(f"Error saving interface {name} on router {router.hostname}: {str(e)}")
        
        # Handle interfaces not found in native data but present in operational data
        for intf_name, oper_intf in oper_interfaces.items():
            if intf_name not in discovered_interfaces:
                try:
                    # Get basic info from operational data
                    enabled = oper_intf.get('admin-status', 'if-state-down').replace('if-state-', '') == 'up'
                    description = oper_intf.get('description', '')
                    mac_address = oper_intf.get('phys-address', '')
                    
                    # Get IP info from operational data
                    temp_ip = oper_intf.get('ipv4')
                    temp_mask = oper_intf.get('ipv4-subnet-mask')
                    
                    # Set to null if equal to "0.0.0.0"
                    ip_address = None
                    subnet_mask = None
                    addressing = 'dhcp'
                    
                    if temp_ip and temp_ip != "0.0.0.0":
                        ip_address = temp_ip
                        addressing = 'static'
                    
                    if temp_mask and temp_mask != "0.0.0.0":
                        subnet_mask = temp_mask
                    
                    # Get VRF info
                    vrf_name = oper_intf.get('vrf')
                    vrf = None
                    if vrf_name and vrf_name != self.settings.management_vrf:
                        try:
                            vrf = VRF.objects.get(name=vrf_name, router=router)
                        except VRF.DoesNotExist:
                            self.logger.warning(f"VRF {vrf_name} on router {router.hostname} not found")
                    
                    # Create a temporary Interface object to check if it's new
                    interface, new = Interface.objects.get_or_new(
                        router=router,
                        name=intf_name,
                    )
                    
                    # Update interface properties
                    if new:
                        # Only set MAC address when creating a new interface
                        # since it's an immutable field
                        interface.mac_address = mac_address or '00:00:00:00:00:00'  # Default MAC if not found
                    
                    interface.description = description
                    interface.enabled = enabled
                    interface.addressing = addressing
                    interface.ip_address = ip_address
                    interface.subnet_mask = subnet_mask
                    interface.vrf = vrf
                    
                    # Save the interface
                    interface.save()
                    
                    # Add to interface cache
                    key = f"{router.hostname}:{intf_name}"
                    self.interface_cache[key] = interface
                    
                    if created:
                        self.logger.debug(f"Created new interface from oper data: {router.hostname} - {intf_name}")
                    else:
                        self.logger.debug(f"Updated existing interface from oper data: {router.hostname} - {intf_name}")
                
                except Exception as e:
                    self.logger.error(f"Error processing interface {intf_name} from oper data on router {router.hostname}: {str(e)}")
    
    def update_interface_connections(self):
        self.logger.info("Starting interface connection update")
        
        # Get all routers
        routers = list(Router.objects.all())
        
        # Process each router
        for router in routers:
            try:
                # Get LLDP data
                lldp_data = self.get_lldp_data(router.management_ip_address)
                if not lldp_data:
                    continue
                
                # Get LLDP interface details - this uses the more detailed info
                lldp_intf_details = lldp_data.get('Cisco-IOS-XE-lldp-oper:lldp-entries', {}).get('lldp-intf-details', [])
                
                # Get all interfaces for this router
                router_interfaces = {}
                for interface in Interface.objects.filter(router=router):
                    router_interfaces[interface.name] = interface
                
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
                        remote_system_name = neighbor.get('system-name')
                        remote_interface_name = neighbor.get('port-desc')
                        remote_chassis_id = neighbor.get('chassis-id')
                        
                        if not (remote_system_name and remote_interface_name and remote_chassis_id):
                            continue
                        
                        # Find the remote router
                        remote_router = None
                        for r in routers:
                            if r.hostname == remote_system_name:
                                remote_router = r
                                break
                        
                        if not remote_router:
                            self.logger.warning(f"Remote router {remote_system_name} not found")
                            continue
                        
                        # Find the remote interface
                        try:
                            remote_interface = Interface.objects.get(router=remote_router, name=remote_interface_name)
                        except Interface.DoesNotExist:
                            self.logger.warning(f"Remote interface {remote_system_name}:{remote_interface_name} not found")
                            continue
                        
                        # Create the connection
                        max_retries = 3
                        for attempt in range(max_retries):
                            try:
                                with transaction.atomic():
                                    local_interface.connected_interfaces.add(remote_interface)
                                    self.logger.debug(f"Connected {local_interface} to {remote_interface}")
                                break
                            except OperationalError as e:
                                if "database is locked" in str(e) and attempt < max_retries - 1:
                                    self.logger.warning(f"Database locked, retrying connection ({attempt + 1}/{max_retries})")
                                    time.sleep(0.5 * (2 ** attempt))
                                else:
                                    raise
                    
            except Exception as e:
                self.logger.error(f"Error updating connections for router {router.hostname}: {str(e)}")
        
        self.logger.info("Finished interface connection update")