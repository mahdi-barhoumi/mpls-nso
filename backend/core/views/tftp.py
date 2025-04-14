from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from core.modules.tftp import TFTPServer

@csrf_exempt
@require_http_methods(["POST"])
def start_tftp_server(request):
    if TFTPServer.is_running():
        return JsonResponse({
            "message": "DHCP server already started"
        }, status=204)
    
    if TFTPServer.start():
        return JsonResponse({
            "message": "DHCP server started successfully"
        }, status=200)
    
    else:
        return JsonResponse({
            "message": "Failed to start the DHCP server"
        }, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def stop_tftp_server(request):
    if not TFTPServer.is_running():
        return JsonResponse({
            "message": "DHCP server already stopped"
        }, status=204)
    
    if TFTPServer.stop():
        return JsonResponse({
            "message": "DHCP server stopped successfully"
        }, status=200)
    
    else:
        return JsonResponse({
            "message": "Failed to stop the DHCP server"
        }, status=400)

@csrf_exempt
@require_http_methods(["GET"])
def tftp_server_status(request):
    return JsonResponse(TFTPServer.get_status(), status=200)

@csrf_exempt
@require_http_methods(["GET"])
def tftp_files(request):
    return JsonResponse(TFTPServer.get_files_list(), safe=False)

@csrf_exempt
@require_http_methods(["POST"])
def upload_file(request):
    if not TFTPServer.is_running():
        return JsonResponse({
            "message": "TFTP server is not running"
        }, status=400)

    if 'file' not in request.FILES:
        return JsonResponse({
            "message": "No file uploaded"
        }, status=400)

    try:
        TFTPServer.add_file(request.FILES['file'])
        return JsonResponse({
            "message": "File uploaded successfully",
        }, status=201)
    
    except Exception as exception:
        return JsonResponse({
            "message": "Failed to upload file"
        }, status=400)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_file(request, filename):
    if not TFTPServer.is_running():
        return JsonResponse({
            "message": "TFTP server is not running"
        }, status=400)

    existing_filenames = [file['filename'] for file in TFTPServer.get_files_list()]

    if filename not in existing_filenames:
        return JsonResponse({
            "message": "File not found"
        }, status=404)

    try:
        TFTPServer.delete_file(filename)
        return JsonResponse({
            "message": "File deleted successfully"
        }, status=200)
    except Exception as exception:
        return JsonResponse({
            "message": "Failed to delete file"
        }, status=400)