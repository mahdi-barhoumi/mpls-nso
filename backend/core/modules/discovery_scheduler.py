import time
import logging
import threading
from typing import Dict
from datetime import datetime, timedelta
from django.utils import timezone
from core.modules.discovery import NetworkDiscoverer

class _DiscoveryScheduler:
    def __init__(self):
        self.logger = logging.getLogger('scheduler')
        self.discoverer = NetworkDiscoverer()
        self.scheduled_tasks: Dict[str, threading.Timer] = {}
        self.lock = threading.Lock()
        
    def schedule_discovery(self, ip_address: str, is_first_time: bool = True):
        with self.lock:
            # Cancel existing timer if any
            self.cancel_discovery(ip_address)
            
            # Set delay based on whether it's first time
            delay = 5 if is_first_time else 60  # 5 minutes for first time, 1 minute for retries
            
            self.logger.info(f"Scheduling discovery for {ip_address} in {delay} seconds")
            timer = threading.Timer(delay, self._execute_discovery, args=(ip_address,))
            timer.daemon = False
            timer.start()
            
            self.scheduled_tasks[ip_address] = timer
    
    def cancel_discovery(self, ip_address: str):
        if ip_address in self.scheduled_tasks:
            self.scheduled_tasks[ip_address].cancel()
            del self.scheduled_tasks[ip_address]
    
    def _execute_discovery(self, ip_address: str):
        try:
            self.logger.info(f"Executing discovery for {ip_address}")
            device_data = self.discoverer.discover_ip(ip_address)
            
            if not device_data:
                # If discovery failed, reschedule
                self.logger.warning(f"Discovery failed for {ip_address}, rescheduling...")
                self.schedule_discovery(ip_address, is_first_time=False)
        
        except Exception as e:
            self.logger.error(f"Error during discovery of {ip_address}: {str(e)}")
            # Reschedule on error
            self.schedule_discovery(ip_address, is_first_time=False)

DiscoveryScheduler = _DiscoveryScheduler()
