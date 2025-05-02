<template>
  <div class="grid grid-cols-12 gap-4">
    <!-- Summary Statistics -->
    <div class="col-span-12">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="card">
          <div class="flex justify-between mb-3">
            <div>
              <span class="block text-500">Total Routers</span>
              <span class="text-900 text-xl font-medium">{{ stats.total_routers }}</span>
            </div>
            <div
              class="flex items-center justify-center bg-blue-100 dark:bg-blue-400/10 rounded-lg w-10 h-10"
            >
              <i class="pi pi-server text-blue-500"></i>
            </div>
          </div>
          <span class="text-green-500 font-medium">{{ stats.reachable_routers }} Online</span>
        </div>

        <div class="card">
          <div class="flex justify-between mb-3">
            <div>
              <span class="block text-500">Total Interfaces</span>
              <span class="text-900 text-xl font-medium">{{ stats.total_interfaces }}</span>
            </div>
            <div
              class="flex items-center justify-center bg-purple-100 dark:bg-purple-400/10 rounded-lg w-10 h-10"
            >
              <i class="pi pi-sitemap text-purple-500"></i>
            </div>
          </div>
          <span class="text-green-500 font-medium">{{ stats.enabled_interfaces }} Active</span>
        </div>

        <div class="card">
          <div class="flex justify-between mb-3">
            <div>
              <span class="block text-500">High CPU Usage</span>
              <span class="text-900 text-xl font-medium">{{ stats.high_cpu_routers.length }}</span>
            </div>
            <div
              class="flex items-center justify-center bg-orange-100 dark:bg-orange-400/10 rounded-lg w-10 h-10"
            >
              <i class="pi pi-bolt text-orange-500"></i>
            </div>
          </div>
          <span class="text-orange-500 font-medium">Routers Above 70%</span>
        </div>

        <div class="card">
          <div class="flex justify-between mb-3">
            <div>
              <span class="block text-500">Memory Alerts</span>
              <span class="text-900 text-xl font-medium">{{
                stats.high_memory_routers.length
              }}</span>
            </div>
            <div
              class="flex items-center justify-center bg-red-100 dark:bg-red-400/10 rounded-lg w-10 h-10"
            >
              <i class="pi pi-exclamation-triangle text-red-500"></i>
            </div>
          </div>
          <span class="text-red-500 font-medium">Routers Above 80%</span>
        </div>
      </div>
    </div>

    <!-- Router Metrics -->
    <div class="col-span-12 xl:col-span-8">
      <div class="card">
        <div class="flex justify-between items-center mb-4">
          <h5 class="text-xl m-0">{{ viewTitles[selectedView.value] }}</h5>
          <div class="flex gap-2">
            <Dropdown v-model="selectedView" :options="viewOptions" optionLabel="name" />
            <template v-if="selectedView.value === 'performance'">
              <Dropdown v-model="selectedMetric" :options="metricOptions" optionLabel="name" />
              <Dropdown v-model="selectedTimeRange" :options="timeRanges" optionLabel="name" />
            </template>
          </div>
        </div>

        <!-- Performance Chart View -->
        <div v-if="selectedView.value === 'performance'" class="h-[400px]">
          <Chart type="line" :data="chartData" :options="chartOptions" />
        </div>

        <!-- Interface Status View -->
        <div v-if="selectedView.value === 'interfaces'" class="h-[400px]">
          <DataTable
            :value="interfaceMetrics"
            :scrollable="true"
            scrollHeight="400px"
            class="p-datatable-sm"
            :loading="loading"
            v-model:filters="filters"
            filterDisplay="menu"
            :globalFilterFields="['name', 'router_hostname', 'operational_status']"
          >
            <template #header>
              <div class="flex justify-between">
                <span class="p-input-icon-left">
                  <i class="pi pi-search" />
                  <InputText v-model="filters['global'].value" placeholder="Search interfaces..." />
                </span>
              </div>
            </template>

            <Column field="router_hostname" header="Router" frozen sortable />
            <Column field="name" header="Interface" sortable />
            <Column field="operational_status" header="Status" sortable>
              <template #body="slotProps">
                <Tag
                  :severity="slotProps.data.operational_status === 'ready' ? 'success' : 'danger'"
                  :value="slotProps.data.operational_status"
                />
              </template>
            </Column>
            <Column field="bps_in" header="Incoming (bps)" sortable>
              <template #body="slotProps">
                {{ formatBandwidth(slotProps.data.bps_in) }}
              </template>
            </Column>
            <Column field="bps_out" header="Outgoing (bps)" sortable>
              <template #body="slotProps">
                {{ formatBandwidth(slotProps.data.bps_out) }}
              </template>
            </Column>
          </DataTable>
        </div>

        <!-- Detailed Metrics View -->
        <div v-if="selectedView.value === 'details'" class="h-[400px] overflow-y-auto">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div v-for="router in routerMetrics" :key="router.id" class="card p-4">
              <h6 class="mb-3">{{ router.hostname }}</h6>
              <div class="space-y-4">
                <!-- CPU Details -->
                <div>
                  <div class="text-sm text-500 mb-1">CPU Usage</div>
                  <div class="flex justify-between">
                    <span>5s: {{ router.cpu_usage_5s }}%</span>
                    <span>1m: {{ router.cpu_usage_1m }}%</span>
                    <span>5m: {{ router.cpu_usage_5m }}%</span>
                  </div>
                </div>
                <!-- Memory Details -->
                <div>
                  <div class="text-sm text-500 mb-1">Memory</div>
                  <div class="space-y-1">
                    <div class="flex justify-between">
                      <span>Total:</span>
                      <span>{{ formatBytes(router.mem_total) }}</span>
                    </div>
                    <div class="flex justify-between">
                      <span>Used:</span>
                      <span>{{ formatBytes(router.mem_used) }}</span>
                    </div>
                    <div class="flex justify-between">
                      <span>Free:</span>
                      <span>{{ formatBytes(router.mem_free) }}</span>
                    </div>
                  </div>
                </div>
                <!-- Storage Details -->
                <div>
                  <div class="text-sm text-500 mb-1">Storage</div>
                  <div class="space-y-1">
                    <div class="flex justify-between">
                      <span>Total:</span>
                      <span>{{ formatBytes(router.storage_total) }}</span>
                    </div>
                    <div class="flex justify-between">
                      <span>Used:</span>
                      <span>{{ formatBytes(router.storage_used) }}</span>
                    </div>
                    <div class="flex justify-between">
                      <span>Free:</span>
                      <span>{{ formatBytes(router.storage_free) }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Router List -->
    <div class="col-span-12 xl:col-span-4">
      <div class="card">
        <DataTable
          :value="routerMetrics"
          :scrollable="true"
          scrollHeight="400px"
          class="p-datatable-sm"
          :loading="loading"
          sortField="cpu_usage_5m"
          :sortOrder="-1"
          selectionMode="single"
          v-model:selection="selectedRouter"
          @row-select="onRouterSelect"
        >
          <Column field="hostname" header="Router" frozen>
            <template #body="slotProps">
              <div class="flex items-center gap-2">
                <i
                  :class="[
                    'pi',
                    slotProps.data.reachable
                      ? 'pi-check-circle text-green-500'
                      : 'pi-times-circle text-red-500',
                  ]"
                ></i>
                <span>{{ slotProps.data.hostname }}</span>
              </div>
            </template>
          </Column>
          <Column field="cpu_usage_5m" header="CPU" sortable>
            <template #body="slotProps">
              <ProgressBar
                :value="slotProps.data.cpu_usage_5m"
                :class="{
                  'bg-red-100': slotProps.data.cpu_usage_5m >= 90,
                  'bg-orange-100':
                    slotProps.data.cpu_usage_5m >= 70 && slotProps.data.cpu_usage_5m < 90,
                }"
              />
            </template>
          </Column>
          <Column field="mem_used_percent" header="Memory" sortable>
            <template #body="slotProps">
              <ProgressBar
                :value="slotProps.data.mem_used_percent"
                :class="{
                  'bg-red-100': slotProps.data.mem_used_percent >= 90,
                  'bg-orange-100':
                    slotProps.data.mem_used_percent >= 80 && slotProps.data.mem_used_percent < 90,
                }"
              />
            </template>
          </Column>
        </DataTable>
      </div>
    </div>

    <!-- Interface Metrics -->
    <div class="col-span-12">
      <div class="card">
        <div class="flex justify-between items-center mb-4">
          <h5 class="text-xl m-0">
            Interface Status
            <span v-if="selectedRouter" class="text-primary text-lg ml-2">
              ({{ selectedRouter.hostname }})
            </span>
          </h5>
          <div class="flex gap-2">
            <Button icon="pi pi-refresh" @click="refreshData" text />
            <Button icon="pi pi-download" @click="exportData" text />
          </div>
        </div>
        <DataTable
          :value="interfaceMetrics"
          :scrollable="true"
          scrollHeight="400px"
          class="p-datatable-sm"
          :loading="loading"
          v-model:filters="filters"
          filterDisplay="menu"
          :globalFilterFields="['name', 'router_hostname', 'operational_status']"
        >
          <template #header>
            <div class="flex justify-between">
              <span class="p-input-icon-left">
                <i class="pi pi-search" />
                <InputText v-model="filters['global'].value" placeholder="Search interfaces..." />
              </span>
            </div>
          </template>

          <Column field="router_hostname" header="Router" frozen sortable />
          <Column field="name" header="Interface" sortable />
          <Column field="operational_status" header="Status" sortable>
            <template #body="slotProps">
              <Tag
                :severity="slotProps.data.operational_status === 'ready' ? 'success' : 'danger'"
                :value="slotProps.data.operational_status"
              />
            </template>
          </Column>
          <Column field="bps_in" header="Incoming (bps)" sortable>
            <template #body="slotProps">
              {{ formatBandwidth(slotProps.data.bps_in) }}
            </template>
          </Column>
          <Column field="bps_out" header="Outgoing (bps)" sortable>
            <template #body="slotProps">
              {{ formatBandwidth(slotProps.data.bps_out) }}
            </template>
          </Column>
        </DataTable>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useToast } from 'primevue/usetoast'
