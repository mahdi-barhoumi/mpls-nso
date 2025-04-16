import re
import ipaddress
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from core.settings import get_settings

class ImmutableFieldMixin:
    immutable_fields = []  # Define a list of immutable fields in your model
    
    def save(self, *args, **kwargs):
        if self.pk:  # If the object exists in the database
            original = self.__class__.objects.get(pk=self.pk)
            for field in self.immutable_fields:
                if getattr(original, field) != getattr(self, field):
                    raise ValueError(f"{field} is immutable.")
        super().save(*args, **kwargs)

class DefaultManager(models.Manager):
    def get_or_new(self, **kwargs):
        try:
            # Try to get an existing instance
            instance = self.get(**kwargs)
            return instance, False
        except self.model.DoesNotExist:
            # Create a new instance but don't save it
            instance = self.model(**kwargs)
            return instance, True

class DHCPLease(models.Model):
    mac_address = models.CharField(max_length=17, primary_key=True, help_text="MAC address of the client")
    ip_address = models.GenericIPAddressField(help_text="Assigned IP address")
    hostname = models.CharField(max_length=255, default="Unknown", help_text="Client hostname")
    expiry_time = models.DateTimeField(help_text="When this lease expires")
    last_updated = models.DateTimeField(auto_now=True, help_text="When this lease was last updated")
    
    class Meta:
        verbose_name = "DHCP Lease"
        verbose_name_plural = "DHCP Leases"
        ordering = ["ip_address"]
    
    def __str__(self):
        return f"{self.ip_address} - {self.mac_address} ({self.hostname})"
    
    @property
    def is_active(self):
        return self.expiry_time > timezone.now()
    
    @property
    def remaining_time(self):
        if not self.is_active:
            return 0
        delta = self.expiry_time - timezone.now()
        return delta.total_seconds()

class DHCPScope(models.Model):
    network = models.GenericIPAddressField(protocol='IPv4', help_text="Network address of the scope")
    subnet_mask = models.GenericIPAddressField(protocol='IPv4', help_text="Subnet mask of the scope")
    is_active = models.BooleanField(default=False, help_text="Scope status")
    
    class Meta:
        verbose_name = "DHCP Scope"
        verbose_name_plural = "DHCP Scopes"
        unique_together = ['network', 'subnet_mask']
        
    def __str__(self):
        return str(ipaddress.IPv4Network(f"{self.network}/{self.subnet_mask}", strict=False))
    
    def validate(self):
        try:
            # Get global settings
            settings = get_settings()
            
            # Parse the DHCP sites network from settings
            dhcp_sites_network = ipaddress.IPv4Network(
                f"{settings.dhcp_sites_network_address}/{settings.dhcp_sites_network_subnet_mask}", 
                strict=False
            )
            
            # Create a scope
            dhcp_scope = ipaddress.IPv4Network(
                f"{self.network}/{self.subnet_mask}", 
                strict=False
            )
            
            # Validate /30 subnet
            if dhcp_scope.prefixlen != 30:
                raise ValidationError(f"DHCP scope must be a /30 subnet. Current is /{dhcp_scope.prefixlen}")
            
            # Check if the /30 is a valid subnet of the DHCP sites network
            if not dhcp_scope.subnet_of(dhcp_sites_network):
                raise ValidationError(f"DHCP scope {dhcp_scope} must be a subnet of the DHCP sites network {dhcp_sites_network}")
            
            # Ensure the scope is properly aligned for a /30
            self.network = str(dhcp_scope.network_address)
                
        except (ValueError, TypeError) as exception:
            raise ValidationError(f"Invalid DHCP scope: {str(exception)}")

    def save(self, *args, **kwargs):
        self.validate()
        super().save(*args, **kwargs)

