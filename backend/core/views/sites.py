import json
import ipaddress
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from core.settings import get_settings
from core.models import Site, Customer, Router, Interface, DHCPScope
from core.modules.controller import NetworkController

@method_decorator(csrf_exempt, name='dispatch')
class SiteView(View):
    def get(self, request, site_id=None):
        try:
            # Get specific site
            if site_id:
                site = get_object_or_404(Site, id=site_id)
                
                site_data = {
                    'id': site.id,
                    'name': site.name,
                    'description': site.description,
                    'location': site.location,
                    'dhcp_scope': site.dhcp_scope.network,
                    'customer_id': site.customer.id,
                    'assigned_interface_id': site.assigned_interface.id if site.assigned_interface else None,
                    'router_id': site.router.id if site.router else None
                }
                
                return JsonResponse(site_data)
            
            # List all sites
            else:
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
                        'description': site.description,
                        'location': site.location,
                        'dhcp_scope': site.dhcp_scope.network,
                        'customer_id': site.customer.id,
                        'assigned_interface_id': site.assigned_interface.id if site.assigned_interface else None,
                        'router_id': site.router.id if site.router else None
                    }
                    for site in sites
                ]
                
                return JsonResponse(site_list, safe=False)
        
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)
    
    def post(self, request):
        try:
            # Parse JSON data
            data = json.loads(request.body)
            
            # Validate required fields
            required_fields = ['name', 'customer_id']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({
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
                'id': site.id,
                'name': site.name,
                'customer_id': site.customer.id,
                'description': site.description,
                'location': site.location,
                'dhcp_scope': site.dhcp_scope.network,
            }, status=201)
        
        except json.JSONDecodeError:
            return JsonResponse({
                'message': 'Invalid JSON'
            }, status=400)
        
        except (ValidationError, ValueError) as e:
            return JsonResponse({
                'message': str(e)
            }, status=400)
        
        except Exception as e:
            return JsonResponse({
                'message': str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class SiteInterfaceView(View):
    def post(self, request, site_id):
        try:
            # Parse JSON data
            data = json.loads(request.body)
            
            # Validate required fields
            if 'interface_id' not in data:
                return JsonResponse({
                    'message': 'Missing required field: interface_id'
                }, status=400)
            
            # Get site and interface
            site = get_object_or_404(Site, id=site_id)
            interface = get_object_or_404(Interface, id=data['interface_id'])
            
            # Perform attachment using NetworkController
            success = NetworkController.assign_interface(interface, site)
            
            if success:
                return JsonResponse({
                    'message': f'Interface {interface.name} successfully assigned to site {site.name}',
                })
            else:
                return JsonResponse({
                    'message': 'Failed to assign interface to site'
                }, status=500)
        
        except json.JSONDecodeError:
            return JsonResponse({
                'message': 'Invalid JSON'
            }, status=400)
        
        except Exception as e:
            return JsonResponse({
                'message': str(e)
            }, status=500)

    def delete(self, request, site_id):
        try:
            # Get site
            site = get_object_or_404(Site, id=site_id)
            
            # Check if site has an assigned interface
            if not site.assigned_interface:
                return JsonResponse({
                    'message': 'Site has no assigned interface'
                }, status=400)
            
            interface = site.assigned_interface
            
            # Perform unassignment using NetworkController
            success = NetworkController.unassign_interface(interface, site)
            
            if success:
                return JsonResponse({
                    'message': f'Interface {interface.name} successfully unassigned from site {site.name}'
                })
            else:
                return JsonResponse({
                    'message': 'Failed to unassign interface from site'
                }, status=500)
                
        except Exception as e:
            return JsonResponse({
                'message': str(e)
            }, status=500)