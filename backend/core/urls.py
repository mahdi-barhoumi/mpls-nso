from django.urls import path
from core.views import control, utils, settings, discovery, customers, sites, routers,network_map 


urlpatterns = [
    # Settings endpoint
    path('settings/', settings.global_settings, name='settings'),

    # Utility endpoints

    path('utils/host-interfaces/', utils.list_host_interfaces, name='host-interfaces'),

    # Models endpoints
    path('sites/', sites.list_sites, name='list-sites'),
    path('sites/create/', sites.create_site, name='create-site'),
    path('sites/<int:site_id>/', sites.get_site, name='get-site'),
    path('customers/', customers.list_customers, name='list-customers'),
    path('customers/create/', customers.create_customer, name='create-customer'),
    path('customers/<int:customer_id>/', customers.get_customer, name='get-customer'),
    path('routers/', routers.list_routers, name='list-routers'),
    path('routers/<str:router_id>/', routers.get_router, name='get-router'),
    path('routers/<str:router_id>/interfaces/', routers.list_router_interfaces, name='list-router-interfaces'),
    path('routers/<str:router_id>/interfaces/<int:interface_id>/', routers.get_router_interface, name='get-router-interface'),

    # Controller endpoints
    ## DHCP service endpoints
    path('control/dhcp/start/', control.start_dhcp_server, name='start-dhcp-server'),
    path('control/dhcp/stop/', control.stop_dhcp_server, name='stop-dhcp-server'),
    path('control/dhcp/status/', control.dhcp_server_status, name='dhcp-server-status'),
    path('control/dhcp/leases/', control.dhcp_leases, name='dhcp-leases'),

    ## TFTP service endpoints
    path('control/tftp/start/', control.start_tftp_server, name='start-tftp-server'),
    path('control/tftp/stop/', control.stop_tftp_server, name='stop-tftp-server'),
    path('control/tftp/status/', control.tftp_server_status, name='tftp-server-status'),
    path('control/tftp/files/', control.tftp_files, name='tftp-files'),
    path('control/tftp/upload/', control.upload_file, name='upload-tftp-file'),
    path('control/tftp/files/<str:filename>', control.delete_file, name='delete-tftp-file'),

    # Network discovery endpoints
    path('network/discover/', discovery.discover_network, name='discover-network'),
    path('network/map/', NetworkMapView.as_view(), name='map_data'),
    path('network/map/<str:chassis_id>/', NetworkMapDetailView.as_view(), name='router_detail_data'),
]
