import ipaddress
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

from core.settings import Settings

class DHCPLease(models.Model):
    mac_address = models.CharField(max_length=17, primary_key=True, help_text="MAC address of the client")
    ip_address = models.GenericIPAddressField(help_text="Assigned IP address")
    hostname = models.CharField(max_length=255, blank=True, default="Unknown", help_text="Client hostname")
    expiry_time = models.DateTimeField(help_text="When this lease expires")
    last_updated = models.DateTimeField(auto_now=True, help_text="When this lease was last updated")
    
    class Meta:
        verbose_name = "DHCP Lease"
        verbose_name_plural = "DHCP Leases"
        ordering = ["ip_address"]
    
    def __str__(self):
        return f"{self.mac_address} - {self.ip_address} ({self.hostname})"
    
    @property
    def is_active(self):
        return self.expiry_time > timezone.now()
    
    @property
    def remaining_time(self):
        if not self.is_active:
            return 0
        delta = self.expiry_time - timezone.now()
        return delta.total_seconds()

class Router(models.Model):
    ROLE_CHOICES = [
        ('CE', 'Customer Edge'),
        ('PE', 'Provider Edge'),
        ('P', 'Provider Core'),
    ]
    
    chassis_id = models.CharField(max_length=50, primary_key=True, help_text="Router chassis ID (MAC address)")
    management_ip_address = models.GenericIPAddressField(help_text="Router management IP address")
    hostname = models.CharField(max_length=255, default="Unknown", help_text="Router hostname")
    role = models.CharField(max_length=2, choices=ROLE_CHOICES, default='P', help_text="Router role in the network")
    last_discovered = models.DateTimeField(auto_now=True, help_text="When this router was last discovered")

    class Meta:
        verbose_name = "Router"
        verbose_name_plural = "Routers"
        ordering = ["hostname"]
    
    def __str__(self):
        return f"{self.hostname} ({self.management_ip_address})"

class Customer(models.Model):
    name = models.CharField(max_length=255, unique=True, help_text="Customer name")
    description = models.TextField(blank=True, help_text="Customer description")
    email = models.EmailField(blank=True, help_text="Customer email")
    phone_number = models.CharField(max_length=20, blank=True, help_text="Customer phone number")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class VPN(models.Model):
    name = models.CharField(max_length=255, unique=True, help_text="VPN name")
    customer = models.ForeignKey('Customer', null=True, blank=True, on_delete=models.SET_NULL, related_name='vpns', help_text="Customer who owns this VPN, if applicable")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "VPN"
        verbose_name_plural = "VPNs"
        ordering = ["name"]
    
    def __str__(self):
        if self.customer:
            return f"{self.name} ({self.customer.name})"
        return self.name
    
    def validate_route_targets(self):
        vpn_vrfs = self.vrfs.all()
        
        # If there's only one VRF, no validation needed
        if vpn_vrfs.count() <= 1:
            return True
            
        # For VPNs with multiple VRFs, perform validation
        for vrf in vpn_vrfs:
            # Get all export RTs from other VRFs in this VPN
            other_vrfs = vpn_vrfs.exclude(pk=vrf.pk)
            required_imports = set()
            
            for other_vrf in other_vrfs:
                # Add all export RTs from other VRFs to required imports
                export_rts = set(other_vrf.export_targets)
                required_imports.update(export_rts)
            
            # Get current import RTs for this VRF
            current_imports = set(vrf.import_targets)
            
            # Check if any required RTs are missing
            missing_rts = required_imports - current_imports
            
            if missing_rts:
                missing_list = ", ".join(missing_rts)
                raise ValidationError(f"VRF '{vrf.name}' is missing required import route targets: {missing_list}")
        
        return True

    def save(self, *args, **kwargs):
        if self.pk:
            self.validate_route_targets()
        super().save(*args, **kwargs)

class VRF(models.Model):
    name = models.CharField(max_length=255, help_text="VRF name")
    route_distinguisher = models.CharField(max_length=50, blank=True, help_text="Route distinguisher")
    router = models.ForeignKey(Router, on_delete=models.CASCADE, related_name='vrfs', help_text="Router where this VRF is configured")
    vpn = models.ForeignKey('VPN', null=True, blank=True, on_delete=models.SET_NULL, related_name='vrfs', help_text="VPN this VRF belongs to")
    
    class Meta:
        unique_together = [['name', 'router'], ['route_distinguisher', 'router']]
    
    def __str__(self):
        return f"{self.name} (RD: {self.route_distinguisher}) on {self.router.hostname}"
    
    @property
    def import_targets(self):
        return self.route_targets.filter(target_type='import').values_list('value', flat=True)
    
    @property
    def export_targets(self):
        return self.route_targets.filter(target_type='export').values_list('value', flat=True)

