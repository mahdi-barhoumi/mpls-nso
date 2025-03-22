import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from core.modules.interface_control import InterfaceControl
from core.models import DHCPLease
from django.utils import timezone

# Create a single instance of the InterfaceControl class
interface_controller = InterfaceControl(
    username=getattr(settings, 'ROUTER_USERNAME', 'mgmt'),
    password=getattr(settings, 'ROUTER_PASSWORD', 'mgmtapp'),
)

@csrf_exempt
@require_http_methods(["GET"])
def connect_routers(request):
    """Connect to all routers found in DHCP leases and retrieve interface data"""
    try:
        results = interface_controller.process_all_routers()
        return JsonResponse({
            'success': True,
            'data': results
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def list_interfaces(request):
    """List all interfaces on connected routers"""
    try:
        results = interface_controller.process_all_routers()
        return JsonResponse({'interfaces': results})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_interface(request, interface_name):
    """Get details for a specific interface across all routers"""
    try:
        result = interface_controller.get_interface_status(interface_name)
        if result['success']:
            return JsonResponse(result)
        return JsonResponse(result, status=404 if 'not found' in result.get('error', '') else 500)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def enable_interface(request, interface_name):
    """Enable a specific interface across all routers"""
    try:
        result = interface_controller.enable_interface(interface_name)
        return JsonResponse(result, status=200 if result['success'] else 500)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def disable_interface(request, interface_name):
    """Disable a specific interface across all routers"""
    try:
        result = interface_controller.disable_interface(interface_name)
        return JsonResponse(result, status=200 if result['success'] else 500)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def enable_all_interfaces(request):
    """Enable all interfaces on all routers"""
    try:
        # Get router IP from request parameters or apply to all active routers
        router_ip = request.GET.get('router_ip')
        
        if router_ip:
            # Enable interfaces on the specified router
            result = interface_controller.enable_all_interfaces(router_ip)
            return JsonResponse({'success': True, 'result': result})
        else:
            # Enable interfaces on all active routers
            dhcp_leases = DHCPLease.objects.filter(expiry_time__gt=timezone.now())
            results = []
            
            for lease in dhcp_leases:
                router_result = interface_controller.enable_all_interfaces(lease.ip_address)
                results.append(router_result)
                
            return JsonResponse({'success': True, 'results': results})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def disable_all_interfaces(request):
    """Disable all interfaces on all routers"""
    try:
        # Get router IP from request parameters or apply to all active routers
        router_ip = request.GET.get('router_ip')
        
        if router_ip:
            # Disable interfaces on the specified router
            result = interface_controller.disable_all_interfaces(router_ip)
            return JsonResponse({'success': True, 'result': result})
        else:
            # Disable interfaces on all active routers
            dhcp_leases = DHCPLease.objects.filter(expiry_time__gt=timezone.now())
            results = []
            
            for lease in dhcp_leases:
                router_result = interface_controller.disable_all_interfaces(lease.ip_address)
                results.append(router_result)
                
            return JsonResponse({'success': True, 'results': results})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)