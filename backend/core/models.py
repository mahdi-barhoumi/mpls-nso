from django.db import models
from django.utils import timezone

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

class VRF(models.Model):
    name = models.CharField(max_length=255, help_text="VRF name")
    route_distinguisher = models.CharField(max_length=50, blank=True, help_text="Route distinguisher")
    customer = models.ForeignKey(Customer, null=True, on_delete=models.CASCADE, related_name='vrfs')
    
    class Meta:
        unique_together = [['name', 'route_distinguisher']]
    
    def __str__(self):
        return f"{self.name} (RD: {self.route_distinguisher})"
    
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
    
    @property
    def is_connected(self):
        return self.connected_interfaces.exists() or self.connected_from.exists()
