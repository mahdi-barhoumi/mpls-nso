import re
import logging
import ipaddress
import subprocess
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator

class Settings(models.Model):
    # RESTCONF credentials
    restconf_username = models.CharField(max_length=50)
    restconf_password = models.CharField(max_length=100)
    
    # Host network settings - using interface index instead of name
    host_interface_id = models.PositiveIntegerField(
        null=True,
        validators=[MinValueValidator(1)],
        help_text='Network interface index'
    )
    host_ip = models.GenericIPAddressField(protocol='IPv4')
    host_subnet_mask = models.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^(255\.(0|128|192|224|240|248|252|254|255)\.){2}(0|128|192|224|240|248|252|254|255)$|^255\.255\.255\.(0|128|192|224|240|248|252|254)$',
                message='Enter a valid subnet mask',
            )
        ]
    )
    
    # BGP settings
    bgp_as = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(4294967295)  # Max AS number in BGP
        ],
        help_text='BGP Autonomous System number'
    )
    
    # DHCP settings
    dhcp_ip_range_start = models.GenericIPAddressField(protocol='IPv4')
    dhcp_ip_range_end = models.GenericIPAddressField(protocol='IPv4')
    dhcp_lease_time = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text='DHCP lease time in seconds'
    )
    
    # Management VRF
    management_vrf = models.CharField(max_length=100)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Settings'
        verbose_name_plural = 'Settings'
    
    def __str__(self):
        return f"Settings (last updated: {self.updated_at})"
    
    def save(self, *args, **kwargs):
        # Check if this is an update or a new instance
        is_update = self.pk is not None
        
        # If it's an update, get the original instance to detect changes
        if is_update:
            original = Settings.objects.get(pk=self.pk)
            ip_changed = original.host_ip != self.host_ip
            mask_changed = original.host_subnet_mask != self.host_subnet_mask
            interface_changed = original.host_interface_id != self.host_interface_id
        else:
            # For new instances, we'll consider these as changes
            ip_changed = mask_changed = interface_changed = True
        
        # Before saving, perform validations
        if Settings.objects.exists() and not self.pk:
            raise ValidationError('There can only be one Settings instance')
        
        # Validate interface index
        self.validate_interface_id()
        
        # Validate that DHCP range is within subnet
        self.validate_dhcp_range()
        
        # Save the model first
        super().save(*args, **kwargs)
        
        # After saving, if IP or subnet mask changed and interface is set, apply to the network interface
        network_changes = ip_changed or mask_changed or interface_changed
        if self.host_interface_id and is_update and network_changes:
            self.apply_network_configuration()
    
    def validate_interface_id(self):
        # Skip validation if host_interface_id is None
        if not self.host_interface_id:
            return
            
        try:
            # Run netsh command to get interfaces
            result = subprocess.run(
                ['netsh', 'interface', 'ipv4', 'show', 'interfaces'],
                capture_output=True, 
                text=True,
                check=True
            )
            
            # Parse the output to find interface indices
            output = result.stdout
            pattern = r'^\s*(\d+)\s+\d+\s+\d+\s+\w+\s+'
            valid_indices = set()
            
            for line in output.splitlines():
                match = re.match(pattern, line)
                if match:
                    valid_indices.add(int(match.group(1)))
            
            # Check if our index is valid
            if self.host_interface_id not in valid_indices:
                raise ValidationError(f'Interface index {self.host_interface_id} does not exist, Valid indices: {sorted(valid_indices)}')
                
        except subprocess.SubprocessError as e:
            raise ValidationError(f'Failed to validate interface: {str(e)}')
    
    def validate_dhcp_range(self):
        try:
            # Calculate the network from host IP and subnet mask
            ip_interface = ipaddress.IPv4Interface(f"{self.host_ip}/{self.host_subnet_mask}")
            network = ip_interface.network
            
            # Check if DHCP range is within network
            start_ip = ipaddress.IPv4Address(self.dhcp_ip_range_start)
            end_ip = ipaddress.IPv4Address(self.dhcp_ip_range_end)
            
            if start_ip not in network or end_ip not in network:
                raise ValidationError('DHCP IP range must be within the host subnet')
            
            if start_ip > end_ip:
                raise ValidationError('DHCP start IP must be less than or equal to end IP')
                
        except (ValueError, TypeError) as e:
            raise ValidationError(f'IP validation error: {str(e)}')
    
    def apply_network_configuration(self):
        if not self.host_interface_id:
            return False
            
        try:
            # Format the command
            cmd = [
                'netsh', 'interface', 'ipv4', 'set', 'address',
                f'name={self.host_interface_id}',
                'static',
                self.host_ip,
                self.host_subnet_mask
            ]
            
            # Execute the command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Log the result
            logger = logging.getLogger(__name__)
            logger.info(f"Network configuration applied to interface {self.host_interface_id}: {self.host_ip}/{self.host_subnet_mask}")
            
            return True
            
        except subprocess.SubprocessError as e:
            # Log the error
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to apply network configuration: {str(e)}")
            if hasattr(e, 'stderr'):
                logger.error(f"Command stderr: {e.stderr}")
            
            # We don't raise an exception here because the model has already been saved
            # But you might want to add a way to notify the user or admin
            return False
    
    @classmethod
    def get_settings(cls):
        settings, created = cls.objects.get_or_create(
            defaults={
                'restconf_username': 'mgmt',
                'restconf_password': 'mgmtapp',
                'host_ip': '192.168.100.1',
                'host_subnet_mask': '255.255.255.0',
                'bgp_as': 1,  # Provider iBGP AS number
                'dhcp_ip_range_start': '192.168.100.100',
                'dhcp_ip_range_end': '192.168.100.200',
                'dhcp_lease_time': 86400,  # 24 hours in seconds
                'management_vrf': 'management'
            }
        )
        
        # If settings were just created and interface is set, apply network configuration
        if created and settings.host_interface_id:
            settings.apply_network_configuration()
            
        return settings

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
        ('PE', 'Provider Edge'),
        ('P', 'Provider Core'),
        ('CE', 'Customer Edge'),
    ]
    
    chassis_id = models.CharField(max_length=50, primary_key=True, help_text="Router chassis ID (MAC address)")
    management_ip_address = models.GenericIPAddressField(help_text="Router management IP address")
    hostname = models.CharField(max_length=255, default="UnassignedRouter", help_text="Router hostname")
    last_discovered = models.DateTimeField(auto_now=True, help_text="When this router was last discovered")
    role = models.CharField(max_length=2, choices=ROLE_CHOICES, default='P', help_text="Router role in the network")
    
    class Meta:
        verbose_name = "Router"
        verbose_name_plural = "Routers"
        ordering = ["hostname"]
    
    def __str__(self):
        return f"{self.hostname} ({self.management_ip_address})"

