from ncclient import manager
import subprocess
import ipaddress
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

# Replace the subnet range with the desired subnet
subnet = '192.168.181.0/24'
# Use the NETCONF port for your devices
port = 22
# Use the user credentials for your devices
username = 'mgmt'
password = 'mgmtapp'


def ping(ip):
    result = subprocess.run(['ping', '-n', '2', str(ip)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.returncode == 0


def check_netconf(ip):
    try:
        with manager.connect(host=ip, port=port, username=username, password=password, hostkey_verify=False, device_params={'name': 'default'}, timeout=3) as m:
            # Get device capabilities
            capabilities = list(m.server_capabilities)
            return {
                'ip': ip,
                'status': 'NETCONF enabled',
                'capabilities': capabilities,
            }
    except Exception as e:
        return {'ip': ip, 'status': f"Error: {str(e)}"}


def discover_devices(subnet):
    devices = []
    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(discover_device, str(ip)) for ip in ipaddress.IPv4Network(subnet)]
        for future in futures:
            result = future.result()
            if result and result['status'] == 'NETCONF enabled':
                devices.append(result)
    return devices


def discover_device(ip):
    if ping(ip):
        return check_netconf(ip)
    return None


def main():
    discovered_devices = discover_devices(subnet)
    print("Discovered devices:")
    for device in discovered_devices:
        print(device)


if __name__ == '__main__':
    sys.exit(main())
