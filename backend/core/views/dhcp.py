import json
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from core.settings import Settings
from core.models import DHCPLease
from core.modules.dhcp import DHCPServer

dhcp_server = DHCPServer()
try:
    Settings.get_settings()
    dhcp_server.start()
except:
    pass

@csrf_exempt
@require_http_methods(["POST"])
def start_dhcp_server(request):
    try:        
        success = dhcp_server.start()
        
        return JsonResponse({
            'status': 'success' if success else 'error',
            'message': 'DHCP server started successfully' if success else 'DHCP server already started' if dhcp_server.is_running() else 'Failed to start DHCP server'
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def stop_dhcp_server(request):
    try:
        success = dhcp_server.stop()
        return JsonResponse({
            'status': 'success' if success else 'error',
            'message': 'DHCP server stopped successfully' if success else 'DHCP server was not running'
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def dhcp_server_status(request):
    try:
        status = dhcp_server.get_status()
        return JsonResponse({
            'status': 'success',
            'data': status
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def dhcp_leases(request):
    try:
        leases = []
        active_leases = DHCPLease.objects.filter(expiry_time__gt=timezone.now())
        
        for lease in active_leases:
            leases.append({
                'mac_address': lease.mac_address,
                'ip_address': lease.ip_address,
                'hostname': lease.hostname,
                'expiry_time': lease.expiry_time.isoformat(),
                'remaining_seconds': lease.remaining_time
            })
        
        return JsonResponse({
            'status': 'success',
            'leases': leases
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
