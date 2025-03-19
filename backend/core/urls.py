from django.urls import path
from core.views.dhcp import *
from core.views.tftp import *
from core.views.discovery import *
from core.views.interface_control import *

urlpatterns = [
    # DHCP service endpoints
    path('dhcp/start/', start_dhcp_server, name='start_dhcp_server'),
    path('dhcp/stop/', stop_dhcp_server, name='stop_dhcp_server'),
    path('dhcp/status/', dhcp_server_status, name='dhcp_server_status'),
    path('dhcp/leases/', dhcp_leases, name='dhcp_leases'),

    # TFTP service endpoints
    path('tftp/start/', start_tftp_server, name='start_tftp_server'),
    path('tftp/stop/', stop_tftp_server, name='stop_tftp_server'),
    path('tftp/status/', tftp_server_status, name='tftp_server_status'),
    path('tftp/files/', tftp_files, name='tftp_files'),
    path('tftp/upload/', upload_file, name='upload_tftp_file'),
    path('tftp/files/<str:filename>', delete_file, name='delete_tftp_file'),

    # Network discovery service endpoints
    path('network/discover/', discover_network, name='get_network_map'),

    # Interface control endpoints
    path('interfaces/connect/', connect_routers, name='connect-router'),
    path('interfaces/list/', list_interfaces, name='list-interfaces'),
    path('interface/<str:interface_name>/', get_interface, name='get-interface'),
    path('interface/<str:interface_name>/enable/', enable_interface, name='enable-interface'),
    path('interface/<str:interface_name>/disable/', disable_interface, name='disable-interface'),
    path('interfaces/all/enable/', enable_all_interfaces, name='enable_all_interfaces'),
    path('interfaces/all/disable/', disable_all_interfaces, name='disable_all_interfaces'),


]
