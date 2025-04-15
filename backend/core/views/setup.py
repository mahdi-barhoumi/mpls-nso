import json
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.models import User
from django.apps import apps
from django.core.exceptions import ValidationError
from core.settings import Settings, get_settings
from core.modules.controller import NetworkController
from core.modules.discovery import NetworkDiscoverer
from core.modules.dhcp import DHCPServer
from core.modules.tftp import TFTPServer

@method_decorator(csrf_exempt, name='dispatch')
class SetupStatusView(View):
    def get(self, request):
        app_config = apps.get_app_config('core')
        return JsonResponse({
            'needs_setup': not (app_config.state['has_admin'] and app_config.state['has_settings']),
            'has_admin': app_config.state['has_admin'],
            'has_settings': app_config.state['has_settings'],
            'settings': self.get_settings() if app_config.state['has_settings'] else None
        })

    def get_settings(self):
        settings = get_settings()
        if not settings:
            return None
            
        return {
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

@method_decorator(csrf_exempt, name='dispatch')
class AdminSetupView(View):
    def post(self, request):
        app_config = apps.get_app_config('core')
        
        # Check if admin already exists
        if app_config.state['has_admin']:
            return JsonResponse({
                'message': 'Admin user already exists'
            }, status=400)

        try:
            data = json.loads(request.body)
            
            # Validate required fields
            required = ['username', 'password', 'email']
            if not all(field in data for field in required):
                return JsonResponse({
                    'message': 'Missing required fields'
                }, status=400)
            
            # Create superuser
            User.objects.create_superuser(
                username=data['username'],
                password=data['password'],
                email=data['email']
            )
            
            # Update state
            app_config.state['has_admin'] = True
            
            return JsonResponse({
                'message': 'Admin user created successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'message': str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class SettingsSetupView(View):
    def post(self, request):
        app_config = apps.get_app_config('core')
        
        # Check if settings already exist
        if app_config.state['has_settings']:
            return JsonResponse({
                'message': 'Settings already exist and cannot be modified'
            }, status=400)

        try:
            data = json.loads(request.body)
            required_fields = [
                'restconf_username', 'restconf_password', 'host_interface_id', 
                'host_address', 'host_subnet_mask', 'dhcp_sites_network_address', 
                'dhcp_sites_network_subnet_mask', 'dhcp_lease_time', 
                'management_vrf', 'bgp_as'
            ]
            
            # Check for missing or empty fields
            missing = [f for f in required_fields if not data.get(f)]
            if missing:
                return JsonResponse({
                    'message': f'Missing or empty required fields: {", ".join(missing)}'
                }, status=400)

            # Validate data types and formats
            if not isinstance(data.get('bgp_as'), int):
                return JsonResponse({
                    'message': 'BGP AS must be an integer'
                }, status=400)

            if not isinstance(data.get('dhcp_lease_time'), int):
                return JsonResponse({
                    'message': 'DHCP lease time must be an integer'
                }, status=400)

            # Create settings
            settings = Settings(
                restconf_username=data['restconf_username'],
                restconf_password=data['restconf_password'],
                host_interface_id=data['host_interface_id'],
                host_address=data['host_address'],
                host_subnet_mask=data['host_subnet_mask'],
                dhcp_provider_network_address=data['host_address'],
                dhcp_provider_network_subnet_mask=data['host_subnet_mask'],
                dhcp_sites_network_address=data['dhcp_sites_network_address'],
                dhcp_sites_network_subnet_mask=data['dhcp_sites_network_subnet_mask'],
                dhcp_lease_time=data['dhcp_lease_time'],
                management_vrf=data['management_vrf'],
                bgp_as=data['bgp_as']
            )

            # Validate and save
            settings.save()
            
            # Initialize services
            NetworkController.initialize()
            NetworkDiscoverer.initialize()
            DHCPServer.start()
            TFTPServer.start()
            
            # Update state
            app_config.state['has_settings'] = True

            return JsonResponse({
                'message': 'Settings configured successfully'
            })

        except ValidationError as e:
            return JsonResponse({
                'message': str(e)
            }, status=400)
            
        except Exception as e:
            return JsonResponse({
                'message': str(e)
            }, status=500)
