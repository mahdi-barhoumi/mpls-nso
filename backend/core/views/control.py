import json
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from core.models import DHCPLease
from core.modules.controller import NetworkController

@csrf_exempt
@require_http_methods(["POST"])
def start_dhcp_server(request):
    try:        
        success = NetworkController.start_dhcp_server()
        
        return JsonResponse({
            'status': 'success' if success else 'error',
            'message': 'DHCP server started successfully' if success else 'DHCP server already started'
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
        success = NetworkController.stop_dhcp_server()
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
        status = NetworkController.get_dhcp_server_status()
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

@csrf_exempt
@require_http_methods(["POST"])
def start_tftp_server(request):
    try:
        data = json.loads(request.body)

        # Required parameters
        server_ip = data.get('server_ip')
        
        # Optional parameters
        max_block_size = int(data.get('max_block_size', 512))
        
        # Validate required parameters
        if not server_ip:
            return JsonResponse({
                'success': False,
                'error': 'Missing required parameters'
            }, status=400)
        
        success = NetworkController.start_tftp_server(
            server_ip=server_ip,
            max_block_size=max_block_size
        )
        
        return JsonResponse({
            'success': success,
            'message': 'TFTP server started successfully' if success else 'TFTP server already started' if NetworkController.is_tftp_server_running() else 'Failed to start TFTP server'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def stop_tftp_server(request):
    try:
        success = NetworkController.stop_tftp_server()
        return JsonResponse({
            'success': success,
            'message': 'TFTP server stopped successfully' if success else 'TFTP server was not running'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def tftp_server_status(request):
    try:
        status = NetworkController.get_tftp_server_status()
        return JsonResponse(status)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def tftp_files(request):
    try:
        files = NetworkController.get_tftp_files_list()
        return JsonResponse({
            'count': len(files),
            'files': files
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def upload_file(request):
    try:
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'No file uploaded'
            }, status=400)
            
        uploaded_file = request.FILES['file']
        filename = NetworkController.upload_tftp_file(uploaded_file)
                
        return JsonResponse({
            'success': True,
            'message': f'File {filename} uploaded successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_file(request, filename):
    try:
        filename = NetworkController.delete_tftp_file(filename)
        
        return JsonResponse({
            'success': True,
            'message': f'File {filename} deleted successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