class Router(models.Model):
    role = models.CharField(max_length=2, choices=[('CE', 'Customer Edge'), ('PE', 'Provider Edge'), ('P', 'Provider Core')], help_text="Router role in the network")
    hostname = models.CharField(max_length=255, default="Unknown", help_text="Router hostname")
    chassis_id = models.CharField(max_length=50, help_text="Router chassis ID (MAC address)")
    management_ip_address = models.GenericIPAddressField(help_text="Router management IP address")
    first_discovered = models.DateTimeField(auto_now_add=True, help_text="When this router was first discovered")
    last_discovered = models.DateTimeField(auto_now=True, help_text="When this router was last discovered")
    reachable = models.BooleanField(default=False, help_text="Whether the router is currently reachable")

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
    created_at = models.DateTimeField(auto_now_add=True, help_text="When this customer was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="When this customer was updated")
    
    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"
        ordering = ["name"]

    def __str__(self):
        return self.name

class VRF(ImmutableFieldMixin, models.Model):
    objects = DefaultManager()
    immutable_fields = ['router', 'name', 'route_distinguisher']

    router = models.ForeignKey(Router, on_delete=models.CASCADE, related_name='vrfs', help_text="Router where this VRF is configured")
    name = models.CharField(max_length=255, help_text="VRF name")
    route_distinguisher = models.CharField(null=True, max_length=50, help_text="Route distinguisher")
    
    class Meta:
        unique_together = [['name', 'router'], ['route_distinguisher', 'router']]
    
    def __str__(self):
        return f"{self.name} (RD: {self.route_distinguisher}) on {self.router}"
    
    @property
    def import_targets(self):
        if self.pk:
            return self.route_targets.filter(target_type='import').values_list('value', flat=True)
        return None
    
    @property
    def export_targets(self):
        if self.pk:
            return self.route_targets.filter(target_type='export').values_list('value', flat=True)
        return None

class RouteTarget(models.Model):
    vrf = models.ForeignKey(VRF, on_delete=models.CASCADE, related_name='route_targets', help_text="VRF this route target belongs to")
    value = models.CharField(max_length=50, help_text="Route target value (ASN:nn format)")
    target_type = models.CharField(max_length=6, choices=[('import', 'Import route target'), ('export', 'Export route target')], help_text="Import or export target")
    
    class Meta:
        unique_together = [['vrf', 'value', 'target_type']]
    
    def __str__(self):
        return f"{self.value} ({self.target_type})"

class Interface(ImmutableFieldMixin, models.Model):
    objects = DefaultManager()
    immutable_fields = ['router', 'name', 'mac_address']

    router = models.ForeignKey(Router, on_delete=models.CASCADE, related_name='interfaces', help_text="Router this interface belongs to")
    name = models.CharField(max_length=100, help_text="Interface name")
    description = models.CharField(max_length=255, help_text="Interface description")
    enabled = models.BooleanField(help_text="Whether the interface is enabled or not")
    addressing = models.CharField(max_length=10, choices=[('static', 'Static'), ('dhcp', 'DHCP')], help_text="Addressing method")
    mac_address = models.CharField(max_length=17, default="00:00:00:00:00:00", help_text="Interface MAC address")
    ip_address = models.GenericIPAddressField(null=True, protocol='ipv4', help_text="IP address if configured")
    subnet_mask = models.GenericIPAddressField(null=True, protocol='ipv4', help_text="Subnet mask if configured")
    dhcp_helper_address = models.GenericIPAddressField(null=True, protocol='ipv4', help_text="DHCP helper address if applicable")
    vlan = models.PositiveIntegerField(null=True, validators=[MinValueValidator(1), MaxValueValidator(4094)], help_text="VLAN if applicable")
    vrf = models.ForeignKey(VRF, null=True, on_delete=models.SET_NULL, related_name='interfaces')
    connected_interfaces = models.ManyToManyField('self', symmetrical=False, related_name='connected_from')
    first_discovered = models.DateTimeField(auto_now_add=True, help_text="When this interface was first discovered")
    last_discovered = models.DateTimeField(auto_now=True, help_text="When this interface was last discovered")
    
    class Meta:
        unique_together = [['router', 'name']]
    
    def __str__(self):
        return f"{self.router} - {self.name}"

    def validate(self):
        if self.pk:
            current = Interface.objects.get(pk=self.pk)
            if self.addressing == 'dhcp' and current.addressing == 'static':
                self.ip_address = self.subnet_mask = None

        if self.vrf and self.vrf.router != self.router:
            raise ValidationError(f"VRF '{self.vrf}' does not exist on router")

    def save(self, *args, **kwargs):
        self.validate()
        super().save(*args, **kwargs)
    
    @property
    def type(self):
        match = re.match(r'([a-zA-Z-]+)', self.name)
        if match:
            return match.group(1)
        return None

    @property
    def index(self):
        match = re.match(r'[a-zA-Z-]+(.+)$', self.name)
        if match:
            return match.group(1)
        return None

    @property
    def category(self):
        if '.' in self.name:
            return 'logical'
        if 'loopback' in self.name.lower():
            return 'loopback'
        return 'physical'

    @property
    def is_connected(self):
        return self.connected_interfaces.exists() or self.connected_from.exists()
    
    @property
    def is_management_interface(self):
        return self.ip_address == self.router.management_ip_address

class Site(models.Model):
    name = models.CharField(max_length=255, help_text="Site name")
    description = models.TextField(max_length=255, null=True, blank=True, help_text="Site description")
    location = models.CharField(max_length=255, null=True, blank=True, help_text="Site location")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='sites', help_text="Customer this site belongs to")
    dhcp_scope = models.OneToOneField(DHCPScope, null=True, on_delete=models.SET_NULL, help_text="DHCP scope for customer edge management (/30 subnet)")
    link_network = models.GenericIPAddressField(protocol='IPv4', help_text="P2P link network (/30 subnet) for site connectivity")
    assigned_interface = models.ForeignKey(Interface, null=True, on_delete=models.SET_NULL, related_name='site', help_text="Assigned provider interface for this site")
    vrf = models.ForeignKey(VRF, null=True, on_delete=models.SET_NULL, related_name='sites', help_text="VRF for this site")
    ospf_process_id = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(65535)], help_text="OSPF process ID used by the PE router for this site's routing")
    router = models.ForeignKey(Router, null=True, on_delete=models.SET_NULL, related_name='sites', help_text="Customer edge router for this site")

    class Meta:
        unique_together = [['customer', 'name']]
    
    def __str__(self):
        return f"{self.customer.name} - {self.name}"
    
    def validate(self):
        # Validate if the assigned interface belongs to a PE router
        if self.assigned_interface and self.assigned_interface.router.role != 'PE':
            raise ValidationError("Assigned interface must belong to a PE router")

        # Check if DHCP scope is already used by another site
        if self.dhcp_scope:
            existing_sites = Site.objects.filter(dhcp_scope=self.dhcp_scope).exclude(pk=self.pk)
            if existing_sites.exists():
                conflicting_site = existing_sites.first()
                raise ValidationError(f"DHCP scope is already in use by site '{conflicting_site}' for customer '{conflicting_site.customer.name}'")
        
        # Validate router role is CE
        if self.router and self.router.role != 'CE':
            raise ValidationError(f"Router '{self.router.hostname}' must have a CE role for site assignment")
        
        # Validate link_network is not used by another site from the same customer
        existing_sites = Site.objects.filter(
            customer=self.customer,
            link_network=self.link_network
        ).exclude(pk=self.pk)
        
        if existing_sites.exists():
            conflicting_site = existing_sites.first()
            raise ValidationError(f"Link network is already in use by site '{conflicting_site.name}' for the same customer")
    
    def find_available_link_network(self):
        # Start with the 192.168.0.0/16 network
        base_network = ipaddress.ip_network('192.168.0.0/16')
        
        # Get all /30 subnets from the base network
        all_possible_subnets = list(base_network.subnets(new_prefix=30))
        
        # Get all currently used link networks for the same customer
        used_networks = Site.objects.filter(customer=self.customer).exclude(pk=self.pk).values_list('link_network', flat=True)
        used_networks = [ipaddress.ip_network(f"{ip}/30") for ip in used_networks if ip]
        
        # Find the first available subnet
        for subnet in all_possible_subnets:
            if subnet not in used_networks:
                return str(subnet.network_address)
        
        # If no subnet is available, raise an exception
        raise ValidationError("No available /30 subnet in 192.168.0.0/16 range for this customer")
    
    def save(self, *args, **kwargs):
        # If this is a new Site
        if not self.pk:
            self.link_network = self.find_available_link_network()
        
        # Validate before saving
        self.validate()
        super().save(*args, **kwargs)

