import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError

from core.settings import Settings

@csrf_exempt
@require_http_methods(["GET", "POST"])
def global_settings(request):
    if request.method == "GET":
        try:
            # Check if settings exist first
            try:
                settings = Settings.get_settings()
                
                # Convert settings to a dictionary
                settings_dict = {
                    'restconf_username': settings.restconf_username,
                    'restconf_password': settings.restconf_password,
                    'host_interface_id': settings.host_interface_id,
                    'host_ip': settings.host_ip,
                    'host_subnet_mask': settings.host_subnet_mask,
                    'dhcp_sites_network_ip': settings.dhcp_sites_network_ip,
                    'dhcp_sites_network_subnet_mask': settings.dhcp_sites_network_subnet_mask,
                    'bgp_as': settings.bgp_as,
                    'dhcp_ip_range_start': settings.dhcp_ip_range_start,
                    'dhcp_ip_range_end': settings.dhcp_ip_range_end,
                    'dhcp_lease_time': settings.dhcp_lease_time,
                    'management_vrf': settings.management_vrf
                }
                
                return JsonResponse({
                    'status': 'success',
                    'settings': settings_dict,
                    'is_configured': True
                })
            except ValidationError:
                # Settings don't exist yet
                return JsonResponse({
                    'status': 'success',
                    'message': 'Settings have not been configured yet',
                    'is_configured': False
                })
        
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    elif request.method == "POST":
        try:
            # Parse the request body
            data = json.loads(request.body)
            
            # Check if settings already exist
            if Settings.objects.exists():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Settings already exist and cannot be modified'
                }, status=400)
            
            # Create new settings instance
            required_fields = [
                'restconf_username', 'restconf_password', 'host_ip', 'host_subnet_mask',
                'dhcp_sites_network_ip', 'dhcp_sites_network_subnet_mask', 'bgp_as',
                'dhcp_ip_range_start', 'dhcp_ip_range_end', 'dhcp_lease_time', 'management_vrf'
            ]
            
            # Check for missing required fields
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Missing required fields: {", ".join(missing_fields)}'
                }, status=400)
            
            # Create and save new settings
            settings = Settings(
                restconf_username=data.get('restconf_username'),
                restconf_password=data.get('restconf_password'),
                host_interface_id=data.get('host_interface_id'),
                host_ip=data.get('host_ip'),
                host_subnet_mask=data.get('host_subnet_mask'),
                dhcp_sites_network_ip=data.get('dhcp_sites_network_ip'),
                dhcp_sites_network_subnet_mask=data.get('dhcp_sites_network_subnet_mask'),
                bgp_as=data.get('bgp_as'),
                dhcp_ip_range_start=data.get('dhcp_ip_range_start'),
                dhcp_ip_range_end=data.get('dhcp_ip_range_end'),
                dhcp_lease_time=data.get('dhcp_lease_time'),
                management_vrf=data.get('management_vrf')
            )
            
            # Save with validation
            try:
                settings.save()
                return JsonResponse({
                    'status': 'success',
                    'message': 'Settings created successfully'
                })
            except ValidationError as ve:
                return JsonResponse({
                    'status': 'error',
                    'message': str(ve)
                }, status=400)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error', 
                'message': 'Invalid JSON in request'
            }, status=400)
            
        except Exception as e:
            return JsonResponse({
                'status': 'error', 
                'message': f'Error creating settings: {str(e)}'
            }, status=500)
