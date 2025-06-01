<template>
  <div class="card monitoring-card">
    <div class="dashboard">
      <div class="stats-section">
        <h3>Monitoring</h3>
        <div class="update-info">
          <p style="margin: 0;">Last updated: {{ formatUtils.formatTimeDetailed(lastUpdateTime) }}</p>
          <p>Next refresh in: {{ refreshCountdown }}s</p>
        </div>
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-header-row">
              <h3>Devices</h3>
              <div class="stat-values">
                <span class="stat-main">{{ `${dashboardStats.reachable_routers}/${dashboardStats.total_routers} Online`
                  }}</span>
                <small class="stat-secondary">{{ `${formatUtils.getPercentage(dashboardStats.reachable_routers,
                  dashboardStats.total_routers)}% online` }}</small>
              </div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-header-row">
              <h3>Interfaces</h3>
              <div class="stat-values">
                <span class="stat-main">{{ `${dashboardStats.enabled_interfaces}/${dashboardStats.total_interfaces}
                  Active` }}</span>
                <small class="stat-secondary">{{ `${formatUtils.getPercentage(dashboardStats.enabled_interfaces,
                  dashboardStats.total_interfaces)}% active` }}</small>
              </div>
            </div>
          </div>
          <div v-if="dashboardStats.high_cpu_routers?.length" class="stat-card alert">
            <h3>High CPU Alert</h3>
            <p>{{ `${dashboardStats.high_cpu_routers.length} devices above 70%` }}</p>
            <small>{{ `${formatUtils.getPercentage(dashboardStats.high_cpu_routers.length,
              dashboardStats.total_routers)}% of network` }}</small>
          </div>
          <div v-if="dashboardStats.high_memory_routers?.length" class="stat-card alert">
            <h3>Memory Alert</h3>
            <p>{{ `${dashboardStats.high_memory_routers.length} devices above 80%` }}</p>
            <small>{{ `${formatUtils.getPercentage(dashboardStats.high_memory_routers.length,
              dashboardStats.total_routers)}% of network` }}</small>
          </div>
        </div>
      </div>
      <div class="router-section">
        <div class="devices-header-row">
          <h4 class="devices-title">Devices</h4>
          <div class="controls">
            <input v-model="searchQuery" type="text" placeholder="Search devices..." />
            <select v-model="sortBy">
              <option value="hostname">Sort by Hostname</option>
              <option value="cpu_usage_5m">Sort by CPU Usage</option>
              <option value="mem_used_percent">Sort by Memory Usage</option>
              <option value="storage_used">Sort by Storage Usage</option>
              <option value="timestamp">Sort by Last Update</option>
            </select>
          </div>
        </div>
        <div class="table-hint-below">
          <small>
            <i class="pi pi-info-circle" style="vertical-align: middle; margin-right: 0.25em; font-size: 1em;"></i>
            Click on a device row to view detailed information and performance history.
          </small>
        </div>
        <DataTable :value="sortedAndFilteredRouters" dataKey="id" selectionMode="single" :selection="selectedRouter"
          @rowSelect="onRowSelect" @rowUnselect="onRowUnselect" :rowClass="routerRowClass" responsiveLayout="scroll"
          showGridlines :paginator="true" :rows="5" :rowsPerPageOptions="[5, 10, 20, 50]" class="router-table">
          <Column field="hostname" header="Hostname">
            <template #body="slotProps">
              <strong>{{ slotProps.data.hostname }}</strong>
            </template>
          </Column>
          <Column field="reachable" header="Status">
            <template #body="slotProps">
              <span :class="slotProps.data.reachable ? 'online' : 'stale'">
                {{ slotProps.data.reachable ? 'Online' : 'Offline' }}
              </span>
            </template>
          </Column>
          <Column field="cpu_usage_5m" header="CPU Usage">
            <template #body="slotProps">
              <div class="metric-cell" :class="getMetricAlertClass(slotProps.data.cpu_usage_5m, 70, 50)">
                <div class="metric-values">
                  <strong>{{ formatUtils.formatPercentage(slotProps.data.cpu_usage_5m) }}</strong>
                  <small>
                    5s: {{ formatUtils.formatPercentage(slotProps.data.cpu_usage_5s) }} |
                    1m: {{ formatUtils.formatPercentage(slotProps.data.cpu_usage_1m) }}
                  </small>
                </div>
                <div class="usage-bar">
                  <div class="usage-fill" :style="{ width: (slotProps.data.cpu_usage_5m || 0) + '%' }"></div>
                </div>
              </div>
            </template>
          </Column>
          <Column field="mem_used_percent" header="Memory Usage">
            <template #body="slotProps">
              <div class="metric-cell" :class="getMetricAlertClass(slotProps.data.mem_used_percent, 80, 60)">
                <div class="metric-values">
                  <strong>{{ formatUtils.formatPercentage(slotProps.data.mem_used_percent) }}</strong>
                  <small v-if="slotProps.data.mem_total">
                    {{ formatUtils.formatBytes(slotProps.data.mem_used || 0) }} / {{
                      formatUtils.formatBytes(slotProps.data.mem_total) }}
                  </small>
                </div>
                <div class="usage-bar">
                  <div class="usage-fill" :style="{ width: (slotProps.data.mem_used_percent || 0) + '%' }"></div>
                </div>
              </div>
            </template>
          </Column>
          <Column field="storage_used_percent" header="Storage Usage">
            <template #body="slotProps">
              <div class="metric-cell" :class="getMetricAlertClass(slotProps.data.storage_used_percent, 80, 60)">
                <div class="metric-values">
                  <strong>{{ formatUtils.formatPercentage(slotProps.data.storage_used_percent) }}</strong>
                  <small v-if="slotProps.data.storage_total">
                    {{ formatUtils.formatBytes(slotProps.data.storage_used || 0) }} / {{
                      formatUtils.formatBytes(slotProps.data.storage_total) }}
                  </small>
                </div>
                <div class="usage-bar">
                  <div class="usage-fill" :style="{ width: (slotProps.data.storage_used_percent || 0) + '%' }"></div>
                </div>
              </div>
            </template>
          </Column>
          <Column field="timestamp" header="Last Updated">
            <template #body="slotProps">
              {{ formatUtils.formatTimeDetailed(slotProps.data.timestamp) }}
            </template>
          </Column>
        </DataTable>
      </div>
      <div v-if="selectedRouter" class="details-section">
        <h4 style="font-weight: 600; font-size: 1.25rem;">Details: {{ selectedRouter.hostname }}</h4>
        <div class="current-status">
          <div class="status-card usage-card">
            <div class="usage-label">CPU Usage</div>
            <div class="usage-circle-outer">
              <svg class="usage-circle" width="64" height="64">
                <circle class="usage-bg" cx="32" cy="32" r="28" stroke-width="6" fill="none" />
                <circle class="usage-fg" :class="{
                  alert: selectedRouter.cpu_usage_5m >= 70,
                  warning: selectedRouter.cpu_usage_5m >= 50 && selectedRouter.cpu_usage_5m < 70
                }" cx="32" cy="32" r="28" stroke-width="6" fill="none" :stroke-dasharray="175.9"
                  :stroke-dashoffset="175.9 - (175.9 * (selectedRouter.cpu_usage_5m || 0) / 100)"
                  transform="rotate(-90 32 32)" />
                <text x="32" y="32" text-anchor="middle" dominant-baseline="middle" alignment-baseline="middle"
                  class="usage-value" :class="{
                    alert: selectedRouter.cpu_usage_5m >= 70,
                    warning: selectedRouter.cpu_usage_5m >= 50,
                  }">
                  {{ formatUtils.formatPercentage(selectedRouter.cpu_usage_5m) }}
                </text>
              </svg>
            </div>
            <div class="usage-metrics">
              <div class="metric-breakdown">
                <div>5s: {{ formatUtils.formatPercentage(selectedRouter.cpu_usage_5s) }}</div>
                <div>1m: {{ formatUtils.formatPercentage(selectedRouter.cpu_usage_1m) }}</div>
                <div>5m: {{ formatUtils.formatPercentage(selectedRouter.cpu_usage_5m) }}</div>
              </div>
            </div>
          </div>
          <div class="status-card usage-card">
            <div class="usage-label">Memory Usage</div>
            <div class="usage-circle-outer">
              <svg class="usage-circle" width="64" height="64">
                <circle class="usage-bg" cx="32" cy="32" r="28" stroke-width="6" fill="none" />
                <circle class="usage-fg" :class="{
                  alert: selectedRouter.mem_used_percent >= 80,
                  warning: selectedRouter.mem_used_percent >= 60 && selectedRouter.mem_used_percent < 80
                }" cx="32" cy="32" r="28" stroke-width="6" fill="none" :stroke-dasharray="175.9"
                  :stroke-dashoffset="175.9 - (175.9 * (selectedRouter.mem_used_percent || 0) / 100)"
                  transform="rotate(-90 32 32)" />
                <text x="32" y="32" text-anchor="middle" dominant-baseline="middle" alignment-baseline="middle"
                  class="usage-value" :class="{
                    alert: selectedRouter.mem_used_percent >= 80,
                    warning: selectedRouter.mem_used_percent >= 60,
                  }">
                  {{ formatUtils.formatPercentage(selectedRouter.mem_used_percent) }}
                </text>
              </svg>
            </div>
            <div class="usage-metrics">
              <div class="metric-breakdown" v-if="selectedRouter.mem_total">
                <div>Used: {{ formatUtils.formatBytes(selectedRouter.mem_used || 0) }}</div>
                <div>Free: {{ formatUtils.formatBytes(selectedRouter.mem_free || 0) }}</div>
                <div>Total: {{ formatUtils.formatBytes(selectedRouter.mem_total) }}</div>
              </div>
            </div>
          </div>
          <div class="status-card usage-card">
            <div class="usage-label">Storage Usage</div>
            <div class="usage-circle-outer">
              <svg class="usage-circle" width="64" height="64">
                <circle class="usage-bg" cx="32" cy="32" r="28" stroke-width="6" fill="none" />
                <circle class="usage-fg" :class="{
                  alert: selectedRouter.storage_used_percent >= 80,
                  warning: selectedRouter.storage_used_percent >= 60 && selectedRouter.storage_used_percent < 80
                }" cx="32" cy="32" r="28" stroke-width="6" fill="none" :stroke-dasharray="175.9"
                  :stroke-dashoffset="175.9 - (175.9 * (selectedRouter.storage_used_percent || 0) / 100)"
                  transform="rotate(-90 32 32)" />
                <text x="32" y="32" text-anchor="middle" dominant-baseline="middle" alignment-baseline="middle"
                  class="usage-value" :class="{
                    alert: selectedRouter.storage_used_percent >= 80,
                    warning: selectedRouter.storage_used_percent >= 60,
                  }">
                  {{ formatUtils.formatPercentage(selectedRouter.storage_used_percent) }}
                </text>
              </svg>
            </div>
            <div class="usage-metrics">
              <div class="metric-breakdown" v-if="selectedRouter.storage_total">
                <div>Used: {{ formatUtils.formatBytes(selectedRouter.storage_used || 0) }}</div>
                <div>Free: {{ formatUtils.formatBytes(selectedRouter.storage_free || 0) }}</div>
                <div>Total: {{ formatUtils.formatBytes(selectedRouter.storage_total) }}</div>
              </div>
            </div>
          </div>
        </div>
        <div class="metrics-chart">
          <div class="metrics-header-row">
            <h4 class="metrics-title">Performance History</h4>
            <div class="chart-controls">
              <select v-model="timeRange">
                <option value="1">Last 1 Hour</option>
                <option value="6">Last 6 Hours</option>
                <option value="24">Last 24 Hours</option>
                <option value="168">Last 7 Days</option>
              </select>
              <select v-model="selectedMetric">
                <option value="cpu_usage_5m">CPU Usage (5m avg)</option>
                <option value="cpu_usage_1m">CPU Usage (1m avg)</option>
                <option value="cpu_usage_5s">CPU Usage (5s avg)</option>
                <option value="mem_used_percent">Memory Usage</option>
                <option value="storage_used_percent">Storage Usage</option>
              </select>
            </div>
          </div>
          <div v-if="routerHistory.length" class="chart-container">
            <Chart type="line" :data="chartData" :options="chartOptions" class="performance-chart" />
          </div>
          <div v-else class="no-data">
            <p>No historical data available for the selected time range</p>
            <button @click="loadRouterHistory" class="retry-btn">Retry Loading</button>
          </div>
        </div>
        <div class="interfaces-section">
          <h4 class="interfaces-title">Interfaces</h4>
          <div class="table-hint-below">
            <small>
              <i class="pi pi-info-circle" style="vertical-align: middle; margin-right: 0.25em; font-size: 1em;"></i>
              Click on an interface card to view bandwidth history.
            </small>
          </div>
          <div v-if="routerInterfaces.length" class="interfaces-grid">
            <div
              v-for="iface in routerInterfaces"
              :key="iface.interface_id"
              class="interface-card"
              :class="{ selected: selectedInterface && selectedInterface.interface_id === iface.interface_id }"
              @click="selectedInterface = iface"
              style="cursor:pointer"
            >
              <div class="interface-header compact">
                <span class="iface-name">{{ iface.name }}</span>
                <span
                  :class="{
                    'status-up': iface.operational_status === 'up' || iface.operational_status === 'ready',
                    'status-down': iface.operational_status === 'down' || iface.operational_status === 'no-pass'
                  }"
                >
                  {{
                    iface.operational_status === 'up' ? 'UP'
                    : iface.operational_status === 'down' ? 'DOWN'
                    : iface.operational_status === 'ready' ? 'READY'
                    : iface.operational_status === 'no-pass' ? 'NO PASS'
                    : iface.operational_status
                  }}
                </span>
              </div>
              <div class="interface-metrics">
                <div class="traffic-total-row top">
                  <span>Bandwidth: {{ formatBandwidth((iface.bps_in || 0) + (iface.bps_out || 0)) }}</span>
                </div>
                <div class="traffic-metrics compact-grid">
                  <div class="traffic-direction">
                    <div class="direction-label down">
                      <span title="Downstream">↓</span>
                    </div>
                    <div class="traffic-value">
                      <strong>{{ formatBandwidth(iface.bps_in) }}</strong>
                      <small>Transferred: {{ formatBytes(iface.in_octets) }}</small>
                      <small>Discards: {{ formatBytes(iface.in_discards) }}</small>
                      <small :class="{ 'alert': (iface.in_errors || 0) > 0 }">Errors: {{ formatBytes(iface.in_errors) }}</small>
                    </div>
                  </div>
                  <div class="traffic-direction">
                    <div class="direction-label up">
                      <span title="Upstream">↑</span>
                    </div>
                    <div class="traffic-value">
                      <strong>{{ formatBandwidth(iface.bps_out) }}</strong>
                      <small>Transferred: {{ formatBytes(iface.out_octets) }}</small>
                      <small>Discards: {{ formatBytes(iface.out_discards) }}</small>
                      <small :class="{ 'alert': (iface.out_errors || 0) > 0 }">Errors: {{ formatBytes(iface.out_errors) }}</small>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="no-data">
            <p>No interface data available</p>
          </div>
          <div v-if="selectedInterface && interfaceHistory.length">
            <div class="metrics-header-row">
              <h4 style="padding: 0; margin: 0; font-weight:600; font-size: 1.25rem;">Bandwidth History: {{ selectedInterface.name }}</h4>
              <div class="chart-controls">
                <select v-model="interfaceTimeRange">
                  <option value="1">Last 1 Hour</option>
                  <option value="6">Last 6 Hours</option>
                  <option value="24">Last 24 Hours</option>
                  <option value="168">Last 7 Days</option>
                </select>
              </div>
            </div>
            <div class="interface-chart-container">
              <Chart type="line" :data="interfaceChartData" :options="interfaceChartOptions" class="interface-bandwidth-chart" />
            </div>
          </div>
          <div v-if="selectedInterface && !interfaceHistory.length" class="no-data">
            <p>No historical data available for this interface</p>
            <button @click="loadInterfaceHistory(selectedInterface)" class="retry-btn">Retry Loading</button>
          </div>
        </div>
      </div>
      <div v-if="error" class="error">
        <strong>Error:</strong> {{ error }}
        <button @click="error = ''" class="close-error">×</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import MonitoringService from '@/service/MonitoringService'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Chart from 'primevue/chart'

