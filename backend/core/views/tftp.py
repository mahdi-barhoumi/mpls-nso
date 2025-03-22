import os
import json
from django.apps import apps
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from core.modules.tftp import TFTPServer

tftp_server = TFTPServer()

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
        
        success = tftp_server.start(
            root_dir=os.path.join(apps.get_app_config('core').path, 'data\\tftp-files'),
            server_ip=server_ip,
            port=69,
            max_block_size=max_block_size
        )
        
        return JsonResponse({
            'success': success,
            'message': 'TFTP server started successfully' if success else 'TFTP server already started' if tftp_server.is_running() else 'Failed to start TFTP server'
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
        success = tftp_server.stop()
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
        status = tftp_server.get_status()
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
        files = tftp_server.get_files_list()
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
    if not tftp_server.is_running():
        return JsonResponse({
            'success': False,
            'error': 'TFTP server is not running'
        }, status=400)
        
    try:
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'No file uploaded'
            }, status=400)
            
        uploaded_file = request.FILES['file']
        filename = uploaded_file.name
        
        # Ensure root directory exists
        if not tftp_server.root_dir:
            return JsonResponse({
                'success': False,
                'error': 'TFTP server root directory not set'
            }, status=500)
            
        # Save file to TFTP root directory
        file_path = os.path.join(tftp_server.root_dir, filename)
        
        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
                
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
    if not tftp_server.is_running():
        return JsonResponse({
            'success': False,
            'error': 'TFTP server is not running'
        }, status=400)
        
    try:
        if not filename:
            return JsonResponse({
                'success': False,
                'error': 'No filename provided'
            }, status=400)
            
        # Ensure root directory exists
        if not tftp_server.root_dir:
            return JsonResponse({
                'success': False,
                'error': 'TFTP server root directory not set'
            }, status=500)
            
        # Create full path and verify it's within root_dir
        file_path = os.path.realpath(os.path.normpath(os.path.join(tftp_server.root_dir, filename)))
        
        if not file_path.startswith(tftp_server.root_dir):
            return JsonResponse({
                'success': False,
                'error': 'Access denied'
            }, status=403)
            
        if not os.path.exists(file_path):
            return JsonResponse({
                'success': False,
                'error': f'File {filename} not found'
            }, status=404)
            
        os.remove(file_path)
        
        return JsonResponse({
            'success': True,
            'message': f'File {filename} deleted successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
