from django.urls import path
from core.views import control, utils, settings, discovery, customers, sites, routers, network_map

urlpatterns = [
    # Settings endpoint
    path('settings/', settings.global_settings, name='settings'),

    # Utility endpoints

    path('utils/host-interfaces/', utils.list_host_interfaces, name='host-interfaces'),

    # Models endpoints
    
    ## Customer endpoints
    path('customers/', customers.CustomerView.as_view()),
    path('customers/<int:customer_id>/', customers.CustomerView.as_view()),

    ## Router endpoints
    path('routers/', routers.RouterView.as_view()),
    path('routers/<str:router_id>/', routers.RouterView.as_view()),
    path('routers/<str:router_id>/interfaces/', routers.RouterInterfaceView.as_view()),
    path('routers/<str:router_id>/interfaces/<int:interface_id>/', routers.RouterInterfaceView.as_view()),

    ## Site endpoints
    path('sites/', sites.SiteView.as_view()),  
    path('sites/<int:site_id>/', sites.SiteView.as_view()),
    path('sites/<int:site_id>/assign-interface/', sites.SiteInterfaceView.as_view()),

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
    path('network/map/', network_map.NetworkMapView.as_view(), name='map_data'),
]
