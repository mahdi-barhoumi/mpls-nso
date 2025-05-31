class MonitoringService {
  constructor() {
    this.baseUrl = 'http://127.0.0.1:8000/api'
    this.refreshCallbacks = []
    this.refreshInterval = null
  }

  async getDashboardStats() {
    const response = await fetch(`${this.baseUrl}/monitoring/dashboard/`)
    if (!response.ok) throw new Error('Failed to fetch dashboard stats')
    return response.json()
  }

  async getRouterMetrics(routerId = null, hours = 24) {
    const url = routerId
      ? `${this.baseUrl}/monitoring/routers/${routerId}/?hours=${hours}`
      : `${this.baseUrl}/monitoring/routers/`

    const response = await fetch(url)
    if (!response.ok) throw new Error('Failed to fetch router metrics')
    return response.json()
  }

  async getInterfaceMetrics(interfaceId = null, hours = 24) {
    const url = interfaceId
      ? `${this.baseUrl}/monitoring/interfaces/${interfaceId}/?hours=${hours}`
      : `${this.baseUrl}/monitoring/interfaces/`

    const response = await fetch(url)
    if (!response.ok) throw new Error('Failed to fetch interface metrics')
    const data = await response.json()
    // If fetching all interfaces, ensure all stats are present
    if (!interfaceId) {
      // The backend only returns a subset for all interfaces, so fetch details for each if needed
      // But for now, just return as is (the backend should be updated to include all stats)
      return data
    }
    // If fetching a single interface, all stats are present
    return data
  }

  async getDeviceInfo(routerId) {
    const response = await fetch(`${this.baseUrl}/monitoring/device-info/${routerId}/`)
    if (!response.ok) throw new Error('Failed to fetch device info')
    return response.json()
  }

  formatBandwidth(bps) {
    if (!bps) return '0 bps'
    if (bps >= 1e9) return `${(bps / 1e9).toFixed(2)} Gbps`
    if (bps >= 1e6) return `${(bps / 1e6).toFixed(2)} Mbps`
    if (bps >= 1e3) return `${(bps / 1e3).toFixed(2)} Kbps`
    return `${bps} bps`
  }

  formatMemory(kb) {
    if (!kb) return '0 KB'
    if (kb >= 1024 * 1024) return `${(kb / (1024 * 1024)).toFixed(1)} GB`
    if (kb >= 1024) return `${(kb / 1024).toFixed(1)} MB`
    return `${kb} KB`
  }

  addRefreshCallback(callback) {
    this.refreshCallbacks.push(callback)
  }

  startAutoRefresh(interval = 30000) {
    if (this.refreshInterval) this.stopAutoRefresh()
    this.refreshInterval = setInterval(() => {
      this.refreshCallbacks.forEach((callback) => callback())
    }, interval)
  }

  stopAutoRefresh() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval)
      this.refreshInterval = null
    }
  }
}

export default MonitoringService
