import re
import logging
import ipaddress
import subprocess
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator

class Settings(models.Model):
    # Logger definition
    logger = logging.getLogger('settings')

    # RESTCONF credentials
    restconf_username = models.CharField(max_length=50)
    restconf_password = models.CharField(max_length=100)
    
    # Host network settings
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
    
    # DHCP sites network settings
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
        validators=[MinValueValidator(86400)],
        help_text='DHCP lease time in seconds'
    )
    
    # Management VRF
    management_vrf = models.CharField(max_length=100)
    
    class Meta:
        verbose_name = 'Settings'
        verbose_name_plural = 'Settings'
    
    def __str__(self):
        return f"Settings"
    
    def save(self, *args, **kwargs):
        # Check if this is an update or a new instance
        is_update = self.pk is not None
        
        # If it's an update, reject the save operation
        if is_update:
            raise ValidationError('Settings can only be set once and cannot be modified')
        
        # Before saving, perform validations
        if Settings.objects.exists():
            raise ValidationError('There can only be one Settings instance')
        
        # Validate interface index
        self.validate_interface_id()
        
        # Validate that DHCP range is within subnet
        self.validate_dhcp_range()
        
        # Validate that DHCP range has at least 100 IPs
        self.validate_dhcp_range_size()
        
        # Validate that host IP is not in DHCP range
        self.validate_host_ip_not_in_dhcp()
        
        # Validate DHCP sites network subnet size
        self.validate_dhcp_sites_subnet_size()
        
        # Validate that DHCP sites network doesn't overlap with host network
        self.validate_network_overlap()
        
        # Save the model
        super().save(*args, **kwargs)
        
        # After saving, if interface is set, apply to the network interface
        if self.host_interface_id:
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
            self.logger.info(f"Network configuration applied to interface {self.host_interface_id}: {self.host_ip}/{self.host_subnet_mask}")
            
            return True
            
        except subprocess.SubprocessError as e:
            # Log the error
            self.logger.error(f"Failed to apply network configuration: {str(e)}")
            if hasattr(e, 'stderr'):
                self.logger.error(f"Command stderr: {e.stderr}")
            
            # We don't raise an exception here because the model has already been saved
            # But you might want to add a way to notify the user or admin
            return False
    
    @classmethod
    def get_settings(cls):
        # Check if settings exist
        if not cls.objects.exists():
            raise ValidationError('Settings have not been configured yet')
            
        # Return the settings
        return cls.objects.first()
