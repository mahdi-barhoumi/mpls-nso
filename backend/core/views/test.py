from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.serializers import serialize
from core.modules.network_controller import NetworkController
from core.modules.discovery import NetworkDiscoverer
from core.modules.utils.host_network_manager import HostNetworkManager
from core.models import *

@csrf_exempt
@require_http_methods(["GET"])
def test_view(request):
    try:

        #interface = Interface.objects.filter(ip_address="172.0.0.6")

        #data = serialize('json', interface)

        #data = NetworkDiscoverer.discover_single_device("172.0.0.6")

        #data = NetworkController.disable_route_redistribution(site=Site.objects.get(pk=2))

        data = Router.objects.get(pk=6).delete()

        return JsonResponse(data, safe=False)

    except Exception as e:
        return JsonResponse({
            'error': f'{str(e)}'
        }, status=500)