import { FilterMatchMode } from '@primevue/core/api'
import Chart from 'primevue/chart'
import ProgressBar from 'primevue/progressbar'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dropdown from 'primevue/dropdown'
import Tag from 'primevue/tag'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import MonitoringService from '@/service/MonitoringService'
import 'chartjs-adapter-date-fns'
import { enUS } from 'date-fns/locale'

const monitoringService = new MonitoringService()
const toast = useToast()
const loading = ref(false)
const updateInterval = ref(null)
const stats = ref({
  total_routers: 0,
  reachable_routers: 0,
  total_interfaces: 0,
  enabled_interfaces: 0,
  high_cpu_routers: [],
  high_memory_routers: [],
  high_storage_routers: [],
})

const routerMetrics = ref([])
const interfaceMetrics = ref([])
const selectedMetric = ref({ name: 'CPU Usage', value: 'cpu' })
const selectedTimeRange = ref({ name: 'Last 24h', value: 24 })
const selectedRouter = ref(null)

const metricOptions = [
  { name: 'CPU Usage', value: 'cpu' },
  { name: 'Memory Usage', value: 'memory' },
  { name: 'Storage Usage', value: 'storage' },
]

const timeRanges = [
  { name: 'Last Hour', value: 1 },
  { name: 'Last 6h', value: 6 },
  { name: 'Last 24h', value: 24 },
]

