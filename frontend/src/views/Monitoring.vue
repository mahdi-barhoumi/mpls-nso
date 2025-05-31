<template>
  <div class="card monitoring-card">
    <div class="dashboard">
      <!-- NetworkOverview -->
      <div class="stats-section">
        <h3>Monitoring</h3>
        <div class="update-info">
          <p style="margin: 0;">Last updated: {{ formatUtils.formatTimeDetailed(lastUpdateTime) }}</p>
          <p>Next refresh in: {{ refreshCountdown }}s</p>
        </div>
        <div class="stats-grid">
          <div
            class="stat-card"
            :class="{ alert: false }"
          >
            <div class="stat-header-row">
              <h3>Devices</h3>
              <div class="stat-values">
                <span class="stat-main">{{ `${dashboardStats.reachable_routers}/${dashboardStats.total_routers} Online` }}</span>
                <small class="stat-secondary">{{ `${formatUtils.getPercentage(dashboardStats.reachable_routers, dashboardStats.total_routers)}% online` }}</small>
              </div>
            </div>
          </div>
          <div
            class="stat-card"
            :class="{ alert: false }"
          >
            <div class="stat-header-row">
              <h3>Interfaces</h3>
              <div class="stat-values">
                <span class="stat-main">{{ `${dashboardStats.enabled_interfaces}/${dashboardStats.total_interfaces} Active` }}</span>
                <small class="stat-secondary">{{ `${formatUtils.getPercentage(dashboardStats.enabled_interfaces, dashboardStats.total_interfaces)}% active` }}</small>
              </div>
            </div>
          </div>
          <div
            v-if="dashboardStats.high_cpu_routers?.length"
            class="stat-card alert"
          >
            <h3>High CPU Alert</h3>
            <p>{{ `${dashboardStats.high_cpu_routers.length} devices above 70%` }}</p>
            <small>{{ `${formatUtils.getPercentage(dashboardStats.high_cpu_routers.length, dashboardStats.total_routers)}% of network` }}</small>
          </div>
          <div
            v-if="dashboardStats.high_memory_routers?.length"
            class="stat-card alert"
          >
            <h3>Memory Alert</h3>
            <p>{{ `${dashboardStats.high_memory_routers.length} devices above 80%` }}</p>
            <small>{{ `${formatUtils.getPercentage(dashboardStats.high_memory_routers.length, dashboardStats.total_routers)}% of network` }}</small>
          </div>
        </div>
      </div>

      <!-- RouterList -->
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
          <small>Click on a device row to view detailed information and performance history.</small>
        </div>
        <!-- RouterTable: PrimeVue DataTable -->
        <DataTable
          :value="sortedAndFilteredRouters"
          dataKey="id"
          selectionMode="single"
          :selection="selectedRouter"
          @rowSelect="onRowSelect"
          @rowUnselect="onRowUnselect"
          :rowClass="routerRowClass"
          responsiveLayout="scroll"
          showGridlines
          :paginator="true"
          :rows="5"
          :rowsPerPageOptions="[5,10,20,50]"
          class="router-table"
        >
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
                    {{ formatUtils.formatBytes(slotProps.data.mem_used || 0) }} / {{ formatUtils.formatBytes(slotProps.data.mem_total) }}
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
                    {{ formatUtils.formatBytes(slotProps.data.storage_used || 0) }} / {{ formatUtils.formatBytes(slotProps.data.storage_total) }}
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

      <!-- RouterDetails -->
      <div v-if="selectedRouter" class="details-section">
        <h4 style="font-weight: 600; font-size: 1.25rem;">{{ selectedRouter.hostname }} Details</h4>
        <!-- StatusCards -->
        <div class="current-status">
          <div class="status-card">
            <h4>CPU Usage</h4>
            <div class="metric-display">
              <span
                class="metric-value large"
                :class="{
                  alert: selectedRouter.cpu_usage_5m >= 70,
                  warning: selectedRouter.cpu_usage_5m >= 50,
                }"
              >
                {{ formatUtils.formatPercentage(selectedRouter.cpu_usage_5m) }}
              </span>
              <div class="metric-breakdown">
                <div>5 seconds: {{ formatUtils.formatPercentage(selectedRouter.cpu_usage_5s) }}</div>
                <div>1 minute: {{ formatUtils.formatPercentage(selectedRouter.cpu_usage_1m) }}</div>
                <div>5 minutes: {{ formatUtils.formatPercentage(selectedRouter.cpu_usage_5m) }}</div>
              </div>
            </div>
          </div>
          <div class="status-card">
            <h4>Memory Usage</h4>
            <div class="metric-display">
              <span
                class="metric-value large"
                :class="{
                  alert: selectedRouter.mem_used_percent >= 80,
                  warning: selectedRouter.mem_used_percent >= 60,
                }"
              >
                {{ formatUtils.formatPercentage(selectedRouter.mem_used_percent) }}
              </span>
              <div class="metric-breakdown" v-if="selectedRouter.mem_total">
                <div>Used: {{ formatUtils.formatBytes(selectedRouter.mem_used || 0) }}</div>
                <div>Free: {{ formatUtils.formatBytes(selectedRouter.mem_free || 0) }}</div>
                <div>Total: {{ formatUtils.formatBytes(selectedRouter.mem_total) }}</div>
              </div>
            </div>
          </div>
          <div class="status-card">
            <h4>Storage Usage</h4>
            <div class="metric-display">
              <span
                class="metric-value large"
                :class="{
                  alert: selectedRouter.storage_used_percent >= 80,
                  warning: selectedRouter.storage_used_percent >= 60,
                }"
              >
                {{ formatUtils.formatPercentage(selectedRouter.storage_used_percent) }}
              </span>
              <div class="metric-breakdown" v-if="selectedRouter.storage_total">
                <div>Used: {{ formatUtils.formatBytes(selectedRouter.storage_used || 0) }}</div>
                <div>Free: {{ formatUtils.formatBytes(selectedRouter.storage_free || 0) }}</div>
                <div>Total: {{ formatUtils.formatBytes(selectedRouter.storage_total) }}</div>
              </div>
            </div>
          </div>
        </div>
        <!-- PerformanceChart -->
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
            <canvas ref="chartCanvas" width="1000" height="400"></canvas>
            <!-- ChartLegend -->
            <div class="chart-legend">
              <div class="legend-item"><span class="legend-color normal"></span> Normal (&lt; 50%)</div>
              <div class="legend-item"><span class="legend-color warning"></span> Warning (50-70%)</div>
              <div class="legend-item"><span class="legend-color alert"></span> Critical (&gt; 70%)</div>
              <div class="chart-stats">
                Min: {{ chartStats.min }}% | Max: {{ chartStats.max }}% | Avg: {{ chartStats.avg }}%
              </div>
            </div>
          </div>
          <div v-else class="no-data">
            <p>No historical data available for the selected time range</p>
            <button @click="loadRouterHistory" class="retry-btn">Retry Loading</button>
          </div>
        </div>
        <!-- InterfacesList -->
        <div class="interfaces-section">
          <h3>Interfaces</h3>
          <div v-if="routerInterfaces.length" class="interfaces-grid">
            <!-- InterfaceCard -->
            <div
              v-for="iface in routerInterfaces"
              :key="iface.interface_id"
              class="interface-card"
            >
              <div class="interface-header">
                <h4>{{ iface.name }}</h4>
                <span :class="iface.operational_status === 'up' ? 'status-up' : 'status-down'">
                  {{ iface.operational_status }}
                </span>
              </div>
              <div class="interface-metrics">
                <div class="traffic-metrics">
                  <div class="traffic-item">
                    <label>In Traffic:</label>
                    <span>{{ formatBandwidth(iface.bps_in) }}</span>
                  </div>
                  <div class="traffic-item">
                    <label>Out Traffic:</label>
                    <span>{{ formatBandwidth(iface.bps_out) }}</span>
                  </div>
                  <div class="traffic-item">
                    <label>Total Traffic:</label>
                    <span>{{ formatBandwidth((iface.bps_in || 0) + (iface.bps_out || 0)) }}</span>
                  </div>
                  <div class="traffic-item">
                    <label>In Octets:</label>
                    <span>{{ formatBytes(iface.in_octets) }}</span>
                  </div>
                  <div class="traffic-item">
                    <label>Out Octets:</label>
                    <span>{{ formatBytes(iface.out_octets) }}</span>
                  </div>
                  <div class="traffic-item">
                    <label>In Discards:</label>
                    <span>{{ formatBytes(iface.in_discards) }}</span>
                  </div>
                  <div class="traffic-item">
                    <label>Out Discards:</label>
                    <span>{{ formatBytes(iface.out_discards) }}</span>
                  </div>
                  <div class="traffic-item">
                    <label>Errors In:</label>
                    <span>{{ formatBytes(iface.in_errors) }}</span>
                  </div>
                  <div class="traffic-item">
                    <label>Errors Out:</label>
                    <span>{{ formatBytes(iface.out_errors) }}</span>
                  </div>
                </div>
                <div
                  class="error-metrics"
                  v-if="(iface.in_errors || 0) + (iface.out_errors || 0) > 0"
                >
                  <div class="error-item alert">
                    <label>Errors In:</label>
                    <span>{{ formatBytes(iface.in_errors) }}</span>
                  </div>
                  <div class="error-item alert">
                    <label>Errors Out:</label>
                    <span>{{ formatBytes(iface.out_errors) }}</span>
                  </div>
                </div>
                <div class="interface-footer">
                </div>
              </div>
            </div>
          </div>
          <div v-else class="no-data">
            <p>No interface data available</p>
          </div>
        </div>
      </div>

      <!-- ErrorDisplay -->
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

