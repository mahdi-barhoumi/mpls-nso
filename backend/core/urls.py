from django.urls import path
from core.views.dhcp import *
from core.views.tftp import *
from core.views.utils import *
from core.views.settings import *
from core.views.discovery import *
from core.views.interface_control import *

urlpatterns = [
    # Settings endpoint
    path('settings/', global_settings, name='settings'),

    # Utility endpoints
    path('utils/host-interfaces/', list_host_interfaces, name='host-interfaces'),

    # DHCP service endpoints
    path('dhcp/start/', start_dhcp_server, name='start-dhcp-server'),
    path('dhcp/stop/', stop_dhcp_server, name='stop-dhcp-server'),
    path('dhcp/status/', dhcp_server_status, name='dhcp-server-status'),
    path('dhcp/leases/', dhcp_leases, name='dhcp-leases'),

    # TFTP service endpoints
    path('tftp/start/', start_tftp_server, name='start-tftp-server'),
    path('tftp/stop/', stop_tftp_server, name='stop-tftp-server'),
    path('tftp/status/', tftp_server_status, name='tftp-server-status'),
    path('tftp/files/', tftp_files, name='tftp-files'),
    path('tftp/upload/', upload_file, name='upload-tftp-file'),
    path('tftp/files/<str:filename>', delete_file, name='delete-tftp-file'),

    # Network discovery service endpoints
    path('network/discover/', discover_network, name='discover-network'),

    # Interface control endpoints
    path('interfaces/connect/', connect_routers, name='connect-router'),
    path('interfaces/list/', list_interfaces, name='list-interfaces'),
    path('interface/<str:interface_name>/', get_interface, name='get-interface'),
    path('interface/<str:interface_name>/enable/', enable_interface, name='enable-interface'),
    path('interface/<str:interface_name>/disable/', disable_interface, name='disable-interface'),
    path('interfaces/all/enable/', enable_all_interfaces, name='enable-all-interfaces'),
    path('interfaces/all/disable/', disable_all_interfaces, name='disable-all-interfaces'),


]
