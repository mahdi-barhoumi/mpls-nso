from django.http import JsonResponse
from django.views import View
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from core.models import Router, Interface, VRF, OSPFProcess

@method_decorator(csrf_exempt, name='dispatch')
class RouterView(View):
    def get(self, request, router_id=None):
        try:
            if router_id:
                # Single router detail
                routers = [get_object_or_404(Router, id=router_id)]
            else:
                # List all routers
                routers = Router.objects.all()

            router_list = [{
                'id': router.id,
                'reachable': router.reachable,
                'role': router.get_role_display(),
                'hostname': router.hostname,
                'management_ip_address': router.management_ip_address,
                'chassis_id': router.chassis_id,
                'interface_count': router.interfaces.count(),
                'vrf_count': router.vrfs.count(),
                'first_discovered': router.first_discovered.isoformat(),
                'last_discovered': router.last_discovered.isoformat(),
            } for router in routers]
            
            return JsonResponse(router_list if not router_id else router_list[0], safe=False)
        
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class RouterInterfaceView(View):
    def get(self, request, router_id, interface_id=None):
        try:
            router = get_object_or_404(Router, id=router_id)
            
            if interface_id:
                # Single interface detail
                interface = get_object_or_404(Interface, id=interface_id, router=router)
                
                interface_data = {
                    'id': interface.id,
                    'name': interface.name,
                    'enabled': interface.enabled,
                    'description': interface.description,
                    'ip_address': str(interface.ip_address) if interface.ip_address else None,
                    'subnet_mask': str(interface.subnet_mask) if interface.subnet_mask else None,
                    'mac_address': interface.mac_address,
                    'category': interface.category,
                    'addressing': interface.addressing,
                    'type': interface.type,
                    'is_management': interface.is_management_interface,
                    'vrf': interface.vrf.name if interface.vrf else None,
                    'site': interface.site.name if interface.site else None,
                    'is_connected': interface.is_connected,
                    'connected_interfaces': [
                        {'id': conn.id, 'name': conn.name, 'router_id': conn.router.id}
                        for conn in interface.connected_interfaces.all()
                    ]
                }
                
                return JsonResponse(interface_data)
            else:
                # List all interfaces for router
                interfaces = router.interfaces.all()
                
                interface_list = [{
                    'id': interface.id,
                    'name': interface.name,
                    'enabled': interface.enabled,
                    'description': interface.description,
                    'category': interface.category,
                    'addressing': interface.addressing,
                    'type': interface.type,
                    'is_management': interface.is_management_interface,
                    'ip_address': str(interface.ip_address) if interface.ip_address else None,
                    'subnet_mask': str(interface.subnet_mask) if interface.subnet_mask else None,
                    'mac_address': interface.mac_address,
                    'vrf': interface.vrf.name if interface.vrf else None,
                    'site': interface.site.name if interface.site else None,
                    'is_connected': interface.is_connected,
                    'connected_interfaces': [
                        {'id': conn.id, 'name': conn.name, 'router_id': conn.router.id}
                        for conn in interface.connected_interfaces.all()
                    ]
                } for interface in interfaces]
                
                response_data = {
                    'count': len(interface_list),
                    'interfaces': interface_list
                }
                
                return JsonResponse(response_data)
        
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class RouterVRFView(View):
    def get(self, request, router_id, vrf_id=None):
        try:
            router = get_object_or_404(Router, id=router_id)
            
            if vrf_id:
                # Single VRF detail
                vrf = get_object_or_404(VRF, id=vrf_id, router=router)
                
                vrf_data = {
                    'id': vrf.id,
                    'name': vrf.name,
                    'route_distinguisher': vrf.route_distinguisher,
                    'import_targets': list(vrf.import_targets),
                    'export_targets': list(vrf.export_targets),
                    'interface_count': vrf.interfaces.count(),
                    'site': vrf.site.name if hasattr(vrf, 'site') and vrf.site else None
                }
                
                return JsonResponse(vrf_data)
            else:
                # List all VRFs for router
                vrfs = router.vrfs.all()
                
                vrf_list = [{
                    'id': vrf.id,
                    'name': vrf.name,
                    'route_distinguisher': vrf.route_distinguisher,
                    'import_targets': list(vrf.import_targets),
                    'export_targets': list(vrf.export_targets),
                    'interface_count': vrf.interfaces.count(),
                    'site': vrf.site.name if hasattr(vrf, 'site') and vrf.site else None
                } for vrf in vrfs]
                
                response_data = {
                    'count': len(vrf_list),
                    'vrfs': vrf_list
                }
                
                return JsonResponse(response_data)
        
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class RouterOSPFView(View):
    def get(self, request, router_id, process_id=None):
        try:
            router = get_object_or_404(Router, id=router_id)
            
            if process_id:
                # Single OSPF process detail
                ospf = get_object_or_404(OSPFProcess, id=process_id, router=router)
                
                ospf_data = {
                    'id': ospf.id,
                    'process_id': ospf.process_id,
                    'ospf_router_id': ospf.ospf_router_id,
                    'priority': ospf.priority,
                    'vrf': ospf.vrf.name if ospf.vrf else None,
                    'networks': [{
                        'id': network.id,
                        'area': network.area,
                        'network': network.network,
                        'subnet_mask': network.subnet_mask
                    } for network in ospf.networks.all()]
                }
                
                return JsonResponse(ospf_data)
            else:
                # List all OSPF processes for router
                processes = router.processes.all()
                
                process_list = [{
                    'id': ospf.id,
                    'process_id': ospf.process_id,
                    'ospf_router_id': ospf.ospf_router_id,
                    'priority': ospf.priority,
                    'vrf': ospf.vrf.name if ospf.vrf else None,
                    'network_count': ospf.networks.count()
                } for ospf in processes]
                
                response_data = {
                    'count': len(process_list),
                    'processes': process_list
                }
                
                return JsonResponse(response_data)
        
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)