// --- formatUtils (from utils/formatUtils.js) ---
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
  getDataAge(timestamp) {
    if (!timestamp) return 'Unknown'
    const diffMs = new Date() - new Date(timestamp)
    const diffMins = Math.floor(diffMs / 60000)
    if (diffMins < 1) return 'Fresh'
    if (diffMins < 5) return 'Recent'
    if (diffMins < 30) return 'Stale'
    return 'Very Stale'
  },
  isDataStale(timestamp) {
    if (!timestamp) return true
    const diffMs = new Date() - new Date(timestamp)
    return diffMs > 300000 // 5 minutes
  },
  formatBytes(kb) {
    // Interpret input as kilobytes, convert to bytes
    if (!kb) return '0 B'
    const bytes = kb * 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(1024))
    return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + sizes[i]
  },
}

// --- State ---
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

// --- RouterList logic ---
const searchQuery = ref('')
const sortBy = ref('hostname')
const sortedAndFilteredRouters = computed(() => {
  // Always filter and sort, regardless of searchQuery
  let filtered = routers.value
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(
      (router) =>
        router.hostname.toLowerCase().includes(query) ||
        router.router_id.toString().includes(query),
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

// DataTable selection handlers
const onRowSelect = async (event) => {
  selectedRouter.value = event.data
  console.log(selectedRouter.value)
  await loadRouterDetails(event.data.router_id)
}
const onRowUnselect = () => {
  selectedRouter.value = null
}

// DataTable row class for styling
const routerRowClass = (data) => {
  return {
    'router-row': true,
    selected: selectedRouter.value?.id === data.id,
    stale: !data.reachable,
  }
}

// --- Methods ---
const handleRouterSelected = async (router) => {
  selectedRouter.value = router
  await loadRouterDetails(router.router_id)
}
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
    // Fetch both router metrics and router info to get 'reachable'
    const [stats, routerMetrics, routersInfo] = await Promise.all([
      monitoringService.getDashboardStats(),
      monitoringService.getRouterMetrics(),
      fetchRoutersInfo(),
    ])
    dashboardStats.value = stats
    // Merge 'reachable' from routersInfo into routerMetrics
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

// Helper to fetch router info (for 'reachable' status)
async function fetchRoutersInfo() {
  // Use the RouterService to fetch all routers (which includes 'reachable')
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

// --- MetricCell helper ---
const getMetricAlertClass = (value, alertThreshold, warningThreshold) => {
  if (!value) return ''
  if (value >= alertThreshold) return 'alert'
  if (value >= warningThreshold) return 'warning'
  return ''
}

// --- InterfaceCard helper ---
const formatBandwidth = (bps) => {
  if (!bps) return '0 bps'
  const units = ['bps', 'Kbps', 'Mbps', 'Gbps']
  let value = bps
  let unitIndex = 0
  while (value >= 1000 && unitIndex < units.length - 1) {
    value /= 1000
    unitIndex++
  }
  return `${value.toFixed(1)} ${units[unitIndex]}`
}
const formatBytes = (bytes) => {
  if (!bytes) return '0 B'
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + sizes[i]
}
const formatNumber = (num) => {
  if (num === null || num === undefined) return '0'
  return num.toLocaleString()
}

// --- Chart logic (PerformanceChart) ---
const chartCanvas = ref(null)
const chartStats = ref({ min: 0, max: 0, avg: 0 })
const getChartStats = () => {
  if (!routerHistory.value.length) return { min: 0, max: 0, avg: 0 }
  const values = routerHistory.value
    .map((point) => point[selectedMetric.value] || 0)
    .filter((val) => val !== null && val !== undefined)
  if (values.length === 0) return { min: 0, max: 0, avg: 0 }
  const min = Math.min(...values).toFixed(1)
  const max = Math.max(...values).toFixed(1)
  const avg = (values.reduce((a, b) => a + b, 0) / values.length).toFixed(1)
  return { min, max, avg }
}
const getThemeColor = (cssVar, fallback) => {
  if (typeof window === 'undefined') return fallback
  const val = getComputedStyle(document.documentElement).getPropertyValue(cssVar)
  return val ? val.trim() : fallback
}
const drawChart = () => {
  if (!chartCanvas.value || !routerHistory.value.length) return
  const canvas = chartCanvas.value
  const ctx = canvas.getContext('2d')
  const width = canvas.width
  const height = canvas.height
  ctx.clearRect(0, 0, width, height)
  const dataPoints = routerHistory.value
    .map((point) => ({
      value: point[selectedMetric.value] || 0,
      timestamp: new Date(point.timestamp),
    }))
    .filter((point) => !isNaN(point.timestamp.getTime()))
  if (dataPoints.length === 0) return
  const padding = 70
  const chartWidth = width - 2 * padding
  const chartHeight = height - 2 * padding
  const values = dataPoints.map((p) => p.value)
  const maxValue = Math.max(...values, 100)
  const minValue = Math.min(...values, 0)
  const valueRange = maxValue - minValue || 1
  const minTime = Math.min(...dataPoints.map((p) => p.timestamp.getTime()))
  const maxTime = Math.max(...dataPoints.map((p) => p.timestamp.getTime()))
  const timeRangeVal = maxTime - minTime || 1

  // Use theme variables for chart background and grid
  ctx.fillStyle = getThemeColor('--surface-card', '#fafafa')
  ctx.fillRect(padding, padding, chartWidth, chartHeight)
  ctx.strokeStyle = getThemeColor('--surface-border', '#e0e0e0')
  ctx.lineWidth = 1
  ctx.fillStyle = getThemeColor('--text-color', '#666')
  ctx.font = '12px Arial'
  for (let i = 0; i <= 5; i++) {
    const y = padding + (i * chartHeight) / 5
    ctx.beginPath()
    ctx.moveTo(padding, y)
    ctx.lineTo(width - padding, y)
    ctx.stroke()
    const value = maxValue - (i * valueRange) / 5
    ctx.fillText(value.toFixed(1) + '%', 5, y + 4)
  }
  const timeLabels = Math.min(8, dataPoints.length)
  for (let i = 0; i <= timeLabels; i++) {
    const x = padding + (i * chartWidth) / timeLabels
    ctx.beginPath()
    ctx.moveTo(x, padding)
    ctx.lineTo(x, height - padding)
    ctx.stroke()
    if (i > 0 && i < timeLabels) {
      const timePoint = new Date(minTime + (i * timeRangeVal) / timeLabels)
      const timeLabel = timePoint.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
      ctx.save()
      ctx.translate(x, height - padding + 15)
      ctx.rotate(-Math.PI / 4)
      ctx.fillText(timeLabel, 0, 0)
      ctx.restore()
    }
  }
  const drawThresholdLine = (threshold, colorVar, label) => {
    const color = getThemeColor(colorVar, colorVar)
    const y = padding + chartHeight - ((threshold - minValue) / valueRange) * chartHeight
    if (y >= padding && y <= padding + chartHeight) {
      ctx.strokeStyle = color
      ctx.lineWidth = 1
      ctx.setLineDash([5, 5])
      ctx.beginPath()
      ctx.moveTo(padding, y)
      ctx.lineTo(width - padding, y)
      ctx.stroke()
      ctx.setLineDash([])
      ctx.fillStyle = color
      ctx.font = '11px Arial'
      ctx.fillText(label, width - padding + 5, y + 4)
    }
  }
  if (selectedMetric.value.includes('cpu')) {
    drawThresholdLine(50, '--yellow-500', 'Warning (50%)')
    drawThresholdLine(70, '--red-500', 'Critical (70%)')
  } else if (selectedMetric.value.includes('mem') || selectedMetric.value.includes('storage')) {
    drawThresholdLine(60, '--yellow-500', 'Warning (60%)')
    drawThresholdLine(80, '--red-500', 'Critical (80%)')
  }
  ctx.fillStyle = getThemeColor('--primary-50', 'rgba(0, 123, 255, 0.1)')
  ctx.beginPath()
  dataPoints.forEach((point, index) => {
    const x = padding + ((point.timestamp.getTime() - minTime) / timeRangeVal) * chartWidth
    const y = padding + chartHeight - ((point.value - minValue) / valueRange) * chartHeight
    if (index === 0) {
      ctx.moveTo(x, y)
    } else {
      ctx.lineTo(x, y)
    }
  })
  ctx.lineTo(padding + chartWidth, padding + chartHeight)
  ctx.lineTo(padding, padding + chartHeight)
  ctx.closePath()
  ctx.fill()
  ctx.strokeStyle = getThemeColor('--primary-color', '#007bff')
  ctx.lineWidth = 3
  ctx.beginPath()
  dataPoints.forEach((point, index) => {
    const x = padding + ((point.timestamp.getTime() - minTime) / timeRangeVal) * chartWidth
    const y = padding + chartHeight - ((point.value - minValue) / valueRange) * chartHeight
    if (index === 0) {
      ctx.moveTo(x, y)
    } else {
      ctx.lineTo(x, y)
    }
  })
  ctx.stroke()
  ctx.fillStyle = getThemeColor('--primary-color', '#007bff')
  dataPoints.forEach((point) => {
    const x = padding + ((point.timestamp.getTime() - minTime) / timeRangeVal) * chartWidth
    const y = padding + chartHeight - ((point.value - minValue) / valueRange) * chartHeight
    ctx.beginPath()
    ctx.arc(x, y, 4, 0, 2 * Math.PI)
    ctx.fill()
  })
  ctx.fillStyle = getThemeColor('--text-color', '#333')
  ctx.font = 'bold 16px Arial'
  const title = selectedMetric.value.replace(/_/g, ' ').toUpperCase()
  ctx.fillText(title, padding, 25)
  const currentValue = dataPoints[dataPoints.length - 1]?.value || 0
  ctx.font = 'bold 14px Arial'
  ctx.fillStyle =
    currentValue >= 70
      ? getThemeColor('--red-500', '#ff4444')
      : currentValue >= 50
      ? getThemeColor('--yellow-500', '#ffa500')
      : getThemeColor('--green-500', '#28a745')
  ctx.fillText(`Current: ${currentValue.toFixed(1)}%`, width - 150, 25)
  ctx.fillStyle = getThemeColor('--text-secondary-color', '#666')
  ctx.font = '12px Arial'
  ctx.fillText(`${dataPoints.length} data points`, width - 150, 45)
  chartStats.value = getChartStats()
}
watch(
  () => [routerHistory.value, selectedMetric.value],
  async () => {
    await nextTick()
    drawChart()
    chartStats.value = getChartStats()
  },
  { deep: true },
)

// Update chart data when dropdowns change
watch([selectedMetric, timeRange], async () => {
  await loadRouterHistory()
})

// --- Lifecycle ---
onMounted(async () => {
  await loadDashboardData()
  startAutoRefresh()
})
onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
  if (countdownInterval) clearInterval(countdownInterval)
})
</script>

<style scoped>
/* Card container for floating effect */
.card.monitoring-card {
  background: var(--surface-card);
  padding: 2rem 2.5rem;
  min-width: 0;
  min-height: 0;
  position: relative;
  color: var(--text-color);
}

/* Dashboard */
.dashboard {
  padding: 0;
  max-width: 100%;
  margin: 0;
  color: var(--text-color);
}

/* StatCard, NetworkOverview */
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
  margin-top: 1rem; 
  border-radius: 0.75rem;
  background: var(--surface-ground);
  box-shadow: 0 1px 4px rgba(0,0,0,0.03);
  transition: box-shadow 0.15s;
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
.stat-card h3 {
  margin: 0 0 0.5rem 0;
  color: var(--text-color);
  font-size: 1.15rem;
}
.stat-card p {
  margin: 0 0 0.25rem 0;
  font-size: 1.2rem;
  font-weight: bold;
}
.stat-card small {
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
  border: 1px solid var(--surface-border, #e5e7eb); /* Added border for outline */
}

/* RouterList, RouterTable, RouterRow */
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
  margin-bottom: 0; /* Remove margin so it doesn't add extra space in header row */
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
  font-size: 0.93rem; /* smaller font size */
}
.router-table th {
  background: var(--surface-ground);
  padding: 0.6rem 0.6rem; /* reduced padding */
  text-align: left;
  font-weight: 600;
  color: var(--text-color);
  border-bottom: 2px solid var(--surface-border, #dee2e6);
  font-size: 0.97rem; /* slightly smaller */
}

:deep(.p-datatable-header-cell) {
  background-color: var(--surface-ground);
  font-size: 0.97rem; /* smaller header font */
}

:deep(.router-row) {
  cursor: pointer;
  transition: background-color 0.2s;
  font-size: 0.93rem; /* smaller row font */
}
:deep(.router-row:hover td) {
  background-color: var(--surface-hover, rgba(100,100,100,0.07));
}
:deep(.router-row.selected td) {
  background-color: var(--selected-row-bg, rgba(100,100,100,0.2));
}
:deep(.router-row.selected.stale td) {
  background-color: var(--selected-offline-row-bg, rgba(100,0,0,0.07));
}
:deep(.router-row.stale td) {
  background-color: var(--offline-row-bg, rgba(100,0,0,0.2));
}
:deep(.router-row td) {
  padding: 0.6rem 0.6rem; /* reduced padding */
  border-bottom: 1px solid var(--surface-border, #dee2e6);
  font-size: 0.93rem; /* smaller cell font */
}
:deep(.router-row small) {
  display: block;
  color: var(--text-secondary-color, #aaa);
  font-size: 0.90em; /* slightly smaller */
}
.status-up {
  color: var(--green-500, #28a745);
}
.status-down {
  color: var(--red-500, #dc3545);
}
.stale {
  /* Improved offline text color for dark/light modes */
  color: var(--offline-text, #ff6b6b);
}
.online {
  color: var(--green-500, #28a745);
}

/* MetricCell */
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

/* RouterDetails, StatusCards */
.details-section {
  background: var(--surface-card);
  border-radius: 0.75rem;
  box-shadow: 0 1px 4px rgba(0,0,0,0.03);
  color: var(--text-color);
}
.current-status {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.25rem;
  margin-bottom: 2rem;
}
.status-card {
  background: var(--surface-card);
  border: 1px solid var(--surface-border, #dee2e6);
  border-radius: 0.75rem;
  padding: 1.25rem;
  box-shadow: 0 1px 4px rgba(0,0,0,0.03);
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
}

/* PerformanceChart, ChartLegend */
.metrics-chart {
  margin-bottom: 2.5rem;
}
.metrics-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.25rem;
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
  box-shadow: 0 1px 4px rgba(0,0,0,0.03);
  color: var(--text-color);
}
.no-data {
  text-align: center;
  padding: 2.5rem;
  background: var(--surface-ground);
  border-radius: 0.75rem;
  color: var(--text-secondary-color, #aaa);
}
.chart-legend {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--surface-border, #dee2e6);
  font-size: 1rem;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}
.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 2px;
}
.legend-color.normal {
  background: var(--green-500, #28a745);
}
.legend-color.warning {
  background: var(--yellow-500, #ffc107);
}
.legend-color.alert {
  background: var(--red-500, #dc3545);
}
.chart-stats {
  font-weight: 600;
  color: var(--text-color);
}

/* InterfacesList, InterfaceCard */
.interfaces-section {
  margin-top: 2.5rem;
}
.interfaces-section h3 {
  margin-bottom: 1.25rem;
  color: var(--text-color);
}
.interfaces-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1.25rem;
}
.interface-card {
  background: var(--surface-card);
  border: 1px solid var(--surface-border, #dee2e6);
  border-radius: 0.75rem;
  padding: 1.25rem;
  box-shadow: 0 1px 4px rgba(0,0,0,0.03);
  color: var(--text-color);
}
.interface-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.9rem;
  padding-bottom: 0.6rem;
  border-bottom: 1px solid var(--surface-border, #dee2e6);
}
.interface-header h4 {
  margin: 0;
  color: var(--text-color);
}
.status-up {
  color: var(--green-500, #28a745);
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.95em;
}
.status-down {
  color: var(--red-500, #dc3545);
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.95em;
}
.traffic-metrics {
  margin-bottom: 0.9rem;
}
.traffic-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font-size: 1rem;
}
.traffic-item label {
  color: var(--text-secondary-color, #aaa);
  font-weight: 500;
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

/* ErrorDisplay */
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

/* Responsive tweaks */
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
}
</style>
