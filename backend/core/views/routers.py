from django.http import JsonResponse
from django.views import View
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from core.models import Router, Interface

@method_decorator(csrf_exempt, name='dispatch')
class RouterView(View):
    def get(self, request, router_id=None):
        try:
            if router_id:
                # Single router detail
                router = get_object_or_404(Router, id=router_id)
                
                router_data = {
                    'id': router.id,
                    'role': router.get_role_display(),
                    'hostname': router.hostname,
                    'management_ip_address': router.management_ip_address,
                    'chassis_id': router.chassis_id,
                    'interface_count': router.interfaces.count(),
                    'vrf_count': router.vrfs.count(),
                    'last_discovered': router.last_discovered.isoformat(),
                }
                
                return JsonResponse(router_data)
            else:
                # List all routers
                routers = Router.objects.all()
                router_list = [{
                    'id': router.id,
                    'role': router.get_role_display(),
                    'hostname': router.hostname,
                    'management_ip_address': router.management_ip_address,
                    'chassis_id': router.chassis_id,
                    'last_discovered': router.last_discovered.isoformat()
                } for router in routers]
                
                return JsonResponse(router_list, safe=False)
        
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class RouterInterfaceView(View):
    def get(self, request, router_id, interface_id=None):
        try:
            router = get_object_or_404(Router, id=router_id)
            
            if interface_id:
                # Single interface detail
                interface = get_object_or_404(Interface, id=interface_id, router=router)
                
                interface_data = {
                    'id': interface.id,
                    'name': interface.name,
                    'enabled': interface.enabled,
                    'description': interface.description,
                    'ip_address': str(interface.ip_address) if interface.ip_address else None,
                    'subnet_mask': str(interface.subnet_mask) if interface.subnet_mask else None,
                    'mac_address': interface.mac_address,
                    'category': interface.category,
                    'type': interface.type,
                    'is_management': interface.is_management_interface,
                    'vrf': interface.vrf.name if interface.vrf else None,
                    'site': interface.site.name if interface.site else None,
                    'is_connected': interface.is_connected,
                    'connected_interfaces': [
                        {'id': conn.id, 'name': conn.name, 'router_id': conn.router.id}
                        for conn in interface.connected_interfaces.all()
                    ]
                }
                
                return JsonResponse(interface_data)
            else:
                # List all interfaces for router
                interfaces = router.interfaces.all()
                
                interface_list = [{
                    'id': interface.id,
                    'name': interface.name,
                    'enabled': interface.enabled,
                    'description': interface.description,
                    'category': interface.category,
                    'type': interface.type,
                    'is_management': interface.is_management_interface,
                    'ip_address': str(interface.ip_address) if interface.ip_address else None,
                    'subnet_mask': str(interface.subnet_mask) if interface.subnet_mask else None,
                    'mac_address': interface.mac_address,
                    'vrf': interface.vrf.name if interface.vrf else None,
                    'site': interface.site.name if interface.site else None,
                    'is_connected': interface.is_connected,
                    'connected_interfaces': [
                        {'id': conn.id, 'name': conn.name, 'router_id': conn.router.id}
                        for conn in interface.connected_interfaces.all()
                    ]
                } for interface in interfaces]
                
                response_data = {
                    'count': len(interface_list),
                    'interfaces': interface_list
                }
                
                return JsonResponse(response_data)
        
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)
