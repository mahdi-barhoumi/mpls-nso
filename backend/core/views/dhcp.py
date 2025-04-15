from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from core.modules.dhcp import DHCPServer

@csrf_exempt
@require_http_methods(["POST"])
def start_dhcp_server(request):
    if DHCPServer.is_running():
        return JsonResponse({
            "message": "DHCP server already started"
        }, status=204)
    
    if DHCPServer.start():
        return JsonResponse({
            "message": "DHCP server started successfully"
        }, status=200)
    
    else:
        return JsonResponse({
            "message": "Failed to start the DHCP server"
        }, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def stop_dhcp_server(request):
    if not DHCPServer.is_running():
        return JsonResponse({
            "message": "DHCP server already stopped"
        }, status=204)
    
    if DHCPServer.stop():
        return JsonResponse({
            "message": "DHCP server stopped successfully"
        }, status=200)
    
    else:
        return JsonResponse({
            "message": "Failed to stop the DHCP server"
        }, status=400)

@csrf_exempt
@require_http_methods(["GET"])
def dhcp_server_status(request):
    return JsonResponse(DHCPServer.get_status(), status=200)

@csrf_exempt
@require_http_methods(["GET"])
def dhcp_leases(request):
    return JsonResponse(DHCPServer.get_active_leases(), status=200)
