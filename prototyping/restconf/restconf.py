import json
import requests
from requests.auth import HTTPBasicAuth

requests.packages.urllib3.disable_warnings()

ip = "192.168.100.100"
username = "mgmt"
password = "mgmtapp"
method = "GET"
container = "Cisco-IOS-XE-lldp-oper:lldp-entries"
leaf = ""
headers = {
    'accept': "application/yang-data+json",
    'content-type': "application/yang-data+json"
}
payload = ""

url = f"https://{ip}/restconf/data/{container}/{leaf}"

response = requests.request(method, url, auth=(username, password), headers=headers, verify=False, data=payload)

with open('response-data.json', 'w') as file:
    json.dump(response.json(), file, sort_keys=True, indent=4)