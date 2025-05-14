import json
import ipaddress
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from core.models import Site, Customer, Interface
from core.modules.network_controller import NetworkController

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
                    'dhcp_scope': str(ipaddress.IPv4Network(f"{site.dhcp_scope.network}/{site.dhcp_scope.subnet_mask}", strict=False)),
                    'customer': {
                        'id': site.customer.id,
                        'name': site.customer.name
                    },
                    'assigned_interface': {
                        'id': site.assigned_interface.id,
                        'name': site.assigned_interface.name,
                        'router': {
                            'id': site.assigned_interface.router.id,
                            'hostname': site.assigned_interface.router.hostname
                        }
                    } if site.assigned_interface else None,
                   'router_id': site.router.id if site.router else None,
                    'has_routing': site.has_routing,
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
                
                # Serialize sites data with expanded relationships
                site_list = [
                    {
                        'id': site.id,
                        'name': site.name,
                        'description': site.description,
                        'location': site.location,
                        'dhcp_scope': str(ipaddress.IPv4Network(f"{site.dhcp_scope.network}/{site.dhcp_scope.subnet_mask}", strict=False)),
                        'customer': {
                            'id': site.customer.id,
                            'name': site.customer.name
                        },
                        'assigned_interface': {
                            'id': site.assigned_interface.id,
                            'name': site.assigned_interface.name,
                            'router': {
                                'id': site.assigned_interface.router.id,
                                'hostname': site.assigned_interface.router.hostname,
                                'status' : site.assigned_interface.router.reachable
                            }
                        } if site.assigned_interface else None,
                        'router_id': site.router.id if site.router else None,
                        'has_routing': site.has_routing,
                        'status' : site.assigned_interface.router.reachable
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
            required_fields = ['name', 'customer_id', 'assigned_interface_id']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({
                        'message': f'Missing required field: {field}'
                    }, status=400)
            
            if data['assigned_interface_id'] is None:
                return JsonResponse({
                    'message': 'assigned_interface_id cannot be null'
                }, status=400)

            # Get required objects
            try:
                customer = get_object_or_404(Customer, id=data['customer_id'])
                interface = get_object_or_404(Interface, id=data['assigned_interface_id'])
            except:
                return JsonResponse({
                    'message': 'Invalid customer_id or assigned_interface_id'
                }, status=400)

            # Create site using NetworkController
            site, success = NetworkController.create_site(
                name=data['name'],
                customer=customer,
                interface=interface,
                description=data.get('description', ''),
                location=data.get('location', '')
            )

            if not success:
                return JsonResponse({
                    'message': 'Failed to create site'
                }, status=500)

            # Return site data
            return JsonResponse({
                'id': site.id,
                'name': site.name,
                'customer_id': site.customer.id,
                'description': site.description,
                'location': site.location,
                'dhcp_scope': str(ipaddress.IPv4Network(f"{site.dhcp_scope.network}/{site.dhcp_scope.subnet_mask}", strict=False)),
                'assigned_interface_id': site.assigned_interface.id,
                'router_id': site.router.id if site.router else None,
                'status' : site.assigned_interface.router.reachable
            }, status=201)
        
        except json.JSONDecodeError:
            return JsonResponse({
                'message': 'Invalid JSON'
            }, status=400)
        
        except Exception as e:
            return JsonResponse({
                'message': str(e)
            }, status=500)

    def patch(self, request, site_id):
        try:
            # Get site
            site = get_object_or_404(Site, id=site_id)
            
            # Parse JSON data
            data = json.loads(request.body)
            
            # Update fields if provided
            if 'name' in data:
                site.name = data['name']
                
            if 'description' in data:
                site.description = data['description']
                
            if 'location' in data:
                site.location = data['location']
            
            # Save changes
            site.save()
            
            return JsonResponse({
                'id': site.id,
                'name': site.name,
                'customer_id': site.customer.id,
                'description': site.description,
                'location': site.location,
                'dhcp_scope': str(ipaddress.IPv4Network(f"{site.dhcp_scope.network}/{site.dhcp_scope.subnet_mask}", strict=False)),
                'assigned_interface_id': site.assigned_interface.id,
                'router_id': site.router.id if site.router else None,
                'status' : site.assigned_interface.router.reachable
            })
            
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
            
            # Store name for confirmation message
            site_name = site.name

            # Delete the site
            success = NetworkController.delete_site(site)
            
            if success:
                return JsonResponse({
                    'message': f'Site {site_name} successfully deleted'
                })
            else:
                if not success:
                    return JsonResponse({
                        'message': f'Failed to delete site'
                    }, status=400)
                
        except Exception as exception:
            return JsonResponse({
                    'message': f'Failed to delete site'
                }, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class SiteRoutingView(View):
    def post(self, request, site_id):
        try:
            site = get_object_or_404(Site, id=site_id)
            
            if not site.router:
                return JsonResponse({
                    'message': 'Site has no assigned router'
                }, status=400)
                
            if not site.assigned_interface:
                return JsonResponse({
                    'message': 'Site has no assigned interface'
                }, status=400)
            
            # Setup routing using NetworkController
            success = NetworkController.enable_routing(site)
            
            if success:
                site.has_routing = True
                site.save()
                return JsonResponse({
                    'message': f'Successfully configured routing for site {site.name}'
                })
            else:
                return JsonResponse({
                    'message': 'Failed to configure routing'
                }, status=500)
                
        except Exception as e:
            return JsonResponse({
                'message': str(e)
            }, status=500)

    def delete(self, request, site_id):
        try:
            site = get_object_or_404(Site, id=site_id)
            
            if not site.has_routing:
                return JsonResponse({
                    'message': 'Site routing is not enabled'
                }, status=400)
            
            # Disable routing using NetworkController
            success = NetworkController.disable_routing(site)
            
            if success:
                site.has_routing = False
                site.save()
                return JsonResponse({
                    'message': f'Successfully disabled routing for site {site.name}'
                })
            else:
                return JsonResponse({
                    'message': 'Failed to disable routing'
                }, status=500)
                
        except Exception as e:
            return JsonResponse({
                'message': str(e)
            }, status=500)
