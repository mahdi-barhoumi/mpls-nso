import re
import logging
import ipaddress
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from core.modules.utils.host_network_manager import HostNetworkManager

class Settings(models.Model):
    # Logger definition
    logger = logging.getLogger('settings')

    # RESTCONF credentials
    restconf_username = models.CharField(max_length=50)
    restconf_password = models.CharField(max_length=100)
    
    # Host network settings
    host_interface_id = models.PositiveIntegerField(help_text='Network interface index')
    host_address = models.GenericIPAddressField(protocol='IPv4')
    host_subnet_mask = models.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^(255\.(0|128|192|224|240|248|252|254|255)\.){2}(0|128|192|224|240|248|252|254|255)$|^255\.255\.255\.(0|128|192|224|240|248|252|254)$',
                message='Invalid subnet mask',
            )
        ]
    )
    
    # DHCP settings
    dhcp_provider_network_address = models.GenericIPAddressField(protocol='IPv4')
    dhcp_provider_network_subnet_mask = models.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^(255\.(0|128|192|224|240|248|252|254|255)\.){2}(0|128|192|224|240|248|252|254|255)$|^255\.255\.255\.(0|128|192|224|240|248|252|254)$',
                message='Invalid subnet mask',
            )
        ]
    )
    dhcp_sites_network_address = models.GenericIPAddressField(protocol='IPv4')
    dhcp_sites_network_subnet_mask = models.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^(255\.(0|128|192|224|240|248|252|254|255)\.){2}(0|128|192|224|240|248|252|254|255)$|^255\.255\.255\.(0|128|192|224|240|248|252|254)$',
                message='Invalid subnet mask',
            )
        ],
    )
    
    # Management settings
    management_vrf = models.CharField(max_length=100)
    bgp_as = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(4294967295)  # Max AS number in BGP
        ],
        help_text='BGP Autonomous System number'
    )
    
    class Meta:
        verbose_name = 'Settings'
        verbose_name_plural = 'Settings'
    
    def __str__(self):
        return f"Settings"
    
    def save(self, *args, **kwargs):
        # If settings already exist, reject the save
        if Settings.objects.exists():
            raise ValidationError('Settings can only be set once and cannot be modified')
        
        # Perform all validations before saving
        self.validate_interface_id()
        self.validate_dhcp_sites_subnet_size()
        self.validate_network_overlap()
        
        # Attempt to apply network configuration before saving
        self.apply_network_configuration()
    
        # Save the model
        super().save(*args, **kwargs)

    def validate_interface_id(self):
        if not self.host_interface_id:
            return
        
        # Get list of interfaces
        interfaces = HostNetworkManager.list_interfaces()
        
        # Check if interface index exists
        valid_indices = [interface['id'] for interface in interfaces]
        
        if self.host_interface_id not in valid_indices:
            raise ValidationError(f'Interface index {self.host_interface_id} does not exist. Valid indices: {sorted(valid_indices)}')
    
    def validate_dhcp_sites_subnet_size(self):
        try:
            # Convert subnet mask to CIDR prefix length
            subnet_mask = ipaddress.IPv4Network(
                f"0.0.0.0/{self.dhcp_sites_network_subnet_mask}"
            ).prefixlen
            
            # Check if subnet is at least a /10
            if subnet_mask > 10:
                raise ValidationError(f'DHCP sites network subnet must be at least a /10. Current subnet is /{subnet_mask}')
                
        except (ValueError, TypeError) as e:
            raise ValidationError(f'DHCP sites subnet size validation error: {str(e)}')
    
    def validate_network_overlap(self):
        try:
            # Calculate host network
            dhcp_provider_network = ipaddress.IPv4Network(
                f"{self.dhcp_provider_network_address}/{self.dhcp_provider_network_subnet_mask}", 
                strict=False
            )
            
            # Calculate DHCP sites network
            dhcp_sites_network = ipaddress.IPv4Network(
                f"{self.dhcp_sites_network_address}/{self.dhcp_sites_network_subnet_mask}", 
                strict=False
            )
            
            # Check for overlap
            if dhcp_provider_network.overlaps(dhcp_sites_network):
                raise ValidationError('DHCP sites network must not overlap with the DHCP provider network')
                
        except (ValueError, TypeError) as e:
            raise ValidationError(f'Network validation error: {str(e)}')
    
    def apply_network_configuration(self):
        if not self.host_interface_id:
            return False

        try:
            # Configure the interface
            success = HostNetworkManager.configure_interface(
                interface=self.host_interface_id,
                address=self.host_address,
                subnet_mask=self.host_subnet_mask
            )
            
            if success:
                self.logger.info(f"Network configuration applied to interface {self.host_interface_id}: {self.host_address}/{self.host_subnet_mask}")
            else:
                self.logger.error(f"Failed to apply network configuration to interface {self.host_interface_id}")
            
            return success
            
        except Exception as exception:
            self.logger.error(f"Network configuration error: {str(exception)}")
            return False
    
def get_settings():
    try:
        return Settings.objects.first()
    except:
        return None
