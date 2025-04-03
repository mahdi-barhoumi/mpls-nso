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

        interface = Interface.objects.get(pk=14)

        data = interface.category

        return JsonResponse(data, safe=False)

    except Exception as e:
        return JsonResponse({
            'error': f'{str(e)}'
        }, status=500)