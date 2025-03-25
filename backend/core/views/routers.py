from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError

from core.models import Router, Interface

@csrf_exempt
@require_http_methods(["GET"])
def list_routers(request):
    try:
        routers = Router.objects.all()
        router_list = [{
            'chassis_id': router.chassis_id,
            'hostname': router.hostname,
            'management_ip_address': router.management_ip_address,
            'role': router.get_role_display(),
            'last_discovered': router.last_discovered.isoformat()
        } for router in routers]
        
        return JsonResponse({
            'status': 'success',
            'count': len(router_list),
            'data': router_list
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_router(request, router_id):
    try:
        router = get_object_or_404(Router, chassis_id=router_id)
        
        router_data = {
            'chassis_id': router.chassis_id,
            'hostname': router.hostname,
            'management_ip_address': router.management_ip_address,
            'role': router.get_role_display(),
            'last_discovered': router.last_discovered.isoformat(),
            'vrf_count': router.vrfs.count(),
            'interface_count': router.interfaces.count()
        }
        
        return JsonResponse({
            'status': 'success',
            'data': router_data
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def list_router_interfaces(request, router_id):
    try:
        router = get_object_or_404(Router, chassis_id=router_id)
        interfaces = router.interfaces.all()
        
        interface_list = [{
            'id': interface.id,
            'name': interface.name,
            'admin_status': interface.admin_status,
            'oper_status': interface.oper_status,
            'ip_address': str(interface.ip_address) if interface.ip_address else None,
            'vrf': interface.vrf.name if interface.vrf else None,
            'is_connected': interface.is_connected
        } for interface in interfaces]
        
        return JsonResponse({
            'status': 'success',
            'router_hostname': router.hostname,
            'count': len(interface_list),
            'data': interface_list
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_router_interface(request, router_id, interface_id):
    try:
        router = get_object_or_404(Router, chassis_id=router_id)
        interface = get_object_or_404(Interface, id=interface_id, router=router)
        
        interface_data = {
            'id': interface.id,
            'name': interface.name,
            'admin_status': interface.admin_status,
            'oper_status': interface.oper_status,
            'description': interface.description,
            'ip_address': str(interface.ip_address) if interface.ip_address else None,
            'subnet_mask': str(interface.subnet_mask) if interface.subnet_mask else None,
            'mac_address': interface.mac_address,
            'vrf': interface.vrf.name if interface.vrf else None,
            'site': interface.site.name if interface.site else None,
            'is_connected': interface.is_connected,
            'connected_interfaces': [
                {'id': conn.id, 'name': conn.name, 'router': conn.router.hostname}
                for conn in interface.connected_interfaces.all()
            ]
        }
        
        return JsonResponse({
            'status': 'success',
            'router_hostname': router.hostname,
            'data': interface_data
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
