from django.urls import path
from core.views import utils, discovery, dhcp, tftp
from core.views.customers import CustomerView
from core.views.routers import RouterView, RouterInterfaceView  
from core.views.sites import SiteView, SiteRoutingView
from core.views.network_map import NetworkMapView
from core.views.vpns import VPNView, VPNSiteView
from core.views.setup import SetupStatusView, AdminSetupView, SettingsSetupView
from core.views.test import test_view
from core.views.logs import LogsView

urlpatterns = [
    # Test endpoint
    path('test/', test_view, name='test'),

    # Setup endpoints
    path('setup/status/', SetupStatusView.as_view()),
    path('setup/admin/', AdminSetupView.as_view()),
    path('setup/settings/', SettingsSetupView.as_view()),

    # Utility endpoints
    path('utils/host-interfaces/', utils.list_host_interfaces, name='host-interfaces'),

    # Models endpoints
    
    ## Customer endpoints
    path('customers/', CustomerView.as_view()),
    path('customers/<int:customer_id>/', CustomerView.as_view()),

    ## Router endpoints
    path('routers/', RouterView.as_view()),
    path('routers/<str:router_id>/', RouterView.as_view()),
    path('routers/<str:router_id>/interfaces/', RouterInterfaceView.as_view()),
    path('routers/<str:router_id>/interfaces/<int:interface_id>/', RouterInterfaceView.as_view()),

    ## Site endpoints
    path('sites/', SiteView.as_view()),  
    path('sites/<int:site_id>/', SiteView.as_view()),
    path('sites/<int:site_id>/enable-routing/', SiteRoutingView.as_view()),

    # VPN URLs
    path('vpns/', VPNView.as_view(), name='vpn-list-create'),
    path('vpns/<int:vpn_id>/', VPNView.as_view(), name='vpn-detail'),
    path('vpns/<int:vpn_id>/sites/', VPNSiteView.as_view(), name='vpn-site-add'),
    path('vpns/<int:vpn_id>/sites/<int:site_id>/', VPNSiteView.as_view(), name='vpn-site-remove'),

    # DHCP service endpoints
    path('dhcp/start/', dhcp.start_dhcp_server, name='start-dhcp-server'),
    path('dhcp/stop/', dhcp.stop_dhcp_server, name='stop-dhcp-server'),
    path('dhcp/status/', dhcp.dhcp_server_status, name='dhcp-server-status'),
    path('dhcp/leases/', dhcp.dhcp_leases, name='dhcp-leases'),

    ## TFTP service endpoints
    path('tftp/start/', tftp.start_tftp_server, name='start-tftp-server'),
    path('tftp/stop/', tftp.stop_tftp_server, name='stop-tftp-server'),
    path('tftp/status/', tftp.tftp_server_status, name='tftp-server-status'),
    path('tftp/files/', tftp.tftp_files, name='tftp-files'),
    path('tftp/upload/', tftp.upload_file, name='upload-tftp-file'),
    path('tftp/files/<str:filename>/', tftp.delete_file, name='delete-tftp-file'),

    # Network discovery endpoints
    path('network/discover/', discovery.discover_network, name='discover-network'),
    path('network/map/', NetworkMapView.as_view(), name='map_data'),

    # Logs endpoint
    path('logs/', LogsView.as_view(), name='logs'),
]
