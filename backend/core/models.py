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
    chassis_id = models.CharField(max_length=50, primary_key=True, help_text="Router chassis ID (MAC address)")
    ip_address = models.GenericIPAddressField(help_text="Router IP address")
    hostname = models.CharField(max_length=255, default="UnassignedRouter", help_text="Router hostname")
    last_discovered = models.DateTimeField(auto_now=True, help_text="When this router was last discovered")
    
    class Meta:
        verbose_name = "Router"
        verbose_name_plural = "Routers"
        ordering = ["hostname"]
    
    def __str__(self):
        return f"{self.hostname} ({self.ip_address})"
    
    def get_connections(self):
        return self.connections.all()

class RouterConnection(models.Model):
    router = models.ForeignKey(Router, on_delete=models.CASCADE, related_name='connections')
    remote_chassis_id = models.CharField(max_length=50, help_text="Remote router chassis ID")
    remote_system_name = models.CharField(max_length=255, blank=True, help_text="Remote router system name")
    local_interface = models.CharField(max_length=100, help_text="Local interface name")
    remote_interface = models.CharField(max_length=100, help_text="Remote interface name")
    
    class Meta:
        unique_together = [['router', 'remote_chassis_id', 'local_interface']]
    
    def __str__(self):
        return f"{self.router.hostname} ({self.local_interface}) -> {self.remote_chassis_id} ({self.remote_interface})"
