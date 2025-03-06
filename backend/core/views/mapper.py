from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from core.modules.mapper import NetworkMapper

@csrf_exempt
@require_http_methods(["GET"])
def discover_network(request):
    try:
        # Get credentials from settings or use defaults
        username = getattr(settings, 'ROUTER_USERNAME', 'mgmt')
        password = getattr(settings, 'ROUTER_PASSWORD', 'mgmtapp')
        
        # Initialize mapper and discover network
        mapper = NetworkMapper(username, password)
        result = mapper.discover_network()
        
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