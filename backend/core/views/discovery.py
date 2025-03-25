from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from core.modules.discovery import NetworkDiscoverer

@csrf_exempt
@require_http_methods(["GET"])
def discover_network(request):
    try:
        # Initialize discovery service and discover network
        discoverer = NetworkDiscoverer()
        result = discoverer.discover_network()
        
        # Return results
        return JsonResponse({
            'status': 'success',
            'data': result
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