const formatUtils = {
  formatPercentage(value) {
    if (value === null || value === undefined) return 'N/A'
    return value.toFixed(1) + '%'
  },
  getPercentage(part, total) {
    if (!total) return '0.0'
    return ((part / total) * 100).toFixed(1)
  },
  formatTimeDetailed(timestamp) {
    if (!timestamp) return 'N/A'
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ${diffMins % 60}m ago`
    return date.toLocaleString()
  },
  formatBytes(kb) {
    if (!kb) return '0 B'
    const bytes = kb * 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(1024))
    return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + sizes[i]
  },
}

const monitoringService = new MonitoringService()
const dashboardStats = ref({
  total_routers: 0,
  reachable_routers: 0,
  total_interfaces: 0,
  enabled_interfaces: 0,
  high_cpu_routers: [],
  high_memory_routers: [],
  high_storage_routers: [],
})
const routers = ref([])
const selectedRouter = ref(null)
const routerHistory = ref([])
const routerInterfaces = ref([])
const selectedMetric = ref('cpu_usage_5m')
const timeRange = ref('24')
const error = ref('')
const lastUpdateTime = ref(new Date())
const refreshCountdown = ref(30)
const searchQuery = ref('')
const sortBy = ref('hostname')

const sortedAndFilteredRouters = computed(() => {
  let filtered = routers.value
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(
      (router) =>
        router.hostname.toLowerCase().includes(query) ||
        router.router_id.toString().includes(query,
        ),
    )
  }
  return [...filtered].sort((a, b) => {
    switch (sortBy.value) {
      case 'hostname':
        return a.hostname.localeCompare(b.hostname)
      case 'cpu_usage_5m':
        return (b.cpu_usage_5m ?? 0) - (a.cpu_usage_5m ?? 0)
      case 'mem_used_percent':
        return (b.mem_used_percent ?? 0) - (a.mem_used_percent ?? 0)
      case 'storage_used':
        return (b.storage_used ?? 0) - (a.storage_used ?? 0)
      case 'timestamp':
        return new Date(b.timestamp) - new Date(a.timestamp)
      default:
        return 0
    }
  })
})

const onRowSelect = async (event) => {
  selectedRouter.value = event.data
  await loadRouterDetails(event.data.router_id)
}
const onRowUnselect = () => {
  selectedRouter.value = null
}
const routerRowClass = (data) => ({
  'router-row': true,
  selected: selectedRouter.value?.id === data.id,
  stale: !data.reachable,
})

const loadRouterDetails = async (routerId) => {
  try {
    const [history, interfaces] = await Promise.all([
      monitoringService.getRouterMetrics(routerId, parseInt(timeRange.value)),
      monitoringService.getInterfaceMetrics(),
    ])
    routerHistory.value = Array.isArray(history)
      ? history.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
      : []
    routerInterfaces.value = interfaces.filter((iface) => iface.router_id === routerId)
  } catch (err) {
    error.value = `Error loading router details: ${err.message}`
  }
}
const loadRouterHistory = async () => {
  if (selectedRouter.value) {
    await loadRouterDetails(selectedRouter.value.router_id)
  }
}
const loadDashboardData = async () => {
  try {
    error.value = ''
    const [stats, routerMetrics, routersInfo] = await Promise.all([
      monitoringService.getDashboardStats(),
      monitoringService.getRouterMetrics(),
      fetchRoutersInfo(),
    ])
    dashboardStats.value = stats
    routers.value = routerMetrics.map((metric) => {
      const info = routersInfo.find((r) => r.id === metric.router_id)
      return {
        id: metric.router_id,
        hostname: metric.hostname,
        router_id: metric.router_id,
        reachable: info ? info.reachable : false,
        ...metric,
      }
    })
    lastUpdateTime.value = new Date()
  } catch (err) {
    error.value = `Error loading data: ${err.message}`
  }
}
async function fetchRoutersInfo() {
  const res = await fetch('http://127.0.0.1:8000/api/routers/')
  if (!res.ok) throw new Error('Failed to fetch routers info')
  return await res.json()
}
let refreshInterval = null
let countdownInterval = null
const startAutoRefresh = () => {
  refreshCountdown.value = 30
  refreshInterval = setInterval(async () => {
    await loadDashboardData()
    if (selectedRouter.value) {
      await loadRouterDetails(selectedRouter.value.router_id)
    }
    refreshCountdown.value = 30
  }, 30000)
  countdownInterval = setInterval(() => {
    refreshCountdown.value = Math.max(0, refreshCountdown.value - 1)
  }, 1000)
}
const getMetricAlertClass = (value, alertThreshold, warningThreshold) => {
  if (!value) return ''
  if (value >= alertThreshold) return 'alert'
  if (value >= warningThreshold) return 'warning'
  return ''
}
const formatBandwidth = (bps) => {
  if (!bps) return '0 bps'
  const units = ['bps', 'Kbps', 'Mbps', 'Gbps']
  let i = 0
  while (bps >= 1000 && i < units.length - 1) bps /= 1000, i++
  return `${bps.toFixed(1)} ${units[i]}`
}
const formatBytes = (bytes) => {
  if (!bytes) return '0 B'
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  let i = Math.floor(Math.log(bytes) / Math.log(1024))
  return (bytes / 1024 ** i).toFixed(1) + ' ' + sizes[i]
}
const chartStats = ref({ min: 0, max: 0, avg: 0 })

watch(
  () => [routerHistory.value, selectedMetric.value],
  async () => {
    await nextTick()
    drawChart()
    chartStats.value = getChartStats()
  },
  { deep: true },
)
watch([selectedMetric, timeRange], async () => {
  await loadRouterHistory()
})
onMounted(async () => {
  await loadDashboardData()
  startAutoRefresh()
})
onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
  if (countdownInterval) clearInterval(countdownInterval)
})

const chartData = computed(() => {
  if (!routerHistory.value.length) return { labels: [], datasets: [] }

  const dataPoints = routerHistory.value
    .map((point) => ({
      value: point[selectedMetric.value] || 0,
      timestamp: new Date(point.timestamp),
    }))
    .filter((point) => !isNaN(point.timestamp.getTime()))
    .sort((a, b) => a.timestamp - b.timestamp)

  const labels = dataPoints.map(point =>
    point.timestamp.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  )

  const values = dataPoints.map(point => point.value)

  // Legend thresholds
  const warning = getWarningThreshold()
  const critical = getCriticalThreshold()

  return {
    labels,
    datasets: [
      // Dummy datasets for legend (showLine: false, hidden: false)
      {
        label: `Normal (<${warning}%)`,
        borderColor: 'rgba(40, 167, 69, 1)',
        backgroundColor: 'rgba(40, 167, 69, 0.13)',
        pointBackgroundColor: 'rgba(40, 167, 69, 1)',
        pointBorderColor: 'rgba(40, 167, 69, 1)',
        showLine: false,
        hidden: false,
        data: [],
      },
      {
        label: `Warning (${warning}-${critical}%)`,
        borderColor: 'rgba(255, 193, 7, 1)',
        backgroundColor: 'rgba(255, 193, 7, 0.13)',
        pointBackgroundColor: 'rgba(255, 193, 7, 1)',
        pointBorderColor: 'rgba(255, 193, 7, 1)',
        showLine: false,
        hidden: false,
        data: [],
      },
      {
        label: `Critical (≥${critical}%)`,
        borderColor: 'rgba(220, 53, 69, 1)',
        backgroundColor: 'rgba(220, 53, 69, 0.13)',
        pointBackgroundColor: 'rgba(220, 53, 69, 1)',
        pointBorderColor: 'rgba(220, 53, 69, 1)',
        showLine: false,
        hidden: false,
        data: [],
      },
      // Actual data (label: '' to hide from legend)
      {
        label: '',
        data: values,
        fill: true,
        borderWidth: 3,
        pointBackgroundColor: values.map(v =>
          v >= critical ? 'rgba(220, 53, 69, 1)'
          : v >= warning ? 'rgba(255, 193, 7, 1)'
          : 'rgba(40, 167, 69, 1)'
        ),
        pointBorderColor: values.map(v =>
          v >= critical ? 'rgba(220, 53, 69, 1)'
          : v >= warning ? 'rgba(255, 193, 7, 1)'
          : 'rgba(40, 167, 69, 1)'
        ),
        pointRadius: 1,
        pointHoverRadius: 5,
        showLine: true,
        tension: 0.4,
        spanGaps: true,
        segment: {
          backgroundColor: ctx => {
            const v = ctx.p1.parsed.y
            if (v >= critical) return 'rgba(220, 53, 69, 0.13)'
            if (v >= warning) return 'rgba(255, 193, 7, 0.13)'
            return 'rgba(40, 167, 69, 0.13)'
          },
          borderColor: ctx => {
            const v = ctx.p1.parsed.y
            if (v >= critical) return 'rgba(220, 53, 69, 1)'
            if (v >= warning) return 'rgba(255, 193, 7, 1)'
            return 'rgba(40, 167, 69, 1)'
          }
        }
      }
    ]
  }
})

const chartOptions = computed(() => {
  const warningThreshold = getWarningThreshold()
  const criticalThreshold = getCriticalThreshold()
  
  return {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      intersect: false,
      mode: 'index'
    },
    plugins: {
      legend: {
        display: true,
        labels: {
          usePointStyle: true,
          pointStyleWidth: 2,
          filter: (legendItem, data) => {
            // Only show legend for the first three datasets (the thresholds)
            return legendItem.datasetIndex < 3
          }
        }
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: 'rgba(255, 255, 255, 0.2)',
        borderWidth: 1,
        callbacks: {
          label: function(context) {
            return `${context.dataset.label}: ${context.raw != null ? context.raw.toFixed(1) + '%' : 'N/A'}`
          }
        }
      },
      annotation: {
        annotations: {
          warningLine: {
            type: 'line',
            yMin: warningThreshold,
            yMax: warningThreshold,
            borderColor: 'rgba(255, 193, 7, 0.8)',
            borderWidth: 2,
            borderDash: [5, 5],
            label: {
              display: true,
              content: `Warning (${warningThreshold}%)`,
              position: 'end'
            }
          },
          criticalLine: {
            type: 'line',
            yMin: criticalThreshold,
            yMax: criticalThreshold,
            borderColor: 'rgba(220, 53, 69, 0.8)',
            borderWidth: 2,
            borderDash: [5, 5],
            label: {
              display: true,
              content: `Critical (${criticalThreshold}%)`,
              position: 'end'
            }
          }
        }
      }
    },
    scales: {
      x: {
        display: true,
        title: {
          display: true,
          text: 'Time'
        },
        ticks: {
          maxRotation: 45,
          minRotation: 45
        }
      },
      y: {
        display: true,
        title: {
          display: true,
          text: 'Usage (%)'
        },
        min: 0,
        max: 100,
        ticks: {
          callback: function(value) {
            return value + '%'
          }
        }
      }
    }
  }
})

const getWarningThreshold = () => {
  if (selectedMetric.value.includes('cpu')) return 50
  if (selectedMetric.value.includes('mem') || selectedMetric.value.includes('storage')) return 60
  return 50
}

const getCriticalThreshold = () => {
  if (selectedMetric.value.includes('cpu')) return 70
  if (selectedMetric.value.includes('mem') || selectedMetric.value.includes('storage')) return 80
  return 70
}

const getChartStats = () => {
  const vals = routerHistory.value.map(p => p[selectedMetric.value] || 0).filter(v => v != null)
  if (!vals.length) return { min: 0, max: 0, avg: 0 }
  const min = Math.min(...vals).toFixed(1), max = Math.max(...vals).toFixed(1)
  const avg = (vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(1)
  return { min, max, avg }
}

watch(
  () => [routerHistory.value, selectedMetric.value],
  () => {
    chartStats.value = getChartStats()
  },
  { deep: true }
)

// New: State for selected interface and its history
const selectedInterface = ref(null)
const interfaceHistory = ref([])
const interfaceTimeRange = ref('24')
const interfaceChartData = computed(() => {
  if (!interfaceHistory.value.length) return { labels: [], datasets: [] }
  const dataPoints = interfaceHistory.value
    .map(point => ({
      timestamp: new Date(point.timestamp),
      bps_in: point.bps_in || 0,
      bps_out: point.bps_out || 0,
    }))
    .filter(point => !isNaN(point.timestamp.getTime()))
    .sort((a, b) => a.timestamp - b.timestamp)
  const labels = dataPoints.map(point =>
    point.timestamp.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  )
  return {
    labels,
    datasets: [
      {
        label: 'Inbound Bandwidth',
        data: dataPoints.map(p => p.bps_in),
        fill: 'origin',
        borderColor: 'rgba(40, 167, 69, 1)',
        backgroundColor: 'rgba(40, 167, 69, 0.13)', // greenish
        tension: 0.3,
        pointRadius: 1,
        pointHoverRadius: 4,
      },
      {
        label: 'Outbound Bandwidth',
        data: dataPoints.map(p => p.bps_out),
        fill: 'origin',
        borderColor: 'rgba(0, 123, 255, 1)',
        backgroundColor: 'rgba(0, 123, 255, 0.13)', // blueish
        tension: 0.3,
        pointRadius: 1,
        pointHoverRadius: 4,
      },
    ],
  }
})
const interfaceChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: true,
      labels: { usePointStyle: true }
    },
    tooltip: {
      callbacks: {
        label: function(context) {
          // Format as bandwidth
          const value = context.raw || 0
          if (value >= 1e9) return `${context.dataset.label}: ${(value / 1e9).toFixed(2)} Gbps`
          if (value >= 1e6) return `${context.dataset.label}: ${(value / 1e6).toFixed(2)} Mbps`
          if (value >= 1e3) return `${context.dataset.label}: ${(value / 1e3).toFixed(2)} Kbps`
          return `${context.dataset.label}: ${value} bps`
        }
      }
    }
  },
  scales: {
    x: {
      display: true,
      title: { display: true, text: 'Time' },
      ticks: { maxRotation: 45, minRotation: 45 }
    },
    y: {
      display: true,
      title: { display: true, text: 'Bandwidth (bps)' },
      min: 0,
      ticks: {
        callback: function(value) {
          if (value >= 1e9) return (value / 1e9).toFixed(1) + 'G'
          if (value >= 1e6) return (value / 1e6).toFixed(1) + 'M'
          if (value >= 1e3) return (value / 1e3).toFixed(1) + 'K'
          return value
        }
      }
    }
  }
}

// New: Load interface history when an interface is selected
const loadInterfaceHistory = async (iface) => {
  if (!iface) return
  try {
    const history = await monitoringService.getInterfaceMetrics(iface.interface_id, parseInt(interfaceTimeRange.value))
    interfaceHistory.value = Array.isArray(history)
      ? history.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
      : []
  } catch (err) {
    error.value = `Error loading interface history: ${err.message}`
    interfaceHistory.value = []
  }
}

// Watch for interface selection
watch(selectedInterface, async (iface) => {
  await loadInterfaceHistory(iface)
})

// Watch for interface time range change
watch(interfaceTimeRange, async () => {
  await loadInterfaceHistory(selectedInterface.value)
})

// Clear interface chart/history when router changes
watch(selectedRouter, () => {
  selectedInterface.value = null
  interfaceHistory.value = []
})
</script>

<style scoped>
.performance-chart {
  height: 360px;
  width: 100%;
}

.card.monitoring-card {
  background: var(--surface-card);
  padding: 0;
  position: relative;
  color: var(--text-color);
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: auto;
}

.dashboard {
  padding: 2rem 2.5rem;
  max-width: 100%;
  margin: 0;
  color: var(--text-color);
  flex: 1 1 auto;
  min-height: 0;
  overflow: auto;
}

.stats-section {
  margin-bottom: 1.5rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.25rem;
  margin-bottom: 1.25rem;
}

.stat-card {
  border: 1px solid var(--surface-border, #e5e7eb);
  padding: 1.25rem 1.5rem;
  border-radius: 0.75rem;
  background: var(--surface-ground);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03);
  color: var(--text-color);
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.stat-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.2rem;
}

.stat-header-row h3 {
  margin: 0;
  font-size: 1.15rem;
  color: var(--text-color);
  font-weight: 600;
}

.stat-values {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  min-width: 110px;
}

.stat-main {
  font-size: 1.2rem;
  font-weight: bold;
  margin-bottom: 0.1rem;
  color: var(--text-color);
}

.stat-secondary {
  color: var(--text-secondary-color, #aaa);
  font-size: 0.95em;
}

.stat-card.alert {
  background-color: var(--red-50, #2d1517);
}

.update-info {
  background: var(--surface-ground);
  padding: 1rem 1rem;
  border-radius: 0.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.97em;
  color: var(--text-secondary-color, #aaa);
  border: 1px solid var(--surface-border, #e5e7eb);
}

.router-section {
  margin-bottom: 1.5rem;
}

.devices-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.devices-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-color);
}

.controls {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.controls input,
.controls select {
  padding: 0.5rem 0.9rem;
  border: 1px solid var(--surface-border, #ddd);
  border-radius: 0.4rem;
  font-size: 1rem;
  background: var(--input-bg, var(--surface-card));
  color: var(--text-color);
}

.table-hint-below {
  margin-bottom: 0.5rem;
  color: var(--text-secondary-color, #aaa);
  font-size: 0.98em;
  text-align: left;
}

.router-table {
  width: 100%;
  border-collapse: collapse;
  background: var(--surface-card);
  overflow: hidden;
  color: var(--text-color);
  font-size: 0.93rem;
}

.router-table th {
  background: var(--surface-ground);
  padding: 0.6rem 0.6rem;
  text-align: left;
  font-weight: 600;
  color: var(--text-color);
  border-bottom: 2px solid var(--surface-border, #dee2e6);
  font-size: 0.97rem;
}

:deep(.p-datatable-header-cell) {
  background-color: var(--surface-ground);
  font-size: 0.97rem;
}

:deep(.router-row) {
  cursor: pointer;
  transition: background-color 0.2s;
  font-size: 0.93rem;
}

:deep(.router-row:hover td) {
  background-color: var(--surface-hover, rgba(100, 100, 100, 0.07));
}

:deep(.router-row.selected td) {
  background-color: var(--selected-row-bg, rgba(100, 100, 100, 0.2));
}

:deep(.router-row.selected.stale td) {
  background-color: var(--selected-offline-row-bg, rgba(100, 0, 0, 0.07));
}

:deep(.router-row.stale td) {
  background-color: var(--offline-row-bg, rgba(100, 0, 0, 0.2));
}

:deep(.router-row td) {
  padding: 0.6rem 0.6rem;
  border-bottom: 1px solid var(--surface-border, #dee2e6);
  font-size: 0.93rem;
}

:deep(.router-row small) {
  display: block;
  color: var(--text-secondary-color, #aaa);
  font-size: 0.90em;
}

.status-up {
  color: var(--green-500, #28a745);
}

.status-down {
  color: var(--red-500, #dc3545);
}

.stale {
  color: var(--offline-text, #ff6b6b);
}

.online {
  color: var(--green-500, #28a745);
}

.metric-cell {
  min-width: 120px;
}

.metric-values strong {
  display: block;
  font-size: 1.05rem;
}

.metric-values small {
  display: block;
  color: var(--text-secondary-color, #aaa);
  font-size: 0.93em;
  margin-top: 2px;
}

.usage-bar {
  height: 4px;
  background: var(--surface-border, #e9ecef);
  border-radius: 2px;
  margin-top: 4px;
  overflow: hidden;
}

.usage-fill {
  height: 100%;
  background: var(--primary-color, #007bff);
  transition: width 0.3s ease;
}

.metric-cell.warning .usage-fill {
  background: var(--yellow-500, #ffc107);
}

.metric-cell.alert .usage-fill {
  background: var(--red-500, #dc3545);
}

.details-section {
  background: var(--surface-card);
  border-radius: 0.75rem;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03);
  color: var(--text-color);
}

.current-status {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.7rem;
  margin-bottom: 1.2rem;
}

.status-card {
  background: var(--surface-card);
  border: 1px solid var(--surface-border, #dee2e6);
  border-radius: 0.75rem;
  padding: 1.25rem;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03);
  color: var(--text-color);
}

.status-card h4 {
  margin: 0 0 0.7rem 0;
  color: var(--text-color);
  font-size: 1.08rem;
}

.metric-display {
  text-align: center;
}

.metric-value.large {
  display: block;
  font-size: 2.2rem;
  font-weight: bold;
  margin-bottom: 0.8rem;
  color: var(--green-500, #28a745);
}

.metric-value.warning {
  color: var(--yellow-500, #ffc107);
}

.metric-value.alert {
  color: var(--red-500, #dc3545);
}

.metric-breakdown {
  text-align: left;
  font-size: 1rem;
  color: var(--text-secondary-color, #aaa);
}

.metric-breakdown div {
  margin-bottom: 4px;
  text-align: right;
}

.status-card.usage-card {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0.7rem;
  background: var(--surface-card);
  border: 1px solid var(--surface-border, #e0e0e0);
  border-radius: 0.7rem;
  box-shadow: 0 1px 4px 0 rgba(0, 0, 0, 0.03);
}

.usage-label {
  flex: 1 1 0;
  text-align: left;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-color);
  margin-top: 0.3rem;
}

.usage-circle-outer {
  flex: 1 1 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 60px;
}

.usage-metrics {
  flex: 1 1 0;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-content: flex-end;
}

.usage-bg {
  stroke: var(--surface-border, #e0e0e0);
  opacity: 0.5;
}

.usage-fg {
  stroke: var(--green-500, #28a745);
  transition: stroke 0.2s, stroke-dashoffset 0.5s;
}

.usage-fg.warning {
  stroke: var(--yellow-500, #ffc107);
}

.usage-fg.alert {
  stroke: var(--red-500, #dc3545);
}

.usage-value {
  font-size: 0.9rem;
  font-weight: 700;
  fill: var(--green-500, #28a745);
  pointer-events: none;
  dominant-baseline: middle;
  alignment-baseline: middle;
}

.usage-value.warning {
  fill: var(--yellow-500, #ffc107);
}

.usage-value.alert {
  fill: var(--red-500, #dc3545);
}

.usage-metrics .metric-breakdown {
  margin-top: 0.1rem;
  font-size: 0.90rem;
  color: var(--text-secondary-color, #aaa);
  text-align: left;
  line-height: 1.2;
}

.metrics-chart {
  margin-bottom: 1.5rem;
}

.metrics-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  margin: 1.5rem 0 1rem 0;
}

.metrics-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-color);
}

.chart-controls {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.chart-controls select,
.chart-controls button {
  padding: 0.5rem 0.9rem;
  border: 1px solid var(--surface-border, #ddd);
  border-radius: 0.4rem;
  font-size: 1rem;
  background: var(--input-bg, var(--surface-card));
  color: var(--text-color);
}

.refresh-btn,
.retry-btn {
  background: var(--primary-color, #007bff);
  color: var(--primary-color-text, #fff);
  border: none;
  cursor: pointer;
  border-radius: 0.4rem;
  transition: background 0.15s;
}

.refresh-btn:hover,
.retry-btn:hover {
  background: var(--primary-700, #0056b3);
}

.chart-container {
  background: var(--surface-card);
  border: 1px solid var(--surface-border, #dee2e6);
  border-radius: 0.75rem;
  padding: 1.25rem;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03);
  color: var(--text-color);
}

.no-data {
  text-align: center;
  padding: 2.5rem;
  background: var(--surface-ground);
  border-radius: 0.75rem;
  color: var(--text-secondary-color, #aaa);
}

.interfaces-title {
  margin: 0 0 1.25rem 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-color);
}

.interfaces-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 0.7rem;
}

.interface-card {
  background: var(--surface-card);
  border: 1px solid var(--surface-border, #dee2e6);
  border-radius: 0.6rem;
  /* Remove top padding so header background reaches the top edge */
  padding: 0 1rem 0.6rem 1rem;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
  color: var(--text-color);
  font-size: 0.97rem;
  min-width: 0;
}

.interface-header.compact {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 0;
  /* Extend border to full width */
  margin-left: -1rem;
  margin-right: -1rem;
  padding-top: 0.3rem;
  padding-left: 1rem;
  padding-right: 1rem;
  padding-bottom: 0.4rem;
  border-bottom: 1px solid var(--surface-border, #eee);
  background: var(--surface-ground, #f6f6f6);
  /* Add rounded top corners to match card */
  border-top-left-radius: 0.6rem;
  border-top-right-radius: 0.6rem;
}

.iface-name {
  font-weight: 600;
  font-size: 1.05rem;
  color: var(--text-color);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 160px;
}

.status-up {
  color: var(--green-500, #28a745);
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.93em;
  letter-spacing: 0.5px;
}

.status-down {
  color: var(--red-500, #dc3545);
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.93em;
  letter-spacing: 0.5px;
}

.traffic-total-row.top {
  grid-column: 1 / -1;
  margin: 0.5rem;
  font-size: 1em;
  color: var(--text-color);
  text-align: left;
}

.traffic-metrics.compact-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.2rem 1.2rem;
  margin-bottom: 0.1rem;
  font-size: 0.93em;
}

.traffic-direction {
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  gap: 0.5rem;
}

.direction-label {
  min-width: 1.8em;
  font-weight: 500;
  font-size: 0.9em;
  color: var(--text-secondary-color, #aaa);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.7;
  background: var(--surface-ground, #f6f6f6);
  border-radius: 50%;
  width: 1.8em;
  height: 1.8em;
}

.direction-label.down {
  color: var(--text-secondary-color, #aaa);
  background: var(--surface-ground, #f6f6f6);
}

.direction-label.up {
  color: var(--text-secondary-color, #aaa);
  background: var(--surface-ground, #f6f6f6);
}

.traffic-value {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.traffic-value strong {
  font-size: 1.05em;
  color: var(--text-color);
}

.traffic-value small {
  font-size: 0.93em;
  color: var(--text-secondary-color, #aaa);
}

.traffic-value small.alert {
  color: var(--red-500, #dc3545);
  font-weight: 600;
}

.traffic-total-row {
  margin-top: 0.2rem;
  font-size: 0.98em;
  color: var(--text-color);
  text-align: right;
}

.error-metrics {
  margin-bottom: 0.9rem;
  padding: 0.6rem;
  background: var(--red-50, #2d1517);
  border: 1px solid var(--red-300, #fed7d7);
  border-radius: 0.4rem;
}

.error-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.25rem;
  font-size: 1rem;
}

.error-item.alert {
  color: var(--red-900, #721c24);
}

.error-item.label {
  font-weight: 500;
}

.interface-footer {
  padding-top: 0.6rem;
  border-top: 1px solid var(--surface-border, #dee2e6);
  text-align: center;
}

.error {
  background: var(--red-100, #f8d7da);
  color: var(--red-900, #721c24);
  padding: 0.8rem 1.1rem;
  border: 1px solid var(--red-300, #f5c6cb);
  border-radius: 0.5rem;
  margin: 1.25rem 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.close-error {
  background: none;
  border: none;
  font-size: 1.3rem;
  cursor: pointer;
  padding: 0;
  margin-left: 0.7rem;
  color: var(--text-color);
}

.interface-card.selected {
  background: var(--surface-color, rgba(0, 0, 0, 0.15));
  box-shadow: none;
}

.interface-chart-container {
  background: var(--surface-card);
  border: 1px solid var(--surface-border, #dee2e6);
  border-radius: 0.75rem;
  padding: 1.25rem;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03);
  color: var(--text-color);
}

.interface-bandwidth-chart {
  height: 280px;
  width: 100%;
  margin-top: 0.5rem;
}

@media (max-width: 900px) {
  .card.monitoring-card {
    padding: 1rem 0.5rem;
  }

  .details-section,
  .chart-container,
  .interface-card {
    padding: 1rem;
  }

  .stats-grid,
  .interfaces-grid {
    grid-template-columns: 1fr;
  }

  .traffic-metrics.compact-grid {
    grid-template-columns: 1fr;
  }

  .traffic-total-row.top {
    text-align: left;
  }
}
</style>
