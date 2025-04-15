from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from core.modules.discovery import NetworkDiscoverer

@csrf_exempt
@require_http_methods(["GET"])
def discover_network(request):
    try:
        result = NetworkDiscoverer.discover_network()
        
        # Return results
        return JsonResponse(result)
    
    except Exception as exception:
        return JsonResponse({
            'message': "Failed running network discovery"
        }, status=400)
