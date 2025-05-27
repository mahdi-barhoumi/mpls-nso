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
        <!-- Totals at the very top -->
        <div>
          <div class="grid grid-cols-2 gap-4 mb-3">
            <div class="surface-100 p-2 border-round flex flex-col items-center gap-1">
              <div class="flex items-center justify-center gap-2 mb-1">
                <div class="flex items-center justify-center bg-blue-100 dark:bg-blue-400/20 rounded-full w-9 h-9 shadow">
                  <i class="pi pi-server text-blue-500 text-xl"></i>
                </div>
                <div class="flex flex-col items-start">
                  <div class="text-base font-medium">{{ stats.total_routers }}</div>
                  <div class="text-500 text-xs">Total Devices</div>
                </div>
              </div>
            </div>
            <div class="surface-100 p-2 border-round flex flex-col items-center gap-1">
              <div class="flex items-center justify-center gap-2 mb-1">
                <div class="flex items-center justify-center bg-green-100 dark:bg-green-400/20 rounded-full w-9 h-9 shadow">
                  <i class="pi pi-sitemap text-green-500 text-xl"></i>
                </div>
                <div class="flex flex-col items-start">
                  <div class="text-base font-medium">{{ stats.total_interfaces }}</div>
                  <div class="text-500 text-xs">Total Interfaces</div>
                </div>
              </div>
            </div>
          </div>
        </div>
  
        <div v-if="loading" class="flex justify-center items-center flex-1">
          <i class="pi pi-spin pi-spinner text-primary" style="font-size: 1.5rem"></i>
        </div>
  
        <div v-else class="flex flex-col flex-1 justify-between">
          <!-- Chart and legend side by side, centered vertically -->
          <div class="flex-1 flex items-center justify-center">
            <Chart
              type="pie"
              :data="pieData"
              :options="pieOptions"
              style="min-width: 90%; max-height: 85%; margin: 0"
            />
          </div>
          <!-- High ... at the very bottom -->
          <div class="flex flex-row gap-4 justify-center mt-4 mb-2">
            <div class="flex items-center gap-2 text-sm">
              <i class="pi pi-gauge text-yellow-500"></i>
              <span>{{ stats.high_cpu_routers.length }} High CPU</span>
            </div>
            <div class="flex items-center gap-2 text-sm">
              <i class="pi pi-microchip text-orange-500"></i>
              <span>{{ stats.high_memory_routers.length }} High Memory</span>
            </div>
            <div class="flex items-center gap-2 text-sm">
              <i class="pi pi-database text-red-500"></i>
              <span>{{ stats.high_storage_routers.length }} High Storage</span>
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
  
  // Register datalabels plugin globally for Chart.js
  import ChartJS from 'chart.js/auto'
  ChartJS.register(ChartDataLabels)
  
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
  
  // Detect dark mode (Tailwind dark class on html or body)
  const isDark = computed(() =>
    document.documentElement.classList.contains('dark') ||
    document.body.classList.contains('dark')
  )
  
  // Use more saturated but not harsh colors for the pie chart
  const pieColors = computed(() =>
    isDark.value
      ? ['#14b8a6', '#ef4444'] // teal-600, red-500 for dark mode
      : ['#10b981', '#ef4444'] // green-600, red-500 for light mode
  )

  const pieData = ref({
    labels: ['Reachable', 'Unreachable'],
    datasets: [
      {
        data: [0, 0],
        backgroundColor: pieColors.value,
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
      legend: {
        display: true,
        position: 'right',
        labels: {
          color: isDark.value ? '#d1d5db' : '#6b7280',
          usePointStyle: true,
          pointStyle: 'circle',
          padding: 18,
          font: {
            size: 14,
            weight: 'bold',
          },
          boxWidth: 18,
        },
      },
      datalabels: {
        color: '#fff',
        font: {
          weight: 'bold',
          size: 16,
        },
        formatter: (value) => value,
        display: true,
      },
    },
    layout: {
      padding: 0,
    },
    responsive: true,
    maintainAspectRatio: false,
    backgroundColor: 'transparent',
  })
  
  // Watch for dark mode changes and update chart legend color dynamically
  watch(isDark, (val) => {
    pieData.value.datasets[0].backgroundColor = pieColors.value
    pieOptions.value.plugins.legend.labels.color = val ? '#d1d5db' : '#6b7280'
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
