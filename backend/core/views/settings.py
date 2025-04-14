import json
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.exceptions import ValidationError
from core.modules.controller import NetworkController
from core.modules.discovery import NetworkDiscoverer
from core.modules.dhcp import DHCPServer
from core.modules.tftp import TFTPServer
from core.settings import Settings, get_settings

@method_decorator(csrf_exempt, name='dispatch')
class SettingsView(View):
    def get(self, request):
        # Check if settings exist first
        settings = get_settings()
        if settings:
            # Convert settings to a dictionary
            settings_dict = {
                'restconf_username': settings.restconf_username,
                'restconf_password': settings.restconf_password,
                'host_interface_id': settings.host_interface_id,
                'host_address': settings.host_address,
                'host_subnet_mask': settings.host_subnet_mask,
                'dhcp_provider_network_address': settings.dhcp_provider_network_address,
                'dhcp_provider_network_subnet_mask': settings.dhcp_provider_network_subnet_mask,
                'dhcp_sites_network_address': settings.dhcp_sites_network_address,
                'dhcp_sites_network_subnet_mask': settings.dhcp_sites_network_subnet_mask,
                'dhcp_lease_time': settings.dhcp_lease_time,
                'management_vrf': settings.management_vrf,
                'bgp_as': settings.bgp_as
            }
            
            return JsonResponse({
                'status': 'success',
                'settings': settings_dict,
                'is_configured': True
            })
        
        return JsonResponse({
            'status': 'success', 
            'message': 'Settings have not been configured yet',
            'is_configured': False
        })

    def post(self, request):
        try:
            # Parse the request body
            data = json.loads(request.body)
            
            # Check if settings already exist
            if get_settings():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Settings already exist and cannot be modified'
                }, status=400)
            
            # Create new settings instance
            required_fields = [
                'restconf_username', 'restconf_password', 'host_interface_id', 'host_address', 'host_subnet_mask',
                'dhcp_sites_network_address', 'dhcp_sites_network_subnet_mask', 'dhcp_lease_time', 'management_vrf', 'bgp_as'
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
                host_address=data.get('host_address'),
                host_subnet_mask=data.get('host_subnet_mask'),
                dhcp_provider_network_address=data.get('host_address'),
                dhcp_provider_network_subnet_mask=data.get('host_subnet_mask'),
                dhcp_sites_network_address=data.get('dhcp_sites_network_address'),
                dhcp_sites_network_subnet_mask=data.get('dhcp_sites_network_subnet_mask'),
                dhcp_lease_time=data.get('dhcp_lease_time'),
                management_vrf=data.get('management_vrf'),
                bgp_as=data.get('bgp_as')
            )
            
            # Save with validation
            try:
                settings.save()
                NetworkController.initialize()
                NetworkDiscoverer.initialize()
                DHCPServer.start()
                TFTPServer.start()
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
