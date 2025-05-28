<template>
    <div class="card h-full">
      <div class="card-header">
        <h5 class="text-lg m-0">Monitoring Overview</h5>
        <div class="flex items-center gap-2">
          <Button
            icon="pi pi-refresh"
            text
            rounded
            size="small"
            :loading="loading"
            @click="fetchStats"
            tooltip="Refresh"
          />
          <Button
            icon="pi pi-external-link"
            text
            rounded
            size="small"
            @click="navigateToMonitoring"
            tooltip="Go to Monitoring"
          />
          <div
            class="flex items-center justify-center bg-blue-100 dark:bg-blue-400/10 rounded-lg w-8 h-8"
          >
            <i class="pi pi-chart-pie text-blue-500"></i>
          </div>
        </div>
      </div>
  
      <div class="card-content h-full flex flex-col justify-between">
  
        <div v-if="loading" class="flex justify-center items-center flex-1">
          <i class="pi pi-spin pi-spinner text-primary" style="font-size: 1.5rem"></i>
        </div>
  
        <div v-else class="flex flex-col flex-1 justify-between">
          <!-- Charts in the same row with fixed size -->
          <div class="flex flex-row flex-nowrap items-center justify-around">
            <div class="flex flex-col items-center justify-center min-w-0">
              <div class="flex items-center justify-center mb-2">
                <i class="pi pi-server text-2xl text-blue-500 mr-2"></i>
                <span class="text-center font-semibold text-base">Devices</span>
              </div>
              <div class="w-full max-w-[150px] aspect-square flex items-center justify-center">
                <Chart
                  type="doughnut"
                  :data="pieData"
                  :options="pieOptions"
                  :plugins="[routerCenterTextPlugin, ChartDataLabels]"
                  :key="chartKey"
                  style="width: 100%; height: 100%; padding: 15px;"
                />
              </div>
            </div>
            <div class="flex flex-col items-center justify-center min-w-0">
              <div class="flex items-center justify-center mb-2">
                <i class="pi pi-sitemap text-2xl text-green-500 mr-2"></i>
                <span class="text-center font-semibold text-base">Interfaces</span>
              </div>
              <div class="w-full max-w-[150px] aspect-square flex items-center justify-center">
                <Chart
                  type="doughnut"
                  :data="ifacePieData"
                  :options="ifacePieOptions"
                  :plugins="[ifaceCenterTextPlugin, ChartDataLabels]"
                  :key="ifaceChartKey"
                  style="width: 100%; height: 100%; padding: 15px;"
                />
              </div>
            </div>
          </div>
          <!-- Shared legend for both charts -->
          <div class="flex flex-row justify-center gap-6 my-0">
            <div class="flex items-center gap-2">
              <span class="inline-block w-5 h-3 rounded-sm" :style="{ background: pieColors[0] }"></span>
              <span class="text-sm font-medium">Up</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="inline-block w-5 h-3 rounded-sm" :style="{ background: pieColors[1] }"></span>
              <span class="text-sm font-medium">Down</span>
            </div>
          </div>
          <!-- High ... at the very bottom -->
          <div class="flex flex-row gap-4 justify-around mt-4 mb-2">
            <div class="flex flex-col items-center px-3 py-1 bg-red-50 dark:bg-red-900/20 rounded-lg shadow-sm min-w-[70px]">
              <div class="flex items-center gap-1">
                <i class="pi pi-gauge text-red-500"></i>
                <span class="font-bold text-lg">{{ stats.high_cpu_routers.length }}</span>
              </div>
              <span class="text-xs font-medium mt-1 text-red-700 dark:text-red-300">High CPU</span>
            </div>
            <div class="flex flex-col items-center px-3 py-1 bg-orange-50 dark:bg-orange-900/20 rounded-lg shadow-sm min-w-[70px]">
              <div class="flex items-center gap-1">
                <i class="pi pi-microchip text-orange-500"></i>
                <span class="font-bold text-lg">{{ stats.high_memory_routers.length }}</span>
              </div>
              <span class="text-xs font-medium mt-1 text-orange-700 dark:text-orange-300">High Memory</span>
            </div>
            <div class="flex flex-col items-center px-3 py-1 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg shadow-sm min-w-[70px]">
              <div class="flex items-center gap-1">
                <i class="pi pi-database text-yellow-500"></i>
                <span class="font-bold text-lg">{{ stats.high_storage_routers.length }}</span>
              </div>
              <span class="text-xs font-medium mt-1 text-yellow-700 dark:text-yellow-300">High Storage</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
  import { useToast } from 'primevue/usetoast'
  import Button from 'primevue/button'
  import Chart from 'primevue/chart'
  import ChartDataLabels from 'chartjs-plugin-datalabels'
  import MonitoringService from '@/service/MonitoringService'
  import { useRouter } from 'vue-router'
  import { useLayout } from '@/layout/composables/layout'
  
  // Parameterized center text plugin factory
  function createCenterTextPlugin(getValue, getLabel) {
    return {
      id: 'centerText',
      afterDraw(chart) {
        const { ctx, chartArea: area } = chart
        if (!area) return
        ctx.save()
        // Calculate vertical centering for two lines
        const labelFontSize = 14 // px
        const valueFontSize = 24 // px
        const lineGap = 4 // px gap between lines

        const totalHeight = labelFontSize + valueFontSize + lineGap
        const centerY = (area.top + area.bottom) / 2

        // Always use the latest color from chart options (set by watcher)
        const color = chart.options.plugins?.datalabels?.color ?? '#222'

        // Draw label (e.g. "Total") on top
        ctx.font = `normal ${labelFontSize}px Lato, sans-serif`
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        ctx.fillStyle = color
        ctx.fillText(
          getLabel(),
          (area.left + area.right) / 2,
          centerY - (totalHeight / 2) + (labelFontSize / 2)
        )

        // Draw value below
        ctx.font = `bold ${valueFontSize}px Lato, sans-serif`
        ctx.fillStyle = color
        ctx.fillText(
          getValue(),
          (area.left + area.right) / 2,
          centerY + (totalHeight / 2) - (valueFontSize / 2)
        )
        ctx.restore()
      }
    }
  }
  
  const monitoringService = new MonitoringService()
  const toast = useToast()
  const router = useRouter()
  const loading = ref(false)
  const stats = ref({
    total_routers: 0,
    reachable_routers: 0,
    total_interfaces: 0,
    enabled_interfaces: 0,
    high_cpu_routers: [],
    high_memory_routers: [],
    high_storage_routers: [],
  })
  
  // Detect dark mode using the app-dark class (matches Tailwind config)
  const isDark = computed(() =>
    document.documentElement.className.includes('app-dark') ||
    document.body.className.includes('app-dark')
  )

  // Also watch the reactive dark mode state from layout composable
  const { isDarkTheme } = useLayout()

  // Computed color for text (reactive to theme)
  const chartTextColor = computed(() => (isDark.value ? '#fff' : '#222'))

  // Chart keys for forcing re-render
  const chartKey = ref(0)
  const ifaceChartKey = ref(0)
  
  const pieColors = ['#22c55e', '#ef4444'] // green-500, red-500
  
  const pieData = ref({
    labels: ['Up', 'Down'],
    datasets: [
      {
        data: [0, 0],
        backgroundColor: pieColors,
        borderColor: [
          'rgba(0,0,0,0)', // No border
          'rgba(0,0,0,0)',
        ],
        borderWidth: 0, // No border
      },
    ],
  })
  
  const pieOptions = ref({
    plugins: {
      legend: { display: false },
      datalabels: {
        display: true,
        color: chartTextColor.value,
        font: { weight: 'bold', size: 11 }, // smaller font size
        formatter: (value) => value,
      },
    },
    cutout: '70%',
    layout: { padding: 0 },
    responsive: true,
    maintainAspectRatio: false,
    backgroundColor: 'transparent',
  })
  
  const ifacePieData = ref({
    labels: ['Up', 'Down'],
    datasets: [
      {
        data: [0, 0],
        backgroundColor: pieColors,
        borderColor: [
          'rgba(0,0,0,0)',
          'rgba(0,0,0,0)',
        ],
        borderWidth: 0,
      },
    ],
  })
  
  const ifacePieOptions = ref({
    plugins: {
      legend: { display: false },
      datalabels: {
        display: true,
        color: chartTextColor.value,
        font: { weight: 'bold', size: 11 }, // smaller font size
        formatter: (value) => value,
      },
    },
    cutout: '70%',
    layout: { padding: 0 },
    responsive: true,
    maintainAspectRatio: false,
    backgroundColor: 'transparent',
  })
  
  // Plugins for each chart
  const routerCenterTextPlugin = createCenterTextPlugin(
    () => stats.value.total_routers?.toString() ?? '0',
    () => 'Total'
  )
  const ifaceCenterTextPlugin = createCenterTextPlugin(
    () => stats.value.total_interfaces?.toString() ?? '0',
    () => 'Total'
  )
  
  // Watch for dark mode changes and update chart legend color dynamically
  watch([isDark, isDarkTheme], () => {
    pieData.value.datasets[0].backgroundColor = pieColors
    ifacePieData.value.datasets[0].backgroundColor = pieColors
    // Update datalabels color in chart options so plugin picks up new color
    pieOptions.value.plugins.datalabels.color = chartTextColor.value
    ifacePieOptions.value.plugins.datalabels.color = chartTextColor.value
    // Force chart re-render to update color and avoid canvas error
    chartKey.value++
    ifaceChartKey.value++
  })
  
  const fetchStats = async () => {
    loading.value = true
    try {
      const data = await monitoringService.getDashboardStats()
      stats.value = data
      pieData.value.datasets[0].data = [
        data.reachable_routers,
        data.total_routers - data.reachable_routers,
      ]
      ifacePieData.value.datasets[0].data = [
        data.enabled_interfaces,
        data.total_interfaces - data.enabled_interfaces,
      ]
    } catch (error) {
      toast.add({
        severity: 'error',
        summary: 'Error',
        detail: 'Failed to load monitoring stats',
        life: 3000,
      })
    } finally {
      loading.value = false
    }
  }
  
  const navigateToMonitoring = () => {
    router.push('/monitoring')
  }
  
  onMounted(() => {
    fetchStats()
    const interval = setInterval(fetchStats, 60000)
    onUnmounted(() => clearInterval(interval))
  })
  </script>
