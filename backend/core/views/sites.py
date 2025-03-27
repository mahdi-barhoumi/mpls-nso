import json
import ipaddress
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from core.settings import get_settings
from core.models import Site, Customer, Router, Interface, DHCPScope
from core.modules.controller import NetworkController

@csrf_exempt
@require_http_methods(["GET"])
def list_sites(request):
    try:
        # Optional customer filtering
        customer_id = request.GET.get('customer_id')
        
        if customer_id:
            sites = Site.objects.filter(customer_id=customer_id)
        else:
            sites = Site.objects.all()
        
        # Serialize sites data
        site_list = [
            {
                'id': site.id,
                'name': site.name,
                'customer_id': site.customer.id,
                'description': site.description,
                'location': site.location,
                'dhcp_scope': site.dhcp_scope.network,
                'router_chassis_id': site.router.chassis_id if site.router else None
            }
            for site in sites
        ]
        
        return JsonResponse({
            'status': 'success',
            'data': site_list
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_site(request, site_id):
    try:
        site = get_object_or_404(Site, id=site_id)
        
        site_data = {
            'id': site.id,
            'name': site.name,
            'customer': site.customer.name,
            'description': site.description,
            'location': site.location,
            'dhcp_scope': site.dhcp_scope.network,
            'router_chassis_id': site.router.chassis_id if site.router else None
        }
        
        return JsonResponse({
            'status': 'success',
            'data': site_data
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def create_site(request):
    try:
        # Parse JSON data
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['name', 'customer_id']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }, status=400)
        
        # Get customer
        customer = get_object_or_404(Customer, id=data['customer_id'])
        
        # Get settings
        settings = get_settings()
        
        # Parse the DHCP sites network from settings
        dhcp_sites_network = ipaddress.IPv4Network(
            f"{settings.dhcp_sites_network_address}/{settings.dhcp_sites_network_subnet_mask}", 
            strict=False
        )
        
        # If a DHCP scope is not provided, find an available /30 subnet
        if 'dhcp_scope' not in data:
            # Get all existing site DHCP scopes
            existing_scopes = DHCPScope.objects.all()
            used_scopes = {
                ipaddress.IPv4Network(f"{scope.network}/30", strict=False) 
                for scope in existing_scopes
            }
            
            # Find the first available /30 subnet
            for network in dhcp_sites_network.subnets(new_prefix=30):
                if not any(network.overlaps(used_scope) for used_scope in used_scopes):
                    dhcp_scope_network = str(network[0])
                    break
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No available DHCP scope found'
                }, status=400)
        else:
            dhcp_scope_network = data['dhcp_scope']
        
        # Create DHCP Scope
        dhcp_scope = DHCPScope(
            is_active=False,
            network=dhcp_scope_network,
            subnet_mask='255.255.255.252' 
        )

        # Validate the DHCP scope
        dhcp_scope.save()

        # Create site
        site = Site(
            name=data['name'],
            customer=customer,
            description=data.get('description', ''),
            location=data.get('location', ''),
            dhcp_scope=dhcp_scope,
        )
        
        # Validate and save site
        site.save()
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'id': site.id,
                'name': site.name,
                'customer_id': site.customer.id,
                'description': site.description,
                'location': site.location,
                'dhcp_scope': site.dhcp_scope.network,
            }
        }, status=201)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON'
        }, status=400)
    
    except (ValidationError, ValueError) as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def attach_site_to_interface(request, site_id):
    try:
        # Parse JSON data
        data = json.loads(request.body)
        
        # Validate required fields
        if 'interface_id' not in data:
            return JsonResponse({
                'status': 'error',
                'message': 'Missing required field: interface_id'
            }, status=400)
        
        # Get site and interface
        site = get_object_or_404(Site, id=site_id)
        interface = get_object_or_404(Interface, id=data['interface_id'])
        
        # Perform attachment using NetworkController
        success = NetworkController.attach_site_to_interface(interface, site)
        
        if success:
            return JsonResponse({
                'status': 'success',
                'message': f'Site {site.name} successfully attached to interface {interface.name}',
                'data': {
                    'site_id': site.id,
                    'interface_id': interface.id,
                    'interface_name': interface.name,
                    'router_hostname': interface.router.hostname
                }
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Failed to attach site to interface'
            }, status=500)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON'
        }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
