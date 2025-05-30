import logging
import threading
from typing import Dict
from core.modules.discovery import NetworkDiscoverer
from core.modules.monitor import NetworkMonitor

class _Scheduler:
    def __init__(self):
        self.logger = logging.getLogger('scheduler')
        self.scheduled_discoveries: Dict[str, threading.Timer] = {}
        self.lock = threading.Lock()
        
        # Timers for periodic tasks
        self.network_discovery_timer = None
        self.network_monitor_timer = None
        
        # Intervals (in seconds)
        self.network_discovery_interval = 300  # 5 minutes
        self.network_monitor_interval = 60     # 60 seconds
        
    def schedule_discovery(self, ip_address: str, is_first_time: bool = True):
        with self.lock:
            # Cancel existing timer if any
            self.cancel_discovery(ip_address)
            
            # Set delay based on whether it's first time
            delay = 60 if is_first_time else 10  # 1 minute for first time, 10 seconds for retries
            
            self.logger.info(f"Scheduling discovery for {ip_address} in {delay} seconds")
            timer = threading.Timer(delay, self._execute_discovery, args=(ip_address,))
            timer.daemon = True
            timer.start()
            
            self.scheduled_discoveries[ip_address] = timer
    
    def cancel_discovery(self, ip_address: str):
        if ip_address in self.scheduled_discoveries:
            self.scheduled_discoveries[ip_address].cancel()
            del self.scheduled_discoveries[ip_address]
    
    def _execute_discovery(self, ip_address: str):
        try:
            self.logger.info(f"Executing discovery for {ip_address}")
            result = NetworkDiscoverer.discover_single_device(ip_address)
            
            if not result['success']:
                self.logger.warning(f"Discovery failed for {ip_address}, rescheduling...")
                self.schedule_discovery(ip_address, is_first_time=False)
        
        except Exception as e:
            self.logger.error(f"Error during discovery of {ip_address}: {str(e)}")
            self.schedule_discovery(ip_address, is_first_time=False)
    
    def start_periodic_tasks(self):
        with self.lock:
            if not NetworkDiscoverer.initialized or not NetworkMonitor.initialized:
                self.logger.warning("Cannot start periodic tasks: services not initialized")
                return
                
            # Start network discovery
            if self.network_discovery_timer:
                self.network_discovery_timer.cancel()
            self._schedule_next_discovery()
            
            # Start network monitoring
            if self.network_monitor_timer:
                self.network_monitor_timer.cancel()
            self._schedule_next_monitoring()
            
            self.logger.info(f"Started periodic tasks (Discovery: {self.network_discovery_interval}s, Monitoring: {self.network_monitor_interval}s)")
    
    def stop_periodic_tasks(self):
        with self.lock:
            if self.network_discovery_timer:
                self.network_discovery_timer.cancel()
                self.network_discovery_timer = None
                
            if self.network_monitor_timer:
                self.network_monitor_timer.cancel()
                self.network_monitor_timer = None
                
            self.logger.info("Stopped all periodic tasks")
    
    def _schedule_next_discovery(self):
        self.network_discovery_timer = threading.Timer(
            self.network_discovery_interval, 
            self._execute_network_discovery
        )
        self.network_discovery_timer.daemon = True
        self.network_discovery_timer.start()
    
    def _schedule_next_monitoring(self):
        self.network_monitor_timer = threading.Timer(
            self.network_monitor_interval, 
            self._execute_network_monitoring
        )
        self.network_monitor_timer.daemon = True
        self.network_monitor_timer.start()
    
    def _execute_network_discovery(self):
        try:
            self.logger.info("Starting network-wide discovery")
            NetworkDiscoverer.discover_network()
        except Exception as e:
            self.logger.error(f"Error during network-wide discovery: {str(e)}")
        finally:
            self._schedule_next_discovery()
    
    def _execute_network_monitoring(self):
        try:
            self.logger.info("Starting network-wide monitoring")
            NetworkMonitor.monitor_all_routers()
        except Exception as e:
            self.logger.error(f"Error during network-wide monitoring: {str(e)}")
        finally:
            self._schedule_next_monitoring()

Scheduler = _Scheduler()
Scheduler.start_periodic_tasks()
