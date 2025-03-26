import os
import logging
from django.apps import apps
from core.modules.dhcp import DHCPServer
from core.modules.tftp import TFTPServer
from core.settings import get_settings

class _NetworkController:
    def __init__(self):
        self.logger = logging.getLogger('network-controller')
        self.dhcp_server = DHCPServer()
        self.tftp_server = TFTPServer()
        self.start_dhcp_server()

    def start_dhcp_server(self):
        # Ensure settings are loaded
        settings = get_settings()
        if not settings:
            self.logger.warning("Cannot start DHCP server: No system settings found")
            return False

        try:
            # Start DHCP server with settings
            return self.dhcp_server.start(
                server_ip=settings.host_address,
                tftp_server_ip=settings.host_address,
                main_scope_address=settings.dhcp_provider_network_address,
                main_scope_subnet_mask=settings.dhcp_provider_network_subnet_mask,
                lease_time=settings.dhcp_lease_time
            )
        except Exception as e:
            self.logger.error(f"DHCP server start failed: {e}")
            return False

    def stop_dhcp_server(self):
        try:
            return self.dhcp_server.stop()
        except Exception as e:
            self.logger.error(f"DHCP server stop failed: {e}")
            return False

    def get_dhcp_server_status(self):
        return self.dhcp_server.get_status()

    def get_active_dhcp_leases(self):
        return self.dhcp_server.get_active_leases()

    def start_tftp_server(self, server_ip=None, max_block_size=512):
        settings = get_settings()
        if not server_ip and settings:
            server_ip = settings.host_address

        if not server_ip:
            self.logger.error("Cannot start TFTP server: No server IP provided")
            return False

        try:
            return self.tftp_server.start(
                root_dir=os.path.join(apps.get_app_config('core').path, 'data\\tftp-files'),
                server_ip=server_ip,
                port=69,
                max_block_size=max_block_size
            )
        except Exception as e:
            self.logger.error(f"TFTP server start failed: {e}")
            return False

    def stop_tftp_server(self):
        try:
            return self.tftp_server.stop()
        except Exception as e:
            self.logger.error(f"TFTP server stop failed: {e}")
            return False

    def get_tftp_server_status(self):
        return self.tftp_server.get_status()

    def get_tftp_files_list(self):
        return self.tftp_server.get_files_list()

    def is_tftp_server_running(self):
        return self.tftp_server.is_running()

    def upload_tftp_file(self, uploaded_file):
        if not self.is_tftp_server_running():
            raise Exception('TFTP server is not running')

        if not self.tftp_server.root_dir:
            raise Exception('TFTP server root directory not set')

        filename = uploaded_file.name
        file_path = os.path.join(self.tftp_server.root_dir, filename)

        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        return filename

    def delete_tftp_file(self, filename):
        if not self.is_tftp_server_running():
            raise Exception('TFTP server is not running')

        if not self.tftp_server.root_dir:
            raise Exception('TFTP server root directory not set')

        file_path = os.path.realpath(os.path.normpath(os.path.join(self.tftp_server.root_dir, filename)))

        if not file_path.startswith(self.tftp_server.root_dir):
            raise Exception('Access denied')

        if not os.path.exists(file_path):
            raise Exception(f'File {filename} not found')

        os.remove(file_path)
        return filename

NetworkController = _NetworkController()
