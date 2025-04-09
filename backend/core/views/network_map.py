from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from core.models import Router, Interface

class NetworkMapView(View):
    """Network topology view that provides data for frontend visualization."""

    @method_decorator(cache_page(60 * 5))  # Cache for 5 minutes
    def get(self, request):
        # Get all routers with their interfaces
        routers = Router.objects.prefetch_related(
            'interfaces__connected_interfaces',
            'vrfs'
        ).all()
        nodes = []
        links = []
        processed_links = set()

        # Create nodes and links
        for router in routers:
            # Add router as a node
            nodes.append({
                'id': router.id,
                'hostname': router.hostname,
                'role': router.role,
                'chassis_id': router.chassis_id,
                'management_ip': router.management_ip_address
            })

            # Process interfaces and create links
            for interface in router.interfaces.all():
                for connected in interface.connected_interfaces.all():
                    # Create unique link ID using interface IDs
                    link_id = f"{min(interface.id, connected.id)}-{max(interface.id, connected.id)}"
                    
                    # Skip if we've already processed this link
                    if link_id in processed_links:
                        continue

                    # Add link with interface details
                    links.append({
                        'id': link_id,
                        'source': router.id,
                        'target': connected.router.id,
                        'sourceInterface': interface.id,
                        'targetInterface': connected.id,
                        'sourceInterfaceName': interface.name,
                        'targetInterfaceName': connected.name,
                        'sourceInterfaceDetails': {
                            'ip_address': interface.ip_address,
                            'subnet_mask': interface.subnet_mask,
                            'category': interface.category
                        },
                        'targetInterfaceDetails': {
                            'ip_address': connected.ip_address,
                            'subnet_mask': connected.subnet_mask,
                            'category': connected.category
                        }
                    })
                    processed_links.add(link_id)

        return JsonResponse({
            'nodes': nodes,
            'links': links
        })