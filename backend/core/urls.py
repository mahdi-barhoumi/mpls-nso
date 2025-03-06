from django.urls import path
from core.views.dhcp import *
from core.views.tftp import *
from core.views.mapper import *

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

    # Network mapper endpoints
    path('network/discover/', discover_network, name='get_network_map'),
]