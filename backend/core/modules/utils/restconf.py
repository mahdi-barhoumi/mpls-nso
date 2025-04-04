import requests
import json
import logging
import time
from requests.auth import HTTPBasicAuth
from core.settings import get_settings

requests.packages.urllib3.disable_warnings()

class RestconfWrapper:
    def __init__(self, username=None, password=None, max_retries=3, timeout=10, verify_ssl=False, auto_save=True):
        settings = get_settings()
        self.username = username if username else settings.restconf_username
        self.password = password if password else settings.restconf_password
        self.max_retries = max_retries
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.auto_save = auto_save  # Auto-save enabled by default
        self.logger = logging.getLogger('restconf')
        self.auth = HTTPBasicAuth(self.username, self.password)
        self.headers = {
            'Accept': 'application/yang-data+json',
            'Content-Type': 'application/yang-data+json'
        }
    
    def get(self, ip_address, path):
        url = f"https://{ip_address}/restconf/data/{path}"
        
        for attempt in range(self.max_retries):
            try:
                self.logger.debug(f"GET {url} (attempt {attempt + 1}/{self.max_retries})")
                
                response = requests.get(
                    url,
                    headers=self.headers,
                    auth=self.auth,
                    verify=self.verify_ssl,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 204:
                    # No content, return empty dict
                    self.logger.debug(f"No content (204) from {url}")
                    return {}
                elif response.status_code == 404:
                    # Not found, return None
                    self.logger.debug(f"Resource not found (404) at {url}")
                    return None
                else:
                    self.logger.warning(f"Failed to get data from {url}: HTTP {response.status_code}")
                    if attempt == self.max_retries - 1:
                        return None
            except requests.exceptions.Timeout:
                self.logger.warning(f"Timeout connecting to {url}")
                if attempt == self.max_retries - 1:
                    return None
            except requests.exceptions.ConnectionError:
                self.logger.warning(f"Connection error for {url}")
                if attempt == self.max_retries - 1:
                    return None
            except Exception as e:
                self.logger.error(f"Error getting data from {url}: {str(e)}")
                if attempt == self.max_retries - 1:
                    return None
            
            # Constant backoff instead of exponential
            self.logger.debug("Retrying in 1 second")
            time.sleep(1)
        
        return None
    
    def post(self, ip_address, path, data):
        url = f"https://{ip_address}/restconf/data/{path}"
        
        for attempt in range(self.max_retries):
            try:
                self.logger.debug(f"POST {url} (attempt {attempt + 1}/{self.max_retries})")
                
                response = requests.post(
                    url,
                    headers=self.headers,
                    auth=self.auth,
                    verify=self.verify_ssl,
                    timeout=self.timeout,
                    json=data
                )
                
                if response.status_code in [200, 201, 204]:
                    # Success - return response content if any, otherwise empty dict
                    result = {}
                    try:
                        result = response.json()
                    except ValueError:
                        pass
                    
                    # Auto-save if enabled
                    if self.auto_save:
                        self.save(ip_address)
                        
                    return result
                else:
                    self.logger.warning(f"Failed to POST data to {url}: HTTP {response.status_code}")
                    if attempt == self.max_retries - 1:
                        return None
            except requests.exceptions.Timeout:
                self.logger.warning(f"Timeout connecting to {url}")
                if attempt == self.max_retries - 1:
                    return None
            except requests.exceptions.ConnectionError:
                self.logger.warning(f"Connection error for {url}")
                if attempt == self.max_retries - 1:
                    return None
            except Exception as e:
                self.logger.error(f"Error posting data to {url}: {str(e)}")
                if attempt == self.max_retries - 1:
                    return None
            
            # Constant backoff
            self.logger.debug("Retrying in 1 second")
            time.sleep(1)
        
        return None
    
    def patch(self, ip_address, path, data):
        url = f"https://{ip_address}/restconf/data/{path}"
        
        for attempt in range(self.max_retries):
            try:
                self.logger.debug(f"PATCH {url} (attempt {attempt + 1}/{self.max_retries})")

                response = requests.patch(
                    url,
                    headers=self.headers,
                    auth=self.auth,
                    verify=self.verify_ssl,
                    timeout=self.timeout,
                    json=data
                )
                
                if response.status_code in [200, 204]:
                    # Success - return response content if any, otherwise empty dict
                    result = {}
                    try:
                        result = response.json()
                    except ValueError:
                        pass
                    
                    # Auto-save if enabled
                    if self.auto_save:
                        self.save(ip_address)
                        
                    return result
                else:
                    self.logger.warning(f"Failed to PATCH data at {url}: HTTP {response.status_code}")
                    if attempt == self.max_retries - 1:
                        return None
            except requests.exceptions.Timeout:
                self.logger.warning(f"Timeout connecting to {url}")
                if attempt == self.max_retries - 1:
                    return None
            except requests.exceptions.ConnectionError:
                self.logger.warning(f"Connection error for {url}")
                if attempt == self.max_retries - 1:
                    return None
            except Exception as e:
                self.logger.error(f"Error patching data at {url}: {str(e)}")
                if attempt == self.max_retries - 1:
                    return None
            
            # Constant backoff
            self.logger.debug("Retrying in 1 second")
            time.sleep(1)
        
        return None
    
    def delete(self, ip_address, path):
        url = f"https://{ip_address}/restconf/data/{path}"
        
        for attempt in range(self.max_retries):
            try:
                self.logger.debug(f"DELETE {url} (attempt {attempt + 1}/{self.max_retries})")
                
                response = requests.delete(
                    url,
                    headers=self.headers,
                    auth=self.auth,
                    verify=self.verify_ssl,
                    timeout=self.timeout
                )
                
                if response.status_code in [200, 204]:
                    # Success (no content expected for DELETE)
                    
                    # Auto-save if enabled
                    if self.auto_save:
                        self.save(ip_address)
                        
                    return True
                else:
                    self.logger.warning(f"Failed to DELETE resource at {url}: HTTP {response.status_code}")
                    if attempt == self.max_retries - 1:
                        return False
            except requests.exceptions.Timeout:
                self.logger.warning(f"Timeout connecting to {url}")
                if attempt == self.max_retries - 1:
                    return False
            except requests.exceptions.ConnectionError:
                self.logger.warning(f"Connection error for {url}")
                if attempt == self.max_retries - 1:
                    return False
            except Exception as e:
                self.logger.error(f"Error deleting resource at {url}: {str(e)}")
                if attempt == self.max_retries - 1:
                    return False
            
            # Constant backoff
            self.logger.debug("Retrying in 1 second")
            time.sleep(1)
        
        return False
    
    def put(self, ip_address, path, data):
        url = f"https://{ip_address}/restconf/data/{path}"
        
        for attempt in range(self.max_retries):
            try:
                self.logger.debug(f"PUT {url} (attempt {attempt + 1}/{self.max_retries})")
                
                response = requests.put(
                    url,
                    headers=self.headers,
                    auth=self.auth,
                    verify=self.verify_ssl,
                    timeout=self.timeout,
                    json=data
                )

                if response.status_code in [200, 201, 204]:
                    # Success - return response content if any, otherwise empty dict
                    result = {}
                    try:
                        result = response.json()
                    except ValueError:
                        pass
                    
                    # Auto-save if enabled
                    if self.auto_save:
                        self.save(ip_address)
                        
                    return result
                else:
                    self.logger.warning(f"Failed to PUT data to {url}: HTTP {response.status_code}")
                    if attempt == self.max_retries - 1:
                        return None
            except requests.exceptions.Timeout:
                self.logger.warning(f"Timeout connecting to {url}")
                if attempt == self.max_retries - 1:
                    return None
            except requests.exceptions.ConnectionError:
                self.logger.warning(f"Connection error for {url}")
                if attempt == self.max_retries - 1:
                    return None
            except Exception as e:
                self.logger.error(f"Error putting data to {url}: {str(e)}")
                if attempt == self.max_retries - 1:
                    return None
            
            # Constant backoff
            self.logger.debug("Retrying in 1 second")
            time.sleep(1)
        
        return None
    
    def save(self, ip_address):
        url = f"https://{ip_address}/restconf/operations/cisco-ia:save-config"
        
        try:
            self.logger.debug(f"Attempting to save configuration to startup at {ip_address}")
            
            response = requests.post(
                url,
                headers=self.headers,
                auth=self.auth,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            
            if response.status_code == 200:
                self.logger.debug("Configuration saved to startup successfully")
                return True
            else:
                self.logger.warning(f"Failed to save configuration to startup: HTTP {response.status_code}")
                return False
        except requests.exceptions.Timeout:
            self.logger.warning(f"Timeout connecting to {url}")
            return False
        except requests.exceptions.ConnectionError:
            self.logger.warning(f"Connection error for {url}")
            return False
        except Exception as e:
            self.logger.error(f"Error saving configuration to startup: {str(e)}")
            return False
