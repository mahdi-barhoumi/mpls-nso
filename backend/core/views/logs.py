import os
import re
from datetime import datetime
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings

@method_decorator(csrf_exempt, name='dispatch')
class LogsView(View):
    def get(self, request):
        try:
            # Get query parameters
            level = request.GET.get('level', '').upper()
            module = request.GET.get('module', '')
            start_date = request.GET.get('start_date', '')
            limit = int(request.GET.get('limit', 1000))

            # Regular expression for log parsing
            log_pattern = r'(?P<level>\w+) (?P<timestamp>[\d-]+ [\d:,]+) \((?P<module>[\w-]+)\): (?P<message>.+)'

            # Get log file path from Django settings
            log_file = settings.BASE_DIR / 'logs/logs.log'

            # Ensure logs directory exists
            log_dir = settings.BASE_DIR / 'logs'
            log_dir.mkdir(exist_ok=True)

            # Create log file if it doesn't exist
            if not log_file.exists():
                log_file.touch()

            logs = []
            try:
                with open(log_file, 'r') as file:
                    # Read lines from the end of file
                    lines = file.readlines()[-limit:]
                    
                    for line in lines:
                        match = re.match(log_pattern, line.strip())
                        if match:
                            log_data = match.groupdict()
                            
                            # Filter by level if specified
                            if level and log_data['level'] != level:
                                continue
                                
                            # Filter by module if specified
                            if module and module.lower() not in log_data['module'].lower():
                                continue
                                
                            # Filter by start date if specified
                            if start_date:
                                log_date = datetime.strptime(log_data['timestamp'].split(',')[0], '%Y-%m-%d %H:%M:%S')
                                start = datetime.strptime(start_date, '%Y-%m-%d')
                                if log_date < start:
                                    continue
                            
                            logs.append({
                                'timestamp': log_data['timestamp'],
                                'level': log_data['level'],
                                'module': log_data['module'],
                                'message': log_data['message']
                            })
                            
            except FileNotFoundError:
                return JsonResponse({
                    'message': 'Log file not found'
                }, status=404)

            return JsonResponse({
                'count': len(logs),
                'logs': logs
            })
            
        except Exception as exception:
            return JsonResponse({
                'message': "Failed getting logs"
            }, status=400)
