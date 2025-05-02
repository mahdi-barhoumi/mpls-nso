const BASE_URL = 'http://127.0.0.1:8000/api/metrics'

export default class MonitoringService {
  async getDashboardStats() {
    const response = await fetch(`${BASE_URL}/dashboard/`)
    if (!response.ok) {
      throw new Error('Failed to fetch dashboard statistics')
    }
    return await response.json()
  }

  async getRouterMetrics(routerId = null) {
    const url = routerId ? `${BASE_URL}/routers/${routerId}/` : `${BASE_URL}/routers/`
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error('Failed to fetch router metrics')
    }
    return await response.json()
  }

  async getInterfaceMetrics(interfaceId = null) {
    const url = interfaceId ? `${BASE_URL}/interfaces/${interfaceId}/` : `${BASE_URL}/interfaces/`
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error('Failed to fetch interface metrics')
    }
    return await response.json()
  }

  exportInterfaceMetrics(data) {
    const csvContent = data
      .map((metric) => {
        return `${metric.router_hostname},${metric.name},${metric.operational_status},${metric.bps_in},${metric.bps_out}`
      })
      .join('\n')

    const header = 'Router,Interface,Status,Incoming (bps),Outgoing (bps)\n'
    const blob = new Blob([header + csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)

    const link = document.createElement('a')
    link.setAttribute('href', url)
    link.setAttribute('download', `interface-metrics-${new Date().toISOString().split('T')[0]}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  formatBandwidth(bps) {
    if (bps >= 1000000000) {
      return `${(bps / 1000000000).toFixed(2)} Gbps`
    } else if (bps >= 1000000) {
      return `${(bps / 1000000).toFixed(2)} Mbps`
    } else if (bps >= 1000) {
      return `${(bps / 1000).toFixed(2)} Kbps`
    }
    return `${bps} bps`
  }
}
