<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useToast } from 'primevue/usetoast'
import LogService from '@/service/LogService'
import Dropdown from 'primevue/dropdown'
import Calendar from 'primevue/calendar'
import Button from 'primevue/button'
import InputSwitch from 'primevue/inputswitch'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'

const toast = useToast()
const logs = ref([])
const loading = ref(false)
const liveUpdate = ref(false)
const selectedLevel = ref(null)
const selectedModule = ref(null)
const startDate = ref(null)
const updateInterval = ref(null)

const logLevels = ['INFO', 'WARNING', 'ERROR', 'DEBUG']
const modules = ['Discovery', 'DHCP', 'TFTP', 'Network', 'Service', 'Monitor']

const getLogLevelSeverity = (level) => {
  switch (level) {
    case 'ERROR':
      return { severity: 'danger', icon: 'pi pi-times' }
    case 'WARNING':
      return { severity: 'warn', icon: 'pi pi-exclamation-triangle' }
    case 'INFO':
      return { severity: 'info', icon: 'pi pi-info-circle' }
    case 'DEBUG':
      return { severity: 'help', icon: 'pi pi-search' }
  }
}

const formatTimestamp = (timestamp) => {
  // Replace comma with period to make it valid ISO format
  const isoTimestamp = timestamp.replace(',', '.')
  return new Date(isoTimestamp).toLocaleString()
}

const fetchLogs = async () => {
  loading.value = true
  try {
    const params = {
      level: selectedLevel.value,
      module: selectedModule.value,
      start_date: startDate.value ? startDate.value.toISOString().split('T')[0] : null,
    }
    const response = await LogService.getLogs(params)
    logs.value = response.logs
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to fetch logs',
      life: 3000,
    })
  } finally {
    loading.value = false
  }
}

const refreshLogs = () => {
  fetchLogs()
}

const exportLogs = () => {
  const csvContent = logs.value
    .map((log) => {
      return `${log.timestamp},"${log.level}","${log.module}","${log.message.replace(/"/g, '""')}"`
    })
    .join('\n')

  const header = 'Timestamp,Level,Module,Message\n'
  const blob = new Blob([header + csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)

  link.setAttribute('href', url)
  link.setAttribute('download', `logs-${new Date().toISOString().split('T')[0]}.csv`)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

// Watch for filter changes
watch([selectedLevel, selectedModule, startDate], () => {
  refreshLogs()
})

// Live update handling
watch(liveUpdate, (newValue) => {
  if (newValue) {
    updateInterval.value = setInterval(refreshLogs, 5000) // Update every 5 seconds
  } else if (updateInterval.value) {
    clearInterval(updateInterval.value)
  }
})

onMounted(() => {
  fetchLogs()
})

onUnmounted(() => {
  if (updateInterval.value) {
    clearInterval(updateInterval.value)
  }
})
</script>

<template>
  <div class="card">
    <div class="flex justify-between mb-4">
      <div>
        <span class="text-xl text-900 font-bold">System Logs</span>
      </div>
      <div class="flex gap-2 items-center">
        <Dropdown
          v-model="selectedLevel"
          :options="logLevels"
          placeholder="Log Level"
          class="w-full md:w-14rem"
        />
        <Dropdown
          v-model="selectedModule"
          :options="modules"
          placeholder="Module"
          class="w-full md:w-14rem"
        />
        <Calendar
          v-model="startDate"
          placeholder="Start Date"
          class="w-full md:w-14rem"
          :maxDate="new Date()"
          :showTime="true"
        />
        <Button
          icon="pi pi-refresh"
          @click="refreshLogs"
          class="p-button-rounded p-button-text min-w-[2.5rem] h-[2.5rem] flex justify-center items-center"
          severity="secondary"
        />
        <Button
          icon="pi pi-download"
          @click="exportLogs"
          class="p-button-rounded p-button-text min-w-[2.5rem] h-[2.5rem] flex justify-center items-center"
          severity="secondary"
          :disabled="!logs.length"
        />
        <div class="flex items-center gap-2 px-2 py-1 surface-100 dark:surface-800 border-round">
          <InputSwitch v-model="liveUpdate" :disabled="loading" />
          <span :class="['font-medium', { 'text-primary': liveUpdate, 'text-500': !liveUpdate }]"
            >Live</span
          >
        </div>
      </div>
    </div>

    <div class="datatable-padding">
      <div v-if="loading" class="flex flex-col items-center justify-center py-12 text-lg text-500">
        <span class="pi pi-spin pi-spinner text-3xl mb-3"></span>
        Loading logs...
      </div>
      <DataTable
        v-else
        :value="logs"
        stripedRows
        scrollable
        showGridlines
        scrollHeight="70vh"
        class="p-datatable-sm"
        sortField="timestamp"
        :sortOrder="-1"
      >
        <Column field="timestamp" header="Timestamp" sortable>
          <template #body="slotProps">
            {{ formatTimestamp(slotProps.data.timestamp) }}
          </template>
        </Column>
        <Column field="level" header="Level" sortable>
          <template #body="slotProps">
            <Tag
              :severity="getLogLevelSeverity(slotProps.data.level).severity"
              :icon="getLogLevelSeverity(slotProps.data.level).icon"
            >
              {{ slotProps.data.level }}
            </Tag>
          </template>
        </Column>
        <Column field="module" header="Module" sortable style="min-width: 200px">
          <template #body="slotProps">
            <Button severity="contrast" variant="text">{{ slotProps.data.module }}</Button>
          </template>
        </Column>
        <Column field="message" header="Message" style="min-width: 50%">
          <template #body="slotProps">
            <div class="whitespace-normal break-words">{{ slotProps.data.message }}</div>
          </template>
        </Column>
      </DataTable>
    </div>
  </div>
</template>

<style>
.p-tag.yellow {
  background-color: #fbbf24;
  color: #92400e;
}

.datatable-padding {
  padding-right: 0.5rem;
  padding-left: 0.5rem;
}
</style>