class Customer(models.Model):
    name = models.CharField(max_length=255, unique=True, help_text="Customer name")
    description = models.TextField(blank=True, help_text="Customer description")
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
                raise ValidationError(
                    f"VRF '{vrf.name}' is missing required import route targets: {missing_list}"
                )
        
        return True

    def clean(*args, **kwargs):
        if self.pk:
            self.validate_route_targets()
        super().save(*args, **kwargs)

class VRF(models.Model):
    name = models.CharField(max_length=255, help_text="VRF name")
    route_distinguisher = models.CharField(max_length=50, blank=True, help_text="Route distinguisher")
    customer = models.ForeignKey(Customer, null=True, on_delete=models.CASCADE, related_name='vrfs')
    router = models.ForeignKey(Router, on_delete=models.CASCADE, related_name='vrfs', help_text="Router where this VRF is configured")
    vpn = models.ForeignKey('VPN', null=True, blank=True, on_delete=models.SET_NULL, related_name='vrfs',
                          help_text="VPN this VRF belongs to")
    
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
    
    def __str__(self):
        return f"{self.customer.name} - {self.name}"

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
            raise ValidationError({
                'vrf': f"VRF '{self.vrf}' does not exist on router '{self.router.hostname}'"
            })
        super().save(*args, **kwargs)
    
    @property
    def is_connected(self):
        return self.connected_interfaces.exists() or self.connected_from.exists()
