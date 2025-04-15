import json
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from core.models import VPN, Site, Customer
from core.modules.controller import NetworkController

@method_decorator(csrf_exempt, name='dispatch')
class VPNView(View):
    def get(self, request, vpn_id=None):
        if vpn_id:
            try:
                vpn = VPN.objects.prefetch_related('sites').get(id=vpn_id)
                return JsonResponse({
                    'id': vpn.id,
                    'name': vpn.name,
                    'description': vpn.description,
                    'customer': {
                        'id': vpn.customer.id,
                        'name': vpn.customer.name
                    },
                    'sites': [{
                        'id': site.id,
                        'name': site.name,
                        'location': site.location,
                    } for site in vpn.sites.all()]
                })
            except VPN.DoesNotExist:
                return JsonResponse({'error': 'VPN not found'}, status=404)
        
        vpns = VPN.objects.all()
        return JsonResponse(
            [{
                'id': vpn.id,
                'name': vpn.name,
                'customer': vpn.customer.name,
                'customer_id': vpn.customer.id,
                'description': vpn.description,
                'site_count': vpn.sites.count()
            } for vpn in vpns],
        safe=False)

    def post(self, request):
        try:
            data = json.loads(request.body)
            name = data.get('name')
            description = data.get('description', '')
            customer_id = data.get('customer_id')
            
            if not name:
                return JsonResponse({'error': 'name is required'}, status=400)
            
            if not customer_id:
                return JsonResponse({'error': 'customer_id is required'}, status=400)

            try:
                customer = Customer.objects.get(id=customer_id)
            except Customer.DoesNotExist:
                return JsonResponse({'error': 'Customer not found'}, status=404)
                
            vpn = VPN.objects.create(
                name=name,
                description=description,
                customer=customer,
                discovered=False
            )
            
            return JsonResponse({
                'id': vpn.id,
                'name': vpn.name,
                'customer': customer.name,
                'description': vpn.description,
            }, status=201)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def patch(self, request, vpn_id):
        try:
            vpn = VPN.objects.get(id=vpn_id)
            data = json.loads(request.body)
            
            # Update only allowed fields
            if 'name' in data:
                vpn.name = data['name']
            if 'description' in data:
                vpn.description = data['description']
                
            vpn.save()
            
            return JsonResponse({
                'id': vpn.id,
                'name': vpn.name,
                'description': vpn.description,
                'customer': {
                    'id': vpn.customer.id,
                    'name': vpn.customer.name
                },
                'sites': [{
                    'id': site.id,
                    'name': site.name,
                    'location': site.location,
                } for site in vpn.sites.all()]
            })
            
        except VPN.DoesNotExist:
            return JsonResponse({'error': 'VPN not found'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
        
    def delete(self, request, vpn_id):
        try:
            vpn = VPN.objects.get(id=vpn_id)
            
            # Don't allow deletion of discovered VPNs
            if vpn.discovered:
                return JsonResponse({'error': 'Cannot delete discovered VPNs'}, status=400)
            
            if NetworkController.delete_vpn(vpn):
                return JsonResponse({'message': 'VPN deleted successfully'})
            else:
                return JsonResponse({'error': 'Failed to delete VPN'}, status=500)
            
        except VPN.DoesNotExist:
            return JsonResponse({'error': 'VPN not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class VPNSiteView(View):
    def post(self, request, vpn_id):
        try:
            data = json.loads(request.body)
            site_id = data.get('site_id')
            
            if not site_id:
                return JsonResponse({'error': 'Site ID is required'}, status=400)
            
            vpn = VPN.objects.get(id=vpn_id)
            site = Site.objects.get(id=site_id)
            
            # Check if site belongs to same customer as VPN
            if vpn.customer and site.customer != vpn.customer:
                return JsonResponse({'error': 'Site must belong to the same customer as the VPN'}, status=400)
            
            # Check if site is already in this VPN
            if site in vpn.sites.all():
                return JsonResponse({'error': 'Site is already part of this VPN'}, status=400)
            
            # Check if site has routing enabled (needs VRF and OSPF configuration)
            if not site.vrf or not site.ospf_process_id:
                return JsonResponse({'error': 'Site routing must be enabled before adding to VPN'}, status=400)
            
            if NetworkController.add_site_to_vpn(site, vpn):
                return JsonResponse({'message': 'Site added to VPN successfully'})
            else:
                return JsonResponse({'error': 'Failed to add site to VPN'}, status=500)
            
        except (VPN.DoesNotExist, Site.DoesNotExist):
            return JsonResponse({'error': 'VPN or Site not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def delete(self, request, vpn_id, site_id):
        try:
            vpn = VPN.objects.get(id=vpn_id)
            site = Site.objects.get(id=site_id)
            
            # Check if site is part of this VPN
            if site not in vpn.sites.all():
                return JsonResponse({'error': 'Site is not part of this VPN'}, status=400)
            
            if NetworkController.remove_site_from_vpn(site, vpn):
                return JsonResponse({'message': 'Site removed from VPN successfully'})
            else:
                return JsonResponse({'error': 'Failed to remove site from VPN'}, status=500)
            
        except (VPN.DoesNotExist, Site.DoesNotExist):
            return JsonResponse({'error': 'VPN or Site not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    