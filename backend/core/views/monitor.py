from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, F, Count
from core.models import Router, Interface, RouterMetric, InterfaceMetric, Site, Customer
from core.modules.monitor import NetworkMonitor

@method_decorator(csrf_exempt, name='dispatch')
class RouterMetricsView(View):
    def get(self, request, router_id=None):
        try:
            # Get time range from query params, default to last 24 hours
            hours = int(request.GET.get('hours', 24))
            since = timezone.now() - timedelta(hours=hours)

            if router_id:
                # Get metrics for specific router
                router = get_object_or_404(Router, id=router_id)
                metrics = RouterMetric.objects.filter(
                    router=router,
                    timestamp__gte=since
                ).order_by('timestamp')

                metrics_data = [{
                    'id': metric.id,
                    'router_id': router.id,
                    'hostname': router.hostname,
                    'timestamp': metric.timestamp.isoformat(),
                    'cpu_usage_5s': metric.cpu_usage_5s or 0,
                    'cpu_usage_1m': metric.cpu_usage_1m or 0,
                    'cpu_usage_5m': metric.cpu_usage_5m or 0,
                    'mem_used_percent': metric.mem_used_percent or 0,
                    'mem_total': metric.mem_total or 0,
                    'mem_used': metric.mem_used or 0,
                    'mem_free': metric.mem_free or 0,
                    'storage_used_percent': metric.storage_used_percent or 0,
                    'storage_total': metric.storage_total or 0,
                    'storage_used': metric.storage_used or 0,
                    'storage_free': metric.storage_free or 0
                } for metric in metrics]

                return JsonResponse(metrics_data, safe=False)
            else:
                # Get latest metrics for all routers
                latest_metrics = []
                for router in Router.objects.all():
                    latest_metric = RouterMetric.objects.filter(router=router).order_by('-timestamp').first()
                    if latest_metric:
                        latest_metrics.append({
                            'id': latest_metric.id,
                            'router_id': router.id,
                            'hostname': router.hostname,
                            'timestamp': latest_metric.timestamp.isoformat(),
                            'cpu_usage_5s': latest_metric.cpu_usage_5s or 0,
                            'cpu_usage_1m': latest_metric.cpu_usage_1m or 0,
                            'cpu_usage_5m': latest_metric.cpu_usage_5m or 0,
                            'mem_used_percent': latest_metric.mem_used_percent or 0,
                            'mem_total': latest_metric.mem_total or 0,
                            'mem_used': latest_metric.mem_used or 0,
                            'mem_free': latest_metric.mem_free or 0,
                            'storage_used_percent': latest_metric.storage_used_percent or 0,
                            'storage_total': latest_metric.storage_total or 0,
                            'storage_used': latest_metric.storage_used or 0,
                            'storage_free': latest_metric.storage_free or 0
                        })

                return JsonResponse(latest_metrics, safe=False)

        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class InterfaceMetricsView(View):
    def get(self, request, interface_id=None):
        try:
            # Get time range from query params, default to last 24 hours
            hours = int(request.GET.get('hours', 24))
            since = timezone.now() - timedelta(hours=hours)

            if interface_id:
                # Get metrics for specific interface
                interface = get_object_or_404(Interface, id=interface_id)
                metrics = InterfaceMetric.objects.filter(
                    interface=interface,
                    timestamp__gte=since
                ).order_by('timestamp')

                metrics_data = [{
                    'timestamp': metric.timestamp.isoformat(),
                    'operational_status': metric.operational_status,
                    'in_octets': metric.in_octets,
                    'out_octets': metric.out_octets,
                    'in_errors': metric.in_errors,
                    'out_errors': metric.out_errors,
                    'in_discards': metric.in_discards,
                    'out_discards': metric.out_discards,
                    'bps_in': metric.bps_in,
                    'bps_out': metric.bps_out
                } for metric in metrics]

                return JsonResponse(metrics_data, safe=False)
            else:
                # Get latest metrics for all interfaces
                latest_metrics = []
                for interface in Interface.objects.select_related('router').all():
                    latest_metric = InterfaceMetric.objects.filter(interface=interface).order_by('-timestamp').first()
                    if latest_metric:
                        latest_metrics.append({
                            'interface_id': interface.id,
                            'name': interface.name,
                            'router_id': interface.router.id,
                            'router_hostname': interface.router.hostname,
                            'timestamp': latest_metric.timestamp.isoformat(),
                            'operational_status': latest_metric.operational_status,
                            'in_octets': latest_metric.in_octets,
                            'out_octets': latest_metric.out_octets,
                            'in_errors': latest_metric.in_errors,
                            'out_errors': latest_metric.out_errors,
                            'in_discards': latest_metric.in_discards,
                            'out_discards': latest_metric.out_discards,
                            'bps_in': latest_metric.bps_in,
                            'bps_out': latest_metric.bps_out
                        })

                return JsonResponse(latest_metrics, safe=False)

        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class DashboardStatsView(View):
    def get(self, request):
        try:
            # Get summary stats for the dashboard
            total_routers = Router.objects.count()
            reachable_routers = Router.objects.filter(reachable=True).count()
            total_interfaces = Interface.objects.count()
            enabled_interfaces = Interface.objects.filter(enabled=True).count()

            # Get routers with high resource usage
            high_cpu_routers = []
            high_memory_routers = []
            high_storage_routers = []

            for router in Router.objects.all():
                latest_metric = RouterMetric.objects.filter(router=router).order_by('-timestamp').first()
                if latest_metric:
                    if latest_metric.cpu_usage_5m >= 70:  # CPU threshold
                        high_cpu_routers.append({
                            'id': router.id,
                            'hostname': router.hostname,
                            'usage': latest_metric.cpu_usage_5m
                        })
                    if latest_metric.mem_used_percent >= 80:  # Memory threshold
                        high_memory_routers.append({
                            'id': router.id,
                            'hostname': router.hostname,
                            'usage': latest_metric.mem_used_percent
                        })
                    if latest_metric.storage_used_percent >= 80:  # Storage threshold
                        high_storage_routers.append({
                            'id': router.id,
                            'hostname': router.hostname,
                            'usage': latest_metric.storage_used_percent
                        })

            return JsonResponse({
                'total_routers': total_routers,
                'reachable_routers': reachable_routers,
                'total_interfaces': total_interfaces,
                'enabled_interfaces': enabled_interfaces,
                'high_cpu_routers': high_cpu_routers,
                'high_memory_routers': high_memory_routers,
                'high_storage_routers': high_storage_routers
            })

        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class RouterInfoView(View):
    def get(self, request, router_id):
        try:
            router = get_object_or_404(Router, id=router_id)
            
            if not router.reachable:
                return JsonResponse({
                    'message': 'Router is not reachable'
                }, status=404)
            
            device_info = NetworkMonitor.get_device_info(router)
            
            if device_info:
                return JsonResponse(device_info)
            else:
                return JsonResponse({
                    'message': 'Failed to retrieve device information'
                }, status=500)
                
        except Exception as e:
            return JsonResponse({
                'message': str(e)
            }, status=500)