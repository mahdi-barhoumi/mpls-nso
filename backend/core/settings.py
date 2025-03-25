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
    
    # DHCP settings
    dhcp_ip_range_start = models.GenericIPAddressField(protocol='IPv4')
    dhcp_ip_range_end = models.GenericIPAddressField(protocol='IPv4')
    dhcp_lease_time = models.PositiveIntegerField(
        validators=[MinValueValidator(86400)],
        help_text='DHCP lease time in seconds'
    )
    dhcp_sites_network_ip = models.GenericIPAddressField(
        protocol='IPv4',
        help_text='IP address for the DHCP sites network'
    )
    dhcp_sites_network_subnet_mask = models.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^(255\.(0|128|192|224|240|248|252|254|255)\.){2}(0|128|192|224|240|248|252|254|255)$|^255\.255\.255\.(0|128|192|224|240|248|252|254)$',
                message='Enter a valid subnet mask',
            )
        ],
        help_text='Subnet mask for the DHCP sites network'
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
        self.validate_dhcp_range()
        self.validate_dhcp_range_size()
        self.validate_host_ip_not_in_dhcp()
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
        valid_indices = [interface['index'] for interface in interfaces]
        
        if self.host_interface_id not in valid_indices:
            raise ValidationError(f'Interface index {self.host_interface_id} does not exist. Valid indices: {sorted(valid_indices)}')
    
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
    
    def validate_dhcp_range_size(self):
        try:
            # Convert range start and end to integer representation
            start_ip = int(ipaddress.IPv4Address(self.dhcp_ip_range_start))
            end_ip = int(ipaddress.IPv4Address(self.dhcp_ip_range_end))
            
            # Calculate the number of IPs in the range (inclusive)
            ip_count = end_ip - start_ip + 1
            
            # Check if range has at least 100 IPs
            if ip_count < 100:
                raise ValidationError(f'DHCP range must include at least 100 IPs. Current range has {ip_count} IPs.')
                
        except (ValueError, TypeError) as e:
            raise ValidationError(f'DHCP range size validation error: {str(e)}')
    
    def validate_host_ip_not_in_dhcp(self):
        try:
            # Convert all IPs to IPv4Address objects for comparison
            host_ip = ipaddress.IPv4Address(self.host_ip)
            start_ip = ipaddress.IPv4Address(self.dhcp_ip_range_start)
            end_ip = ipaddress.IPv4Address(self.dhcp_ip_range_end)
            
            # Check if host IP is within DHCP range
            if start_ip <= host_ip <= end_ip:
                raise ValidationError('Host IP cannot be within the DHCP IP range')
                
        except (ValueError, TypeError) as e:
            raise ValidationError(f'IP validation error: {str(e)}')
    
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
            host_network = ipaddress.IPv4Network(
                f"{self.host_ip}/{self.host_subnet_mask}", 
                strict=False
            )
            
            # Calculate DHCP sites network
            dhcp_sites_network = ipaddress.IPv4Network(
                f"{self.dhcp_sites_network_ip}/{self.dhcp_sites_network_subnet_mask}", 
                strict=False
            )
            
            # Check for overlap
            if host_network.overlaps(dhcp_sites_network):
                raise ValidationError('DHCP sites network must not overlap with the host network')
                
        except (ValueError, TypeError) as e:
            raise ValidationError(f'Network validation error: {str(e)}')
    
    def apply_network_configuration(self):
        if not self.host_interface_id:
            return False

        try:
            # Configure the interface
            success = HostNetworkManager.configure_interface(
                interface=self.host_interface_id,
                address=self.host_ip,
                subnet_mask=self.host_subnet_mask
            )
            
            if success:
                self.logger.info(f"Network configuration applied to interface {self.host_interface_id}: {self.host_ip}/{self.host_subnet_mask}")
            else:
                self.logger.error(f"Failed to apply network configuration to interface {self.host_interface_id}")
            
            return success
            
        except Exception as exception:
            self.logger.error(f"Network configuration error: {str(exception)}")
            return False
    
    @classmethod
    def get_settings(cls):
        # Check if settings exist
        if not cls.objects.exists():
            raise ValidationError('Settings have not been configured yet')
            
        # Return the settings
        return cls.objects.first()
