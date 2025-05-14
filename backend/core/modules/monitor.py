import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from django.utils import timezone
from core.models import Router, RouterMetric, InterfaceMetric, Notification
from core.modules.utils.restconf import RestconfWrapper
from core.settings import get_settings

class _NetworkMonitor:
    def __init__(self):
        self.logger = logging.getLogger('network-monitor')
        self.restconf = None
        self.initialized = False
        self.metrics_interval = 5 * 60  # 5 minutes
        self.notification_cooldown = 30 * 60  # 30 minutes
        self.thresholds = {
            'cpu_warning': 70.0,
            'cpu_critical': 90.0,
            'memory_warning': 80.0,
            'memory_critical': 90.0,
            'storage_warning': 80.0,
            'storage_critical': 90.0
        }
        self.last_notification_hashes = {}
        self.is_running = False
        self.monitor_interval = 30  # seconds
        self.max_workers = 5  # Default number of worker threads

    def initialize(self):
        if self.initialized:
            return
            
        settings = get_settings()
        if not settings:
            self.logger.warning("Cannot initialize monitor: No system settings found")
            return

        self.restconf = RestconfWrapper()
        self.initialized = True
        
    def monitor_all_routers(self):
        routers = Router.objects.all()  # Monitor all routers, not just reachable ones
        self.logger.info(f"Starting network-wide monitoring cycle for {routers.count()} routers")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_router = {executor.submit(self.monitor_router, router): router for router in routers}
            
            for future in future_to_router:
                router = future_to_router[future]
                try:
                    future.result()
                except Exception as e:
                    self.logger.error(f"Error monitoring router {router.hostname}: {str(e)}")
        
        self.logger.info("Completed network-wide monitoring cycle")

    def monitor_router(self, router):
        self.logger.info(f"Monitoring router {router.hostname} ({router.management_ip_address})")
        
        # Check if RESTCONF is available
        if not self.restconf.is_available(router.management_ip_address):
            self.logger.warning(f"Router {router.hostname} is not reachable via RESTCONF")
            if router.reachable:  # Only update if status changed
                router.reachable = False
                router.save()
                self.logger.info(f"Marked router {router.hostname} as unreachable")
                self._create_notification(
                    title=f"Router {router.hostname} is unreachable",
                    message=f"Lost connection to router {router.hostname} ({router.management_ip_address})",
                    severity="critical",
                    source="monitoring"
                )
            return
        
        # Mark as reachable if we got here
        if not router.reachable:  # Only update if status changed
            router.reachable = True
            router.save()
            self.logger.info(f"Marked router {router.hostname} as reachable")
            self._create_notification(
                title=f"Router {router.hostname} is now reachable",
                message=f"Restored connection to router {router.hostname} ({router.management_ip_address})",
                severity="info",
                source="monitoring"
            )
        
        # Collect system metrics
        self.collect_system_metrics(router)
        
        # Collect interface metrics
        self.collect_interface_metrics(router)
        
        self.logger.info(f"Completed monitoring for router {router.hostname}")

    def collect_system_metrics(self, router):
        # Collect CPU usage metrics
        cpu_data = self.restconf.get(
            router.management_ip_address,
            "Cisco-IOS-XE-process-cpu-oper:cpu-usage/cpu-utilization"
        )
        
        if not cpu_data:
            self.logger.warning(f"Failed to collect CPU metrics for {router.hostname}")
            return
        
        # Collect memory metrics
        memory_data = self.restconf.get(
            router.management_ip_address,
            "Cisco-IOS-XE-memory-oper:memory-statistics/memory-statistic"
        )
        
        if not memory_data or 'Cisco-IOS-XE-memory-oper:memory-statistic' not in memory_data:
            self.logger.warning(f"Failed to collect memory metrics for {router.hostname}")
            return
        
        # Collect storage metrics
        storage_data = self.restconf.get(
            router.management_ip_address,
            "Cisco-IOS-XE-platform-software-oper:cisco-platform-software/q-filesystem"
        )
        
        if not storage_data or 'Cisco-IOS-XE-platform-software-oper:q-filesystem' not in storage_data:
            self.logger.warning(f"Failed to collect storage metrics for {router.hostname}")
            return
        
        # Parse metrics from the responses
        cpu_util = cpu_data.get('Cisco-IOS-XE-process-cpu-oper:cpu-utilization', {})
        
        # Get main memory stats (Processor memory)
        memory_stats = None
        for mem_stat in memory_data.get('Cisco-IOS-XE-memory-oper:memory-statistic', []):
            if mem_stat.get('name') == 'Processor':
                memory_stats = mem_stat
                break
        
        if not memory_stats:
            self.logger.warning(f"No processor memory stats found for {router.hostname}")
            return
        
        # Get the primary storage partition
        storage_stats = None
        filesystem = storage_data.get('Cisco-IOS-XE-platform-software-oper:q-filesystem', {})
        if filesystem:
            for partition in filesystem[0].get('partitions', []):
                if partition.get('is-primary', False):
                    storage_stats = partition
                    break
        
        if not storage_stats:
            self.logger.warning(f"No primary storage partition found for {router.hostname}")
            return
        
        # Calculate metrics
        cpu_5s = float(cpu_util.get('five-seconds', 0))
        cpu_1m = float(cpu_util.get('one-minute', 0))
        cpu_5m = float(cpu_util.get('five-minutes', 0))
        
        mem_total = int(memory_stats.get('total-memory', 0))
        mem_used = int(memory_stats.get('used-memory', 0))
        mem_free = int(memory_stats.get('free-memory', 0))
        mem_used_percent = (mem_used / mem_total * 100) if mem_total > 0 else 0
        
        storage_total = int(storage_stats.get('total-size', 0))
        storage_used = int(storage_stats.get('used-size', 0))
        storage_free = storage_total - storage_used
        storage_used_percent = float(storage_stats.get('used-percent', 0))
        
        # Store metrics in database
        router_metric = RouterMetric(
            router=router,
            cpu_usage_5s=cpu_5s,
            cpu_usage_1m=cpu_1m,
            cpu_usage_5m=cpu_5m,
            mem_used_percent=mem_used_percent,
            mem_total=mem_total,
            mem_used=mem_used,
            mem_free=mem_free,
            storage_used_percent=storage_used_percent,
            storage_total=storage_total,
            storage_used=storage_used,
            storage_free=storage_free,
        )
        router_metric.save()
        
        # Check thresholds and create notifications if needed
        self._check_cpu_thresholds(router, cpu_5m)
        self._check_memory_thresholds(router, mem_used_percent)
        self._check_storage_thresholds(router, storage_used_percent)
    
    def get_system_info(self, router):
        try:
            system_data = self.restconf.get(
                router.management_ip_address,
                "openconfig-system:system"
            )
            
            if not system_data or 'openconfig-system:system' not in system_data:
                return None
                
            system = system_data['openconfig-system:system']
            state = system.get('state', {})
            
            # Calculate uptime from boot-time
            boot_time = int(state.get('boot-time', 0))
            current_time = int(timezone.now().timestamp())
            uptime_seconds = current_time - boot_time
            
            return {
                'uptime': uptime_seconds,
                'current_datetime': state.get('current-datetime'),
                'cpu_info': self._parse_cpu_info(system.get('cpus', {}).get('cpu', []))
            }
            
        except Exception as e:
            self.logger.error(f"Error getting system info for {router.hostname}: {str(e)}")
            return None
            
    def _parse_cpu_info(self, cpus):
        cpu_info = []
        for cpu in cpus:
            state = cpu.get('state', {})
            total = state.get('total', {})
            cpu_info.append({
                'index': cpu.get('index'),
                'total': total.get('instant'),
                'idle': state.get('idle', {}).get('instant'),
                'user': state.get('user', {}).get('instant'),
                'kernel': state.get('kernel', {}).get('instant')
            })
        return cpu_info

    def collect_interface_metrics(self, router):
        interfaces_data = self.restconf.get(
            router.management_ip_address,
            "Cisco-IOS-XE-interfaces-oper:interfaces/interface"
        )
        
        if not interfaces_data or 'Cisco-IOS-XE-interfaces-oper:interface' not in interfaces_data:
            self.logger.warning(f"Failed to collect interface metrics for {router.hostname}")
            return
        
        interface_list = interfaces_data.get('Cisco-IOS-XE-interfaces-oper:interface', [])
        
        for intf_data in interface_list:
            interface_name = intf_data.get('name')
            
            # Find the interface in the database
            try:
                interface = router.interfaces.get(name=interface_name)
            except router.interfaces.model.DoesNotExist:
                self.logger.debug(f"Interface {interface_name} not found in database for {router.hostname}")
                continue
            
            # Get interface metrics
            operational_status = intf_data.get('oper-status', 'unknown').replace('if-oper-state-', '')
            
            stats = intf_data.get('statistics', {})
            in_octets = int(stats.get('in-octets', 0))
            out_octets = int(stats.get('out-octets', 0))
            in_errors = int(stats.get('in-errors', 0))
            out_errors = int(stats.get('out-errors', 0))
            in_discards = int(stats.get('in-discards', 0))
            out_discards = int(stats.get('out-discards', 0))
            rx_kbps = int(stats.get('rx-kbps', 0))
            tx_kbps = int(stats.get('tx-kbps', 0))
            
            # Convert kbps to bps
            bps_in = rx_kbps * 1000
            bps_out = tx_kbps * 1000
            
            # Store metrics in database
            interface_metric = InterfaceMetric(
                interface=interface,
                operational_status=operational_status,
                in_octets=in_octets,
                out_octets=out_octets,
                in_errors=in_errors,
                out_errors=out_errors,
                in_discards=in_discards,
                out_discards=out_discards,
                bps_in=bps_in,
                bps_out=bps_out
            )
            interface_metric.save()
            
            # Check interface status
            self._check_interface_status(interface, operational_status)
            self._check_interface_errors(interface, in_errors, out_errors)
    
    def _check_cpu_thresholds(self, router, cpu_usage):
        if cpu_usage >= self.thresholds['cpu_critical']:
            self._create_notification(
                title=f"Critical CPU usage on {router.hostname}",
                message=f"CPU usage is {cpu_usage:.1f}%, which exceeds the critical threshold of {self.thresholds['cpu_critical']}%",
                severity="critical",
                source="monitoring"
            )
        elif cpu_usage >= self.thresholds['cpu_warning']:
            self._create_notification(
                title=f"High CPU usage on {router.hostname}",
                message=f"CPU usage is {cpu_usage:.1f}%, which exceeds the warning threshold of {self.thresholds['cpu_warning']}%",
                severity="warning",
                source="monitoring"
            )
    
    def _check_memory_thresholds(self, router, memory_usage):
        if memory_usage >= self.thresholds['memory_critical']:
            self._create_notification(
                title=f"Critical memory usage on {router.hostname}",
                message=f"Memory usage is {memory_usage:.1f}%, which exceeds the critical threshold of {self.thresholds['memory_critical']}%",
                severity="critical",
                source="monitoring"
            )
        elif memory_usage >= self.thresholds['memory_warning']:
            self._create_notification(
                title=f"High memory usage on {router.hostname}",
                message=f"Memory usage is {memory_usage:.1f}%, which exceeds the warning threshold of {self.thresholds['memory_warning']}%",
                severity="warning",
                source="monitoring"
            )
    
    def _check_storage_thresholds(self, router, storage_usage):
        if storage_usage >= self.thresholds['storage_critical']:
            self._create_notification(
                title=f"Critical storage usage on {router.hostname}",
                message=f"Storage usage is {storage_usage:.1f}%, which exceeds the critical threshold of {self.thresholds['storage_critical']}%",
                severity="critical",
                source="monitoring"
            )
        elif storage_usage >= self.thresholds['storage_warning']:
            self._create_notification(
                title=f"High storage usage on {router.hostname}",
                message=f"Storage usage is {storage_usage:.1f}%, which exceeds the warning threshold of {self.thresholds['storage_warning']}%",
                severity="warning",
                source="monitoring"
            )
    
    def _check_interface_status(self, interface, operational_status):
        if interface.enabled and operational_status != 'ready':
            self.logger.info(f"Interface {interface.name} on {interface.router.hostname} is down")
            self._create_notification(
                title=f"Interface {interface.name} down on {interface.router.hostname}",
                message=f"Interface {interface.name} is administratively up but operationally down",
                severity="warning",
                source="monitoring"
            )
    
    def _check_interface_errors(self, interface, in_errors, out_errors):
        previous_metrics = InterfaceMetric.objects.filter(
            interface=interface
        ).order_by('-timestamp')[1:2]  # Get the second-to-last metric
        
        if previous_metrics:
            prev_in_errors = previous_metrics[0].in_errors
            prev_out_errors = previous_metrics[0].out_errors
            
            if in_errors > prev_in_errors:
                self._create_notification(
                    title=f"Increasing input errors on {interface.name}",
                    message=f"Input errors on interface {interface.name} increased from {prev_in_errors} to {in_errors}",
                    severity="warning",
                    source="monitoring"
                )
            
            if out_errors > prev_out_errors:
                self._create_notification(
                    title=f"Increasing output errors on {interface.name}",
                    message=f"Output errors on interface {interface.name} increased from {prev_out_errors} to {out_errors}",
                    severity="warning",
                    source="monitoring"
                )
    
    def _create_notification(self, title, message, severity, source, router=None, interface=None):
        import hashlib
        
        hash_components = [title, severity, source]
        hash_key = hashlib.sha256('|'.join(hash_components).encode()).hexdigest()
        
        current_time = timezone.now()
        if hash_key in self.last_notification_hashes:
            last_time = self.last_notification_hashes[hash_key]
            if (current_time - last_time).total_seconds() < self.notification_cooldown:
                self.logger.debug(f"Skipping duplicate notification: {title} (cooldown active)")
                return
        
        notification = Notification(
            title=title,
            message=message,
            severity=severity,
            source=source,
            hash_key=hash_key
        )
        notification.save()
        
        self.last_notification_hashes[hash_key] = current_time
        self._cleanup_notification_hashes()
        
        self.logger.info(f"Created {severity} notification: {title}")
        return notification
    
    def _cleanup_notification_hashes(self):
        current_time = timezone.now()
        keys_to_remove = []
        
        for hash_key, timestamp in self.last_notification_hashes.items():
            if (current_time - timestamp).total_seconds() > self.notification_cooldown:
                keys_to_remove.append(hash_key)
        
        for key in keys_to_remove:
            del self.last_notification_hashes[key]
    
    def get_router_metrics(self, router, hours=24):
        since = timezone.now() - timedelta(hours=hours)
        return RouterMetric.objects.filter(
            router=router,
            timestamp__gte=since
        ).order_by('timestamp')
    
    def get_interface_metrics(self, interface, hours=24):
        since = timezone.now() - timedelta(hours=hours)
        return InterfaceMetric.objects.filter(
            interface=interface,
            timestamp__gte=since
        ).order_by('timestamp')
    
    def purge_old_metrics(self, days=30):
        cutoff_date = timezone.now() - timedelta(days=days)
        
        deleted_router_metrics = RouterMetric.objects.filter(timestamp__lt=cutoff_date).delete()
        self.logger.info(f"Purged {deleted_router_metrics[0]} old router metrics")
        
        deleted_interface_metrics = InterfaceMetric.objects.filter(timestamp__lt=cutoff_date).delete()
        self.logger.info(f"Purged {deleted_interface_metrics[0]} old interface metrics")


NetworkMonitor = _NetworkMonitor()
NetworkMonitor.initialize()