import requests
import json
import logging
import time
from django.utils import timezone
from datetime import timedelta
from requests.auth import HTTPBasicAuth
from concurrent.futures import ThreadPoolExecutor
from ipaddress import IPv4Network
from django.db import transaction, OperationalError
from collections import defaultdict

from core.models import DHCPLease, Router, VRF, RouteTarget, Interface, VPN

requests.packages.urllib3.disable_warnings()

logger = logging.getLogger(__name__)

class NetworkDiscoverer:
    def __init__(self, username="mgmt", password="mgmtapp", max_workers=5):
        self.username = username
        self.password = password
        self.max_workers = max_workers
        self.headers = {
            'Accept': 'application/yang-data+json',
            'Content-Type': 'application/yang-data+json'
        }
        self.router_cache = {}  # Cache router objects to avoid duplicate DB queries
        self.interface_cache = {}  # Cache interface objects
        
    def discover_network(self):
        """Main method to discover the entire network and populate the database."""
        logger.info("Starting network discovery process")
        
        # Get all active DHCP leases
        active_leases = DHCPLease.objects.filter(expiry_time__gt=timezone.now())
        logger.info(f"Found {active_leases.count()} active DHCP leases")
        
        # Process each device sequentially to avoid database locking issues
        discovered_devices = []
        for lease in active_leases:
            try:
                device_data = self.process_device(lease)
                if device_data:
                    discovered_devices.append(device_data)
            except Exception as e:
                logger.error(f"Error processing device at {lease.ip_address}: {str(e)}")
        
        # Update connections between interfaces
        self.update_interface_connections()
        
        # Discover VPNs based on VRF route targets
        vpn_count = self.discover_vpns()
        
        return {
            "discovered_devices": len(discovered_devices),
            "routers": {
                "total": Router.objects.count(),
                "provider_edge": Router.objects.filter(role='PE').count(),
                "provider_core": Router.objects.filter(role='P').count(),
                "customer_edge": Router.objects.filter(role='CE').count(),
            },
            "vrfs": VRF.objects.count(),
            "vpns": vpn_count,
            "interfaces": Interface.objects.count(),
        }
    
    def discover_vpns(self):
        """Discover VPNs by analyzing route targets across VRFs."""
        logger.info("Starting VPN discovery process")
        
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
                    vpn_name = f"VPN-{i+1}"
                    
                    # Create or get the VPN
                    vpn, created = VPN.objects.get_or_create(
                        name=vpn_name,
                        defaults={'customer': None}  # No customer association as requested
                    )
                    
                    if created:
                        logger.info(f"Created new VPN: {vpn_name}")
                    else:
                        logger.info(f"Using existing VPN: {vpn_name}")
                    
                    # Associate VRFs with this VPN
                    VRF.objects.filter(id__in=vpn_group).update(vpn=vpn)
                    
                    logger.info(f"Associated {len(vpn_group)} VRFs with VPN: {vpn_name}")
                    vpn_count += 1
            except Exception as e:
                logger.error(f"Error creating VPN for group {i+1}: {str(e)}")
        
        logger.info(f"Finished VPN discovery, created/updated {vpn_count} VPNs")
        return vpn_count
    
    def process_device(self, lease):
        """Process a single device using its DHCP lease information."""
        try:
            ip_address = lease.ip_address
            logger.info(f"Processing device at {ip_address}")
            
            # Get LLDP information
            lldp_data = self.get_lldp_data(ip_address)
            if not lldp_data:
                logger.warning(f"No LLDP data for {ip_address}, skipping")
                return None
            
            lldp_state = lldp_data.get('Cisco-IOS-XE-lldp-oper:lldp-entries', {}).get('lldp-state-details', {})
            chassis_id = lldp_state.get('chassis-id')
            hostname = lldp_state.get('system-name')
            
            if not chassis_id or not hostname:
                logger.warning(f"Incomplete LLDP data for {ip_address}, skipping")
                return None
            
            # Check if the router is PE by checking for BGP configuration
            is_pe = self.check_if_pe_router(ip_address)
            role = 'PE' if is_pe else 'P'
            
            # Get VRF data if it's a PE router
            vrf_data = None
            if is_pe:
                vrf_data = self.get_vrf_data(ip_address)
            
            # Get interfaces data
            interfaces_data = self.get_interfaces_data(ip_address)
            
            # Create or update router within a transaction
            # Use multiple retry attempts with small transactions
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    with transaction.atomic():
                        router, created = Router.objects.update_or_create(
                            chassis_id=chassis_id,
                            defaults={
                                'management_ip_address': ip_address,
                                'hostname': hostname,
                                'role': role
                            }
                        )
                        
                        if created:
                            logger.info(f"Created new router: {hostname}")
                        else:
                            logger.info(f"Updated existing router: {hostname}")
                        
                        # Store router in cache
                        self.router_cache[hostname] = router
                    
                    # Break the loop if successful
                    break
                except OperationalError as e:
                    if "database is locked" in str(e) and attempt < max_retries - 1:
                        logger.warning(f"Database locked, retrying ({attempt + 1}/{max_retries})")
                        time.sleep(0.5 * (2 ** attempt))  # Exponential backoff
                    else:
                        raise
            
            # Process VRFs if PE router (in a separate transaction)
            if is_pe and vrf_data:
                for attempt in range(max_retries):
                    try:
                        with transaction.atomic():
                            self.process_vrfs(router, vrf_data)
                        break
                    except OperationalError as e:
                        if "database is locked" in str(e) and attempt < max_retries - 1:
                            logger.warning(f"Database locked during VRF processing, retrying ({attempt + 1}/{max_retries})")
                            time.sleep(0.5 * (2 ** attempt))  # Exponential backoff
                        else:
                            raise
            
            # Process interfaces (in a separate transaction)
            if interfaces_data:
                for attempt in range(max_retries):
                    try:
                        with transaction.atomic():
                            self.process_interfaces(router, interfaces_data)
                        break
                    except OperationalError as e:
                        if "database is locked" in str(e) and attempt < max_retries - 1:
                            logger.warning(f"Database locked during interface processing, retrying ({attempt + 1}/{max_retries})")
                            time.sleep(0.5 * (2 ** attempt))  # Exponential backoff
                        else:
                            raise
            
            return {
                "hostname": hostname,
                "role": role,
                "ip_address": ip_address,
                "chassis_id": chassis_id,
                "is_pe": is_pe
            }
            
        except Exception as e:
            logger.error(f"Error processing device at {lease.ip_address}: {str(e)}")
            return None
    
    def check_if_pe_router(self, ip_address):
        """Check if router is PE by directly checking BGP configuration.
        
        Returns True if it's a PE router, False otherwise.
        """
        url = f"https://{ip_address}/restconf/data/Cisco-IOS-XE-native:native/router/bgp"
        try:
            response = requests.get(
                url,
                headers=self.headers,
                auth=HTTPBasicAuth(self.username, self.password),
                verify=False,
                timeout=10
            )
            
            # A 204 response means the endpoint exists but has no content (not a PE router)
            if response.status_code == 204:
                return False
            
            # A 200 response with content means it's a PE router
            if response.status_code == 200:
                return True
            
            # Any other response means it's not a PE router
            logger.info(f"BGP check for {ip_address} returned {response.status_code}, assuming not PE")
            return False
        except Exception as e:
            logger.error(f"Error checking BGP for {ip_address}: {str(e)}")
            return False
    
    def get_data_with_retry(self, url, max_retries=3):
        """Get data with retry logic."""
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    url,
                    headers=self.headers,
                    auth=HTTPBasicAuth(self.username, self.password),
                    verify=False,
                    timeout=10
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 204:
                    # No content, return empty dict
                    return {}
                elif response.status_code == 404:
                    # Not found, return None
                    return None
                else:
                    logger.warning(f"Failed to get data from {url}: {response.status_code}")
                    if attempt == max_retries - 1:
                        return None
            except Exception as e:
                logger.error(f"Error getting data from {url}: {str(e)}")
                if attempt == max_retries - 1:
                    return None
            
            # Wait before retry with exponential backoff
            time.sleep(1 * (2 ** attempt))
    
    def get_lldp_data(self, ip_address):
        """Get LLDP data from device."""
        url = f"https://{ip_address}/restconf/data/Cisco-IOS-XE-lldp-oper:lldp-entries"
        return self.get_data_with_retry(url)
    
    def get_vrf_data(self, ip_address):
        """Get VRF data from device."""
        url = f"https://{ip_address}/restconf/data/Cisco-IOS-XE-native:native/vrf/definition"
        return self.get_data_with_retry(url)
    
    def get_interfaces_data(self, ip_address):
        """Get interfaces data from device."""
        url = f"https://{ip_address}/restconf/data/Cisco-IOS-XE-interfaces-oper:interfaces"
        return self.get_data_with_retry(url)
    
    def process_vrfs(self, router, vrf_data):
        """Process VRF data and create/update VRF models."""
        definitions = vrf_data.get('Cisco-IOS-XE-native:definition', [])
        
        for vrf_def in definitions:
            vrf_name = vrf_def.get('name')
            if not vrf_name or vrf_name == 'management':
                continue  # Skip management VRF or invalid entries
            
            # Extract route distinguisher
            rd = vrf_def.get('rd', '')
            
            # Create or update VRF - now with router reference
            vrf, created = VRF.objects.update_or_create(
                name=vrf_name,
                router=router,  # Add router as part of lookup
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
                logger.info(f"Created new VRF: {vrf_name} with RD: {rd} on router {router.hostname}")
            else:
                logger.info(f"Updated existing VRF: {vrf_name} on router {router.hostname}")
    
    def process_interfaces(self, router, interfaces_data):
        """Process interfaces data and create/update Interface models."""
        interfaces = interfaces_data.get('Cisco-IOS-XE-interfaces-oper:interfaces', {}).get('interface', [])
        
        for intf in interfaces:
            name = intf.get('name')
            if not name:
                continue
            
            # Get basic info
            admin_status = intf.get('admin-status', 'if-state-down').replace('if-state-', '')
            oper_status = intf.get('oper-status', 'if-oper-state-down').replace('if-oper-state-', '')
            description = intf.get('description', '')
            mac_address = intf.get('phys-address', '')
            
            # Get IP info
            ip_address = intf.get('ipv4')
            subnet_mask = intf.get('ipv4-subnet-mask')
            
            # Get VRF info
            vrf_name = intf.get('vrf')
            vrf = None
            if vrf_name and vrf_name != 'management':
                try:
                    # Look for VRF on this specific router now
                    vrf = VRF.objects.get(name=vrf_name, router=router)
                except VRF.DoesNotExist:
                    logger.warning(f"VRF {vrf_name} on router {router.hostname} not found")
            
            # Create or update interface
            interface, created = Interface.objects.update_or_create(
                router=router,
                name=name,
                defaults={
                    'admin_status': admin_status,
                    'oper_status': oper_status,
                    'description': description,
                    'ip_address': ip_address,
                    'subnet_mask': subnet_mask,
                    'mac_address': mac_address,
                    'vrf': vrf
                }
            )
            
            # Add to interface cache
            key = f"{router.hostname}:{name}"
            self.interface_cache[key] = interface
            
            if created:
                logger.debug(f"Created new interface: {router.hostname} - {name}")
            else:
                logger.debug(f"Updated existing interface: {router.hostname} - {name}")
    
    def update_interface_connections(self):
        """Update interface connections based on LLDP data."""
        logger.info("Starting interface connection update")
        
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
                        logger.warning(f"Local interface {router.hostname}:{local_interface_name} not found")
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
                            logger.warning(f"Remote router {remote_system_name} not found")
                            continue
                        
                        # Find the remote interface
                        try:
                            remote_interface = Interface.objects.get(router=remote_router, name=remote_interface_name)
                        except Interface.DoesNotExist:
                            logger.warning(f"Remote interface {remote_system_name}:{remote_interface_name} not found")
                            continue
                        
                        # Create the connection
                        max_retries = 3
                        for attempt in range(max_retries):
                            try:
                                with transaction.atomic():
                                    local_interface.connected_interfaces.add(remote_interface)
                                    logger.debug(f"Connected {local_interface} to {remote_interface}")
                                break
                            except OperationalError as e:
                                if "database is locked" in str(e) and attempt < max_retries - 1:
                                    logger.warning(f"Database locked, retrying connection ({attempt + 1}/{max_retries})")
                                    time.sleep(0.5 * (2 ** attempt))
                                else:
                                    raise
                    
            except Exception as e:
                logger.error(f"Error updating connections for router {router.hostname}: {str(e)}")
        
        logger.info("Finished interface connection update")