const filters = ref({
  global: { value: null, matchMode: FilterMatchMode.CONTAINS },
})

const chartData = ref({
  labels: [],
  datasets: [],
})

const chartOptions = {
  plugins: {
    legend: {
      position: 'bottom',
    },
    tooltip: {
      mode: 'index',
      intersect: false,
      callbacks: {
        label: function (context) {
          return `${context.dataset.label}: ${context.parsed.y}%`
        },
      },
    },
  },
  scales: {
    y: {
      min: 0,
      max: 100,
      ticks: {
        stepSize: 20,
        callback: function (value) {
          return value + '%'
        },
      },
    },
    x: {
      type: 'time',
      adapters: {
        date: {
          locale: enUS,
        },
      },
      time: {
        unit: 'hour',
        displayFormats: {
          hour: 'HH:mm',
        },
      },
      title: {
        display: true,
        text: 'Time',
      },
    },
  },
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    intersect: false,
    mode: 'index',
  },
}

// Add new view options
const selectedView = ref({ name: 'Performance', value: 'performance' })
const viewOptions = [
  { name: 'Performance', value: 'performance' },
  { name: 'Interfaces', value: 'interfaces' },
  { name: 'Detailed Metrics', value: 'details' },
]

const viewTitles = {
  performance: 'Router Performance',
  interfaces: 'Interface Status',
  details: 'Detailed Router Metrics',
}

