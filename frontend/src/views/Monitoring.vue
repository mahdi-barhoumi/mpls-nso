<template>
  <div class="dashboard">
    <NetworkOverview
      :stats="dashboardStats"
      :last-update="lastUpdateTime"
      :refresh-countdown="refreshCountdown"
    />

    <RouterList
      :routers="routers"
      :selected-router="selectedRouter"
      @router-selected="handleRouterSelected"
    />

    <RouterDetails
      v-if="selectedRouter"
      :router="selectedRouter"
      :history="routerHistory"
      :interfaces="routerInterfaces"
      :selected-metric="selectedMetric"
      :time-range="timeRange"
      @metric-changed="selectedMetric = $event"
      @time-range-changed="timeRange = $event"
      @refresh-history="loadRouterHistory"
    />

    <ErrorDisplay v-if="error" :error="error" @close="error = ''" />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import NetworkOverview from '@/components/monitoring/NetworkOverview.vue'
import RouterList from '@/components/monitoring/RouterList.vue'
import RouterDetails from '@/components/monitoring/RouterDetails.vue'
import ErrorDisplay from '@/components/monitoring/ErrorDisplay.vue'
import MonitoringService from '@/service/MonitoringService'

const monitoringService = new MonitoringService()

// State
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

// Methods
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

    const [stats, routerMetrics] = await Promise.all([
      monitoringService.getDashboardStats(),
      monitoringService.getRouterMetrics(),
    ])

    dashboardStats.value = stats
    routers.value = routerMetrics.map((metric) => ({
      id: metric.router_id,
      hostname: metric.hostname,
      router_id: metric.router_id,
      ...metric,
    }))

    lastUpdateTime.value = new Date()
  } catch (err) {
    error.value = `Error loading data: ${err.message}`
  }
}

// Auto-refresh logic
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

// Lifecycle
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
.dashboard {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}
</style>
