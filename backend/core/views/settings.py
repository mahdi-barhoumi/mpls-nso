import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError

from core.models import Settings

@csrf_exempt
@require_http_methods(["GET", "POST"])
def global_settings(request):
    if request.method == "GET":
        try:
            settings = Settings.get_settings()
            
            # Convert settings to a dictionary
            settings_dict = {
                'restconf_username': settings.restconf_username,
                'restconf_password': settings.restconf_password,
                'host_interface_id': settings.host_interface_id,
                'host_ip': settings.host_ip,
                'host_subnet_mask': settings.host_subnet_mask,
                'bgp_as': settings.bgp_as,
                'dhcp_ip_range_start': settings.dhcp_ip_range_start,
                'dhcp_ip_range_end': settings.dhcp_ip_range_end,
                'dhcp_lease_time': settings.dhcp_lease_time,
                'management_vrf': settings.management_vrf,
                'last_updated': settings.updated_at.isoformat(),
            }
            
            return JsonResponse({
                'status': 'success',
                'data': settings_dict
            })
        
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    elif request.method == "POST":
        try:
            # Parse the request body
            data = json.loads(request.body)
            
            # Get current settings
            settings = Settings.get_settings()
            
            # Track which fields were updated
            updated_fields = []
            
            # Only update fields that are provided in the request
            for field_name, new_value in data.items():
                if hasattr(settings, field_name) and field_name not in ['created_at', 'updated_at']:
                    old_value = getattr(settings, field_name)
                    setattr(settings, field_name, new_value)
                    if old_value != new_value:
                        updated_fields.append(field_name)
            
            # Save the settings if any fields were updated
            if updated_fields:
                settings.save()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Settings updated successfully',
                    'updated_fields': updated_fields
                })
            else:
                return JsonResponse({
                    'status': 'success',
                    'message': 'No fields were updated'
                })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error', 
                'message': 'Invalid JSON in request'
            }, status=400)
            
        except ValidationError as e:
            return JsonResponse({
                'status': 'error', 
                'message': str(e)
            }, status=400)
            
        except Exception as e:
            return JsonResponse({
                'status': 'error', 
                'message': f'Error updating settings: {str(e)}'
            }, status=500)