// Add bytes formatter
const formatBytes = (bytes) => {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${units[i]}`
}

// Format bandwidth values using service
const formatBandwidth = (bps) => monitoringService.formatBandwidth(bps)

// Fetch dashboard stats
const fetchStats = async () => {
  try {
    stats.value = await monitoringService.getDashboardStats()
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: error.message,
      life: 3000,
    })
  }
}

// Fetch router metrics
const fetchRouterMetrics = async () => {
  try {
    loading.value = true
    routerMetrics.value = await monitoringService.getRouterMetrics()
    updateChart()
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: error.message,
      life: 3000,
    })
  } finally {
    loading.value = false
  }
}

// Fetch interface metrics
const fetchInterfaceMetrics = async () => {
  try {
    loading.value = true
    interfaceMetrics.value = await monitoringService.getInterfaceMetrics()
    if (selectedRouter.value) {
      interfaceMetrics.value = interfaceMetrics.value.filter(
        (i) => i.router_id === selectedRouter.value.id,
      )
    }
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: error.message,
      life: 3000,
    })
  } finally {
    loading.value = false
  }
}

// Update chart data processing
let chartInstance = null

const updateChart = async () => {
  try {
    // Destroy existing chart instance if it exists
    if (chartInstance) {
      chartInstance.destroy()
      chartInstance = null
    }

    const hours = selectedTimeRange.value.value
    const routerId = selectedRouter.value?.id
    const metrics = await monitoringService.getRouterMetrics(routerId, hours)

    const timestamps = metrics.map((m) => new Date(m.timestamp))
    const metricKey =
      selectedMetric.value.value === 'cpu'
        ? 'cpu_usage_5m'
        : selectedMetric.value.value === 'memory'
          ? 'mem_used_percent'
          : 'storage_used_percent'

    let datasets = []
    if (selectedMetric.value.value === 'storage') {
      datasets = [
        {
          label: 'Storage Usage',
          data: metrics.map((m) => m.storage_used_percent),
          borderColor: 'var(--primary-color)',
          backgroundColor: 'rgba(var(--primary-color-rgb), 0.1)',
          tension: 0.4,
          fill: true,
        },
        {
          label: 'Total Storage (GB)',
          data: metrics.map((m) => (m.storage_total / (1024 * 1024 * 1024)).toFixed(2)),
          borderColor: 'var(--success-color)',
          borderDash: [5, 5],
          tension: 0.4,
          fill: false,
          yAxisID: 'storage',
        },
      ]
    } else {
      datasets = [
        {
          label: selectedMetric.value.name,
          data: metrics.map((m) => m[metricKey]),
          borderColor: 'var(--primary-color)',
          backgroundColor: 'rgba(var(--primary-color-rgb), 0.1)',
          tension: 0.4,
          fill: true,
        },
      ]
    }

    chartData.value = {
      labels: timestamps,
      datasets: datasets,
    }

    // Add additional y-axis for storage metrics
    if (selectedMetric.value.value === 'storage') {
      chartOptions.scales.storage = {
        type: 'linear',
        position: 'right',
        grid: {
          drawOnChartArea: false,
        },
        title: {
          display: true,
          text: 'Total Storage (GB)',
        },
      }
    } else {
      delete chartOptions.scales.storage
    }

    // Create new chart instance
    const ctx = document.querySelector('canvas').getContext('2d')
    chartInstance = new Chart(ctx, {
      type: 'line',
      data: chartData.value,
      options: chartOptions,
    })
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to update chart data',
      life: 3000,
    })
  }
}

// Add router selection handler
const onRouterSelect = async (event) => {
  try {
    loading.value = true
    const routerMetrics = await monitoringService.getRouterMetrics(event.data.id)
    // Update router metrics and chart for the selected router
    routerMetrics.value = [routerMetrics]
    updateChart()

    // Fetch interfaces for the selected router
    const interfaces = await monitoringService.getInterfaceMetrics()
    interfaceMetrics.value = interfaces.filter((i) => i.router_id === event.data.id)
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: error.message,
      life: 3000,
    })
  } finally {
    loading.value = false
  }
}

// Modify refresh data to handle selected router
const refreshData = async () => {
  if (selectedRouter.value) {
    await Promise.all([fetchStats(), onRouterSelect({ data: selectedRouter.value })])
  } else {
    await Promise.all([fetchStats(), fetchRouterMetrics(), fetchInterfaceMetrics()])
  }
}

// Add exportData function
const exportData = () => {
  try {
    const data = interfaceMetrics.value.map((metric) => ({
      router: metric.router_hostname,
      interface: metric.name,
      status: metric.operational_status,
      incoming: formatBandwidth(metric.bps_in),
      outgoing: formatBandwidth(metric.bps_out),
    }))

    // Convert to CSV
    const csvContent = [
      ['Router', 'Interface', 'Status', 'Incoming', 'Outgoing'].join(','),
      ...data.map((row) => Object.values(row).join(',')),
    ].join('\n')

    // Create and trigger download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `interface-metrics-${new Date().toISOString()}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Export Failed',
      detail: error.message,
      life: 3000,
    })
  }
}

// Watch for metric and time range changes
watch(
  [selectedMetric, selectedTimeRange],
  () => {
    updateChart()
  },
  { immediate: true },
)

// Add watch for router deselection
watch(selectedRouter, (newVal) => {
  if (!newVal) {
    refreshData()
  }
})

onMounted(() => {
  refreshData()
  // Set up auto-refresh every 30 seconds
  updateInterval.value = setInterval(refreshData, 30000)
})

onUnmounted(() => {
  if (updateInterval.value) {
    clearInterval(updateInterval.value)
  }
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }
})
</script>
