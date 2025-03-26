import json
import ipaddress
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from core.settings import Settings
from core.models import Site, Customer, Router

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
        site_list = []
        for site in sites:
            site_data = {
                'id': site.id,
                'name': site.name,
                'customer_id': site.customer.id,
                'description': site.description,
                'location': site.location,
                'management_network': site.management_network,
                'router_chassis_id': site.router.chassis_id if site.router else None
            }
            site_list.append(site_data)
        
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
            'management_network': site.management_network,
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
        
        # Get global settings
        settings = Settings.get_settings()
        
        # Parse the DHCP sites network from settings
        dhcp_sites_network = ipaddress.IPv4Network(
            f"{settings.dhcp_sites_network_ip}/{settings.dhcp_sites_network_subnet_mask}", 
            strict=False
        )
        
        # If management network is not provided, find an available /30 subnet
        if 'management_network' not in data:
            # Get all existing site management networks
            existing_sites = Site.objects.all()
            used_networks = set()
            
            for site in existing_sites:
                other_management_ip = ipaddress.IPv4Address(site.management_network)
                used_networks.add(ipaddress.IPv4Network(f"{other_management_ip}/30", strict=False))
            
            # Find the first available /30 subnet
            for network in dhcp_sites_network.subnets(new_prefix=30):
                is_available = all(
                    not network.overlaps(used_network) 
                    for used_network in used_networks
                )
                
                if is_available:
                    management_network = str(network[0])
                    break
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No available management network found'
                }, status=400)
        else:
            management_network = data['management_network']
        
        # Create site
        site = Site(
            name=data['name'],
            customer=customer,
            description=data.get('description', ''),
            location=data.get('location', ''),
            management_network=management_network,
        )
        
        # Validate site
        try:
            site.save()
        except ValidationError as e:
            return JsonResponse({
                'status': 'error',
                'message': e.message
            }, status=400)
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'id': site.id,
                'name': site.name,
                'customer_id': site.customer.id,
                'description': site.description,
                'location': site.location,
                'management_network': site.management_network,
            }
        }, status=201)
    
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
