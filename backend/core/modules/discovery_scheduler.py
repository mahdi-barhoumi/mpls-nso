import logging
import threading
from typing import Dict
from core.modules.discovery import NetworkDiscoverer

class _DiscoveryScheduler:
    def __init__(self):
        self.logger = logging.getLogger('discovery-scheduler')
        self.scheduled_tasks: Dict[str, threading.Timer] = {}
        self.lock = threading.Lock()
        self.network_discovery_timer = None
        self.network_discovery_interval = 300  # 5 minutes in seconds
        
    def schedule_discovery(self, ip_address: str, is_first_time: bool = True):
        with self.lock:
            # Cancel existing timer if any
            self.cancel_discovery(ip_address)
            
            # Set delay based on whether it's first time
            delay = 60 if is_first_time else 10  # 1 minute for first time, 10 seconds for retries
            
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
            device_data = NetworkDiscoverer.discover_single_device(ip_address)
            
            if not device_data:
                # If discovery failed, reschedule
                self.logger.warning(f"Discovery failed for {ip_address}, rescheduling...")
                self.schedule_discovery(ip_address, is_first_time=False)
        
        except Exception as e:
            self.logger.error(f"Error during discovery of {ip_address}: {str(e)}")
            # Reschedule on error
            self.schedule_discovery(ip_address, is_first_time=False)
    
    def start_periodic_discovery(self):
        with self.lock:
            if not NetworkDiscoverer.initialized:
                return
            if self.network_discovery_timer:
                self.network_discovery_timer.cancel()
            
            self.logger.info(f"Starting periodic network discovery every {self.network_discovery_interval} seconds")
            self._schedule_next_discovery()
    
    def stop_periodic_discovery(self):
        with self.lock:
            if self.network_discovery_timer:
                self.network_discovery_timer.cancel()
                self.network_discovery_timer = None
                self.logger.info("Stopped periodic network discovery")
    
    def _schedule_next_discovery(self):
        self.network_discovery_timer = threading.Timer(
            self.network_discovery_interval, 
            self._execute_network_discovery
        )
        self.network_discovery_timer.daemon = True
        self.network_discovery_timer.start()
    
    def _execute_network_discovery(self):
        try:
            self.logger.info("Starting network-wide discovery")
            NetworkDiscoverer.discover_network()
        except Exception as e:
            self.logger.error(f"Error during network-wide discovery: {str(e)}")
        finally:
            # Schedule next discovery regardless of success/failure
            self._schedule_next_discovery()

DiscoveryScheduler = _DiscoveryScheduler()
#DiscoveryScheduler.start_periodic_discovery()
