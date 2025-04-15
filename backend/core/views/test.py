from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from core.modules.controller import NetworkController
from core.models import *

@csrf_exempt
@require_http_methods(["GET"])
def test_view(request):
    try:

        router = Router.objects.get(pk=1)

        data = NetworkController.set_router_hostname(router, "PE1")

        return JsonResponse(data, safe=False)

    except Exception as e:
        return JsonResponse({
            'error': f'{str(e)}'
        }, status=500)