class VPN(models.Model):
    name = models.CharField(max_length=255, help_text="VPN name")
    description = models.TextField(max_length=255, null=True, blank=True, help_text="VPN description")
    customer = models.ForeignKey(Customer, null=True, on_delete=models.CASCADE, related_name='vpns', help_text="Customer who owns this VPN, if applicable")
    sites = models.ManyToManyField(Site, related_name='vpns', help_text="VPNs this VRF belongs to")
    discovered = models.BooleanField(default=False, help_text="If the VPN was discovered or created")
    created_at = models.DateTimeField(auto_now_add=True, help_text="When this VPN was created or discovered")
    updated_at = models.DateTimeField(auto_now=True, help_text="When this VPN was last updated")
    
    class Meta:
        verbose_name = "VPN"
        verbose_name_plural = "VPNs"
        ordering = ["name"]
        unique_together = [['name', 'customer']]
    
    def __str__(self):
        if self.customer:
            return f"{self.name} belonging to {self.customer.name}"
        return self.name
    
    def validate(self):
        # Get settings first
        settings = get_settings()
        if not settings:
            raise ValidationError("Settings must be set first before validating VPNs")

        # Collect all sites in this VPN
        vpn_sites = self.sites.all()
        
        # If there's only one site, no validation needed
        if vpn_sites.count() <= 1:
            return True
        
        # Generate the expected route target for this VPN
        vpn_route_target = f"{settings.bgp_as}:{self.id}"
        
        # Validate that each site's VRF exports and imports the VPN route target
        for site in vpn_sites:
            if not site.vrf:
                raise ValidationError(f"Site '{site.name}' has no VRF assigned and cannot participate in VPN '{self.name}'")
            
            # Check if the VRF exports the VPN route target
            export_targets = set(site.vrf.export_targets)
            if vpn_route_target not in export_targets:
                raise ValidationError(f"VRF '{site.vrf.name}' on site '{site.name}' must export VPN route target '{vpn_route_target}'")
            
            # Check if the VRF imports the VPN route target
            import_targets = set(site.vrf.import_targets)
            if vpn_route_target not in import_targets:
                raise ValidationError(f"VRF '{site.vrf.name}' on site '{site.name}' must import VPN route target '{vpn_route_target}'")
        
        return True

    def save(self, *args, **kwargs):
        if self.pk:
            self.validate()
        super().save(*args, **kwargs)
