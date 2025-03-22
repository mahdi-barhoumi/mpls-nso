import json
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from core.models import DHCPLease
from core.modules.dhcp import DHCPServer

dhcp_server = DHCPServer()

@csrf_exempt
@require_http_methods(["POST"])
def start_dhcp_server(request):
    try:
        data = json.loads(request.body)

        # Required parameters
        server_ip = data.get('server_ip')
        start_ip = data.get('start_ip')
        end_ip = data.get('end_ip')
        subnet_mask = data.get('subnet_mask')
        config_filename = data.get('config_filename')
        tftp_server_ip = data.get('tftp_server_ip')
        
        # Optional parameters
        tftp_server_name = data.get('tftp_server_name')
        lease_time = int(data.get('lease_time', 86400))
        
        # Validate required parameters
        if not all([server_ip, start_ip, end_ip, subnet_mask, config_filename, tftp_server_ip]):
            return JsonResponse({
                'success': False,
                'error': 'Missing required parameters'
            }, status=400)
        
        success = dhcp_server.start(
            server_ip=server_ip,
            start_ip=start_ip,
            end_ip=end_ip,
            subnet_mask=subnet_mask,
            config_filename=config_filename,
            tftp_server_ip=tftp_server_ip,
            tftp_server_name=tftp_server_name,
            lease_time=lease_time
        )
        
        return JsonResponse({
            'success': success,
            'message': 'DHCP server started successfully' if success else 'DHCP server already started' if dhcp_server.is_running() else 'Failed to start DHCP server'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def stop_dhcp_server(request):
    try:
        success = dhcp_server.stop()
        return JsonResponse({
            'success': success,
            'message': 'DHCP server stopped successfully' if success else 'DHCP server was not running'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def dhcp_server_status(request):
    try:
        status = dhcp_server.get_status()
        return JsonResponse(status)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
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
            'count': len(leases),
            'leases': leases
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
