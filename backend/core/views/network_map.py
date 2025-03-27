from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from core.models import Router, Interface, VRF


class NetworkMapView(View):
    """
    A comprehensive view that handles both network topology visualization
    and detailed router information based on the request.
    """

    @method_decorator(cache_page(60 * 5))  # Cache for 5 minutes
    def get(self, request, chassis_id=None):
        if chassis_id:
            return self.get_router_details(request, chassis_id)
        return self.get_network_map(request)

    def get_network_map(self, request):
        """
        Returns network topology data for visualization.
        """
        # Get query parameters for filtering
        customer_id = request.GET.get('customer_id')
        vpn_id = request.GET.get('vpn_id')
        site_id = request.GET.get('site_id')
        roles = request.GET.getlist('role')  # Multiple roles can be selected
        include_p_routers = request.GET.get('include_p', 'true').lower() == 'true'
        include_interfaces = request.GET.get('include_interfaces', 'true').lower() == 'true'

        # Start with all routers
        routers = Router.objects.all()

        # Apply filters
        if customer_id:
            customer_router_ids = VRF.objects.filter(customer_id=customer_id).values_list('router__chassis_id', flat=True)
            pe_router_ids = []
            for router in Router.objects.filter(chassis_id__in=customer_router_ids, role='CE'):
                for interface in router.interfaces.all():
                    for connected in interface.connected_interfaces.all():
                        if connected.router.role == 'PE':
                            pe_router_ids.append(connected.router.chassis_id)
            router_ids = list(customer_router_ids) + pe_router_ids
            routers = routers.filter(chassis_id__in=router_ids)

        if vpn_id:
            vpn_router_ids = VRF.objects.filter(vpn_id=vpn_id).values_list('router__chassis_id', flat=True)
            routers = routers.filter(chassis_id__in=vpn_router_ids)

        if site_id:
            site_routers = Interface.objects.filter(site_id=site_id).values_list('router__chassis_id', flat=True)
            routers = routers.filter(chassis_id__in=site_routers)

        if roles:
            routers = routers.filter(role__in=roles)
        elif not include_p_routers:
            routers = routers.exclude(role='P')

        # Prefetch related interfaces with their connections
        routers = routers.prefetch_related(
            'interfaces__connected_interfaces',
            'vrfs__vpn__customer'  # Correctly traverse through vpn to customer
        )

        # Create nodes and links data structures
        nodes = []
        links = []
        processed_interfaces = set()

        for router in routers:
            node = {
                'id': router.chassis_id,
                'type': 'router',
                'label': router.hostname,
                'role': router.role,
                'ip': router.management_ip_address,
                'vrfs': [{'name': vrf.name,
                          'rd': vrf.route_distinguisher,
                          'vpn': vrf.vpn.name if vrf.vpn else None}
                         for vrf in router.vrfs.all()]
            }
            interface_count = router.interfaces.count()
            connected_count = router.interfaces.filter(connected_interfaces__isnull=False).count()
            node['interface_counts'] = {
                'total': interface_count,
                'connected': connected_count
            }
            nodes.append(node)

            for interface in router.interfaces.all():
                for connected in interface.connected_interfaces.all():
                    link_id = f"{min(interface.id, connected.id)}-{max(interface.id, connected.id)}"
                    if link_id not in processed_interfaces and connected.router in routers:
                        link = {
                            'id': link_id,
                            'source': router.chassis_id,
                            'target': connected.router.chassis_id,
                            'sourceInterface': interface.id,
                            'targetInterface': connected.id,
                            'sourceInterfaceName': interface.name,
                            'targetInterfaceName': connected.name,
                            'sourceVrf': interface.vrf.name if interface.vrf else None,
                            'targetVrf': connected.vrf.name if connected.vrf else None,
                        }
                        if include_interfaces:
                            link['sourceInterfaceDetails'] = {
                                'id': interface.id,
                                'name': interface.name,
                                'admin_status': interface.admin_status,
                                'oper_status': interface.oper_status,
                                'ip_address': interface.ip_address,
                                'subnet_mask': interface.subnet_mask,
                                'mac_address': interface.mac_address,
                                'description': interface.description,
                                'site': interface.site.name if interface.site else None
                            }
                            link['targetInterfaceDetails'] = {
                                'id': connected.id,
                                'name': connected.name,
                                'admin_status': connected.admin_status,
                                'oper_status': connected.oper_status,
                                'ip_address': connected.ip_address,
                                'subnet_mask': connected.subnet_mask,
                                'mac_address': connected.mac_address,
                                'description': connected.description,
                                'site': connected.site.name if connected.site else None
                            }
                        links.append(link)
                        processed_interfaces.add(link_id)

        response_data = {
            'nodes': nodes,
            'links': links,
            'metadata': {
                'router_count': len(nodes),
                'link_count': len(links),
                'filters': {
                    'customer_id': customer_id,
                    'vpn_id': vpn_id,
                    'site_id': site_id,
                    'roles': roles,
                    'include_p_routers': include_p_routers,
                    'include_interfaces': include_interfaces
                }
            }
        }
        return JsonResponse(response_data)

    def get_router_details(self, request, chassis_id):
        """
        Returns detailed information about a specific router.
        """
        try:
            router = Router.objects.prefetch_related(
                'interfaces__connected_interfaces__router',
                'vrfs__customer',
                'vrfs__vpn',
                'vrfs__route_targets'
            ).get(chassis_id=chassis_id)

            interfaces_data = []
            for interface in router.interfaces.all():
                connected_to = []
                for connected in interface.connected_interfaces.all():
                    connected_to.append({
                        'router_id': connected.router.chassis_id,
                        'router_name': connected.router.hostname,
                        'interface_id': connected.id,
                        'interface_name': connected.name,
                        'router_role': connected.router.role
                    })
                interfaces_data.append({
                    'id': interface.id,
                    'name': interface.name,
                    'admin_status': interface.admin_status,
                    'oper_status': interface.oper_status,
                    'ip_address': interface.ip_address,
                    'subnet_mask': interface.subnet_mask,
                    'mac_address': interface.mac_address,
                    'description': interface.description,
                    'vrf': interface.vrf.name if interface.vrf else None,
                    'site': interface.site.name if interface.site else None,
                    'connected_to': connected_to
                })

            vrfs_data = []
            for vrf in router.vrfs.all():
                vrfs_data.append({
                    'id': vrf.id,
                    'name': vrf.name,
                    'route_distinguisher': vrf.route_distinguisher,
                    'customer': vrf.customer.name if vrf.customer else None,
                    'vpn': vrf.vpn.name if vrf.vpn else None,
                    'import_targets': list(vrf.import_targets),
                    'export_targets': list(vrf.export_targets),
                    'interface_count': vrf.interfaces.count()
                })

            response_data = {
                'chassis_id': router.chassis_id,
                'hostname': router.hostname,
                'role': router.role,
                'management_ip': router.management_ip_address,
                'last_discovered': router.last_discovered,
                'interfaces': interfaces_data,
                'vrfs': vrfs_data
            }
            return JsonResponse(response_data)

        except Router.DoesNotExist:
            return JsonResponse({'error': 'Router not found'}, status=404)