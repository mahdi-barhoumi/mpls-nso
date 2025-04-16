from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from core.modules.utils.host_network_manager import HostNetworkManager

@csrf_exempt
@require_http_methods(["GET"])
def list_host_interfaces(request):
    try:
        interfaces = HostNetworkManager.list_interfaces()

        # Sort interfaces by ID
        interfaces.sort(key=lambda x: x['id'])
        
        return JsonResponse(interfaces, status=200, safe=False)

    except Exception as exception:
        return JsonResponse({
            'message': "Failed fetching host interfaces"
        }, status=400)