class RouteTarget(models.Model):
    TARGET_TYPE_CHOICES = [
        ('import', 'Import'),
        ('export', 'Export')
    ]
    
    vrf = models.ForeignKey(VRF, on_delete=models.CASCADE, related_name='route_targets')
    value = models.CharField(max_length=50, help_text="Route target value (ASN:nn format)")
    target_type = models.CharField(max_length=6, choices=TARGET_TYPE_CHOICES, help_text="Import or export target")
    
    class Meta:
        unique_together = [['vrf', 'value', 'target_type']]
    
    def __str__(self):
        return f"{self.value} ({self.target_type})"

class Site(models.Model):
    name = models.CharField(max_length=255, help_text="Site name")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='sites')
    description = models.TextField(blank=True, help_text="Site description")
    location = models.CharField(max_length=255, blank=True, help_text="Site location")
    management_network = models.GenericIPAddressField(protocol='IPv4', help_text="Management network IP (/30 subnet derived from DHCP sites network)")
    router = models.ForeignKey(Router, null=True, blank=True, on_delete=models.CASCADE,  related_name='sites', help_text="Customer Edge router for this site")
    
    class Meta:
        unique_together = [['customer', 'name']]
    
    def __str__(self):
        return f"{self.customer.name} - {self.name}"
    
    def save(self, *args, **kwargs):
        # Validate router role is CE
        if self.router and self.router.role != 'CE':
            raise ValidationError(f"Router '{self.router.hostname}' must have a Customer Edge (CE) role for site assignment")
        
        # Validate management network
        self.validate_management_network()
        
        super().save(args, **kwargs)

    def validate_management_network(self):
        if not self.management_network:
            return
            
        try:
            # Get global settings
            settings = Settings.get_settings()
            
            # Parse the DHCP sites network from settings
            dhcp_sites_network = ipaddress.IPv4Network(
                f"{settings.dhcp_sites_network_ip}/{settings.dhcp_sites_network_subnet_mask}", 
                strict=False
            )
            
            # Create a /30 network from the management IP
            management_ip = ipaddress.IPv4Address(self.management_network)
            management_network = ipaddress.IPv4Network(f"{management_ip}/30", strict=False)
            
            # Check if the /30 is a valid subnet of the DHCP sites network
            if not management_network.subnet_of(dhcp_sites_network):
                raise ValidationError(f"Management network {management_network} must be a subnet of the DHCP sites network {dhcp_sites_network}")
            
            # Check if this /30 is already used by another site
            if Site.objects.exclude(pk=self.pk).exists():
                # Get all other sites' management networks
                other_sites = Site.objects.exclude(pk=self.pk)
                for site in other_sites:
                    other_management_ip = ipaddress.IPv4Address(site.management_network)
                    other_management_network = ipaddress.IPv4Network(f"{other_management_ip}/30", strict=False)
                    
                    if management_network == other_management_network:
                        raise ValidationError(f"Management network {management_network} is already used by site '{site.name}'")
            
            # Ensure the network is properly aligned for a /30 (must start at a multiple of 4)
            network_int = int(management_ip)
            if network_int % 4 != 0:
                correct_start = network_int - (network_int % 4)
                correct_ip = str(ipaddress.IPv4Address(correct_start))
                raise ValidationError(f"Management network must be properly aligned for a /30 subnet. Use {correct_ip} instead.")
                
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid management network: {str(e)}")

class Interface(models.Model):
    router = models.ForeignKey(Router, on_delete=models.CASCADE, related_name='interfaces')
    name = models.CharField(max_length=100, help_text="Interface name")
    admin_status = models.CharField(max_length=20, default="down", help_text="Administrative status")
    oper_status = models.CharField(max_length=20, default="down", help_text="Operational status")
    description = models.CharField(max_length=255, blank=True, help_text="Interface description")
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="IP address if configured")
    subnet_mask = models.GenericIPAddressField(null=True, blank=True, help_text="Subnet mask if configured")
    mac_address = models.CharField(max_length=17, blank=True, help_text="Interface MAC address")
    vrf = models.ForeignKey(VRF, null=True, blank=True, on_delete=models.SET_NULL, related_name='interfaces')
    site = models.ForeignKey(Site, null=True, blank=True, on_delete=models.SET_NULL, related_name='interfaces')
    connected_interfaces = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='connected_from')
    
    class Meta:
        unique_together = [['router', 'name']]
    
    def __str__(self):
        return f"{self.router.hostname} - {self.name}"

    def save(self, *args, **kwargs):
        if self.vrf and self.vrf.router != self.router:
            raise ValidationError(f"VRF '{self.vrf}' does not exist on router '{self.router.hostname}'")
        super().save(*args, **kwargs)
    
    @property
    def is_connected(self):
        return self.connected_interfaces.exists() or self.connected_from.exists()
