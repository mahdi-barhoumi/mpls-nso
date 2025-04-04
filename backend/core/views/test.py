from django.http import JsonResponse
from django.core.serializers import serialize
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from core.modules.controller import NetworkController
from core.models import *

@csrf_exempt
@require_http_methods(["GET"])
def test_view(request):
    try:

        router = Router.objects.get(pk=1)
        interface, created = Interface.objects.get_or_new(
            name="GigabitEthernet6.10",
            router=router,
        )

        interface.vlan = 10
        interface.addressing = "dhcp"
        interface.dhcp_helper_address = "192.168.100.2"
        interface.enabled = True
        interface.vrf = VRF.objects.get(router=interface.router, name="customer-1")

        data = NetworkController.delete_interface(interface)

        return JsonResponse(data, safe=False)

    except Exception as e:
        return JsonResponse({
            'error': f'{str(e)}'
        }, status=500)