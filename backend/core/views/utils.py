import re
import subprocess
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

@csrf_exempt
@require_http_methods(["GET"])
def list_host_interfaces(request):
    try:
        # Run netsh command to get interfaces
        result = subprocess.run(
            ['netsh', 'interface', 'ipv4', 'show', 'interfaces'],
            capture_output=True, 
            text=True,
            check=True
        )
        
        # Parse the output to find interface indices, names and states
        output = result.stdout
        interfaces = []
        
        # Skip header lines
        lines = output.splitlines()
        data_lines = []
        for line in lines:
            if re.match(r'^\s*\d+\s+', line):  # Lines starting with a number
                data_lines.append(line)
        
        for line in data_lines:
            # Format from example:
            # 1          75  4294967295  connected     Loopback Pseudo-Interface 1
            match = re.match(r'^\s*(\d+)\s+(\d+)\s+(\d+)\s+(\w+)\s+(.*?)\s*$', line)
            
            if match:
                idx = int(match.group(1))
                metric = int(match.group(2))
                mtu = int(match.group(3))
                state = match.group(4)
                name = match.group(5)
                
                interfaces.append({
                    'id': idx,
                    'name': name,
                    'state': state,
                    'active': state.lower() == 'connected',
                    'metric': metric,
                    'mtu': mtu
                })
        
        # Sort interfaces by ID
        interfaces.sort(key=lambda x: x['id'])
        
        return JsonResponse({
            'status': 'success',
            'interfaces': interfaces
        })
        
    except subprocess.SubprocessError as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to retrieve network interfaces: {str(e)}'
        }, status=500)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Unexpected error: {str(e)}'
        }, status=500)
