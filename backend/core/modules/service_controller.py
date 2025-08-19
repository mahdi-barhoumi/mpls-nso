import logging
import ipaddress
from typing import List, Optional, Tuple
from backend.core.modules.network_controller import NetworkController
from core.models import Site, VPN, Customer, Interface, Router, VRF, RouteTarget, DHCPScope
from core.settings import get_settings

class _ServiceController:
    def __init__(self):
        self.logger = logging.getLogger('service-controller')
        self.initialized = False

    def initialize(self):
        if self.initialized:
            return
            
        settings = get_settings()
        if not settings:
            self.logger.warning("Cannot initialize service controller: No system settings found")
            return

        self.settings = settings
        self.initialized = True
    
    def create_site(self, name: str, customer: Customer, interface: Interface, description: str = '', location: str = '') -> Tuple[Optional[Site], bool]:
        try:
            self.logger.info(f"Creating new site {name}")

            # Parse the DHCP sites network from settings
            dhcp_sites_network = ipaddress.IPv4Network(
                f"{self.settings.dhcp_sites_network_address}/{self.settings.dhcp_sites_network_subnet_mask}", 
                strict=False
            )

            # Get all existing site DHCP scopes
            existing_scopes = DHCPScope.objects.all()
            used_scopes = {
                ipaddress.IPv4Network(f"{scope.network}/30", strict=False) 
                for scope in existing_scopes
            }

            # Find first available /30 subnet
            dhcp_scope_network = None
            for network in dhcp_sites_network.subnets(new_prefix=30):
                if not any(network.overlaps(used_scope) for used_scope in used_scopes):
                    dhcp_scope_network = str(network[0])
                    break

            if not dhcp_scope_network:
                raise Exception('No available DHCP scope found')

            # Create DHCP Scope
            dhcp_scope = DHCPScope.objects.create(
                is_active=False,
                network=dhcp_scope_network,
                subnet_mask='255.255.255.252'
            )

            # Create site
            site = Site.objects.create(
                name=name,
                customer=customer,
                description=description,
                location=location,
                dhcp_scope=dhcp_scope,
            )

            # Assign interface using NetworkController
            if not NetworkController.assign_interface(interface, site):
                # Clean up if interface assignment fails
                dhcp_scope.delete()
                site.delete()
                raise Exception('Failed to assign interface to site')

            self.logger.info(f"Successfully created site {site}")
            return site, True

        except Exception as e:
            self.logger.error(f"Error creating site: {str(e)}")
            return None, False

    def delete_site(self, site: Site) -> bool:
        try:
            self.logger.info(f"Deleting site {site}")

            # Remove the site from all VPNs first
            for vpn in site.vpns.all():
                if not self.remove_site_from_vpn(site, vpn):
                    self.logger.error(f"Failed to remove site from VPN {vpn}")
                    return False
            
            # Disable routing if enabled
            if site.has_routing:
                if not NetworkController.disable_routing(site):
                    self.logger.error(f"Failed to remove site: Could not disable routing")
                    return False

            # Delete the CE router and all its interfaces if it exists
            if site.router:
                try:
                    ce_interface = site.assigned_interface.connected_interfaces.first()
                    ce_interface.addressing = 'dhcp'
                    NetworkController.create_or_update_interface(ce_interface)
                except:
                    pass

            # Unassign the PE interface if assigned
            if site.assigned_interface:
                if not NetworkController.unassign_interface(site):
                    self.logger.error(f"Failed to unassign interface from site")
                    return False

            # Delete the site's VRF and its route targets if it exists
            if site.vrf:
                RouteTarget.objects.filter(vrf=site.vrf).delete()
                if not NetworkController.delete_vrf(site.vrf):
                    self.logger.error(f"Failed to delete site VRF")
                    return False

            if site.router:
                # Delete the CE router
                site.router.delete()

            # Delete the DHCP scope if it exists
            if site.dhcp_scope:
                site.dhcp_scope.delete()

            # Finally delete the site
            site.delete()

            self.logger.info(f"Successfully deleted site {site}")
            return True

        except Exception as e:
            self.logger.error(f"Error deleting site: {str(e)}")
            return False

    def enable_site_routing(self, site: Site) -> bool:
        return NetworkController.enable_routing(site)

    def disable_site_routing(self, site: Site) -> bool:
        return NetworkController.disable_routing(site)

    def create_vpn(self, name: str, customer: Customer, description: str = '') -> Tuple[Optional[VPN], bool]:
        try:
            vpn = VPN.objects.create(
                name=name,
                customer=customer,
                description=description
            )
            self.logger.info(f"Successfully created VPN {vpn}")
            return vpn, True
        except Exception as e:
            self.logger.error(f"Error creating VPN: {str(e)}")
            return None, False

    def delete_vpn(self, vpn: VPN) -> bool:
        try:
            self.logger.info(f"Deleting VPN {vpn}")
            
            # Remove all sites from the VPN
            for site in vpn.sites.all():
                if not self.remove_site_from_vpn(site, vpn):
                    self.logger.error(f"Failed to remove site {site} from VPN {vpn}")
                    return False
            
            # Delete the VPN from the database
            vpn.delete()
            
            self.logger.info(f"Successfully deleted VPN {vpn}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting VPN {vpn}: {str(e)}")
            return False

    def add_site_to_vpn(self, site: Site, vpn: VPN) -> bool:
        try:
            if vpn in site.vpns.all():
                self.logger.info(f"Site {site} is already apart of {vpn}")
                return True

            self.logger.info(f"Adding site {site} to VPN {vpn}")
            
            # Verify site has PE-CE routing configured
            if not site.assigned_interface or not site.vrf or not site.ospf_process_id:
                self.logger.error(f"Site {site} is not properly configured")
                return False

            # Generate the VPN route target
            vpn_route_target = f"{self.settings.bgp_as}:{vpn.id}"
            
            # Configure export route target for the VPN
            export_rt, created = RouteTarget.objects.update_or_create(
                vrf=site.vrf,
                value=vpn_route_target,
                target_type='export'
            )
            export_rt.save()
            
            # Configure import route target for the VPN
            import_rt, created = RouteTarget.objects.update_or_create(
                vrf=site.vrf,
                value=vpn_route_target,
                target_type='import'
            )
            import_rt.save()

            # Update VRF configuration on router using NetworkController
            if not NetworkController.create_or_update_vrf(site.vrf):
                self.logger.error(f"Failed to update VRF configuration for site {site}")
                return False

            # Update database
            vpn.sites.add(site)
            vpn.save()

            self.logger.info(f"Successfully added site {site} to VPN {vpn}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding site {site} to VPN {vpn}: {str(e)}")
            return False

    def remove_site_from_vpn(self, site: Site, vpn: VPN) -> bool:
        try:
            self.logger.info(f"Removing site {site} from VPN {vpn}")
            
            # Verify site is in the VPN
            if site not in vpn.sites.all():
                self.logger.warning(f"Site {site} is not in VPN {vpn}")
                return False
            
            # Generate the VPN route target
            vpn_route_target = f"{self.settings.bgp_as}:{vpn.id}"
            
            # Remove export and import route targets for the VPN
            RouteTarget.objects.filter(
                vrf=site.vrf,
                value=vpn_route_target
            ).delete()
            
            # Update VRF configuration on router using NetworkController
            if not NetworkController.create_or_update_vrf(site.vrf):
                self.logger.error(f"Failed to update VRF configuration for site {site}")
                return False
            
            # Update database
            vpn.sites.remove(site)
            vpn.save()
            
            self.logger.info(f"Successfully removed site {site} from VPN {vpn}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing site {site} from VPN {vpn}: {str(e)}")
            return False

ServiceController = _ServiceController()
ServiceController.initialize()
