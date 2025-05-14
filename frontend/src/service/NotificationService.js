import LogService from './LogService'
import MonitoringService from './MonitoringService'
import { ref } from 'vue'

class NotificationService {
  constructor() {
    this.monitoringService = new MonitoringService()
    this.notifications = ref([]) // Initialize with empty array
    this.pollingInterval = null
  }

  async fetchNotifications() {
    try {
      // Fetch critical logs
      const logsResponse = await LogService.getLogs({ level: 'CRITICAL' })
      const criticalLogs = logsResponse.logs.map((log) => ({
        id: `log-${Date.now()}-${Math.random()}`,
        type: 'log',
        message: log.message,
        timestamp: new Date(log.timestamp),
        module: log.module,
        level: log.level,
      }))

      // Fetch monitoring alerts
      const dashboardStats = await this.monitoringService.getDashboardStats()
      const monitoringAlerts = []

      // Add CPU alerts
      dashboardStats.high_cpu_routers?.forEach((router) => {
        monitoringAlerts.push({
          id: `monitoring-cpu-${router.id}`,
          type: 'monitoring',
          message: `High CPU usage (${router.cpu_usage}%) on router ${router.hostname}`,
          timestamp: new Date(),
          resource: 'router',
          resourceId: router.id,
        })
      })

      // Add Memory alerts
      dashboardStats.high_memory_routers?.forEach((router) => {
        monitoringAlerts.push({
          id: `monitoring-memory-${router.id}`,
          type: 'monitoring',
          message: `High memory usage (${router.memory_usage}%) on router ${router.hostname}`,
          timestamp: new Date(),
          resource: 'router',
          resourceId: router.id,
        })
      })

      // Add Storage alerts
      dashboardStats.high_storage_routers?.forEach((router) => {
        monitoringAlerts.push({
          id: `monitoring-storage-${router.id}`,
          type: 'monitoring',
          message: `High storage usage (${router.storage_usage}%) on router ${router.hostname}`,
          timestamp: new Date(),
          resource: 'router',
          resourceId: router.id,
        })
      })

      // Update notifications
      this.notifications.value = [...monitoringAlerts, ...criticalLogs]
        .sort((a, b) => b.timestamp - a.timestamp)
        .slice(0, 50) // Keep only last 50 notifications
    } catch (error) {
      console.error('Error fetching notifications:', error)
    }
  }

  startPolling(intervalMs = 30000) {
    // Default to 30 seconds
    this.stopPolling()
    this.fetchNotifications() // Initial fetch
    this.pollingInterval = setInterval(() => this.fetchNotifications(), intervalMs)
  }

  stopPolling() {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval)
      this.pollingInterval = null
    }
  }

  clearNotification(id) {
    this.notifications.value = this.notifications.value.filter((n) => n.id !== id)
  }

  clearAllNotifications() {
    this.notifications.value = []
  }

  getNotifications() {
    return this.notifications
  }
}

// Create a singleton instance
const notificationService = new NotificationService()
export default notificationService
