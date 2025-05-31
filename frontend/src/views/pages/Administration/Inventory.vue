<template>
  <div class="card">
    <Toast />
    <!-- Header -->
    <div class="flex flex-wrap justify-between gap-2 mb-4">
      <h4 class="text-2xl font-medium m-0">Device Inventory</h4>
      <div class="flex gap-2">
        <!-- Use IconField/InputIcon/InputText as in customers page -->
        <IconField>
          <InputIcon>
            <i class="pi pi-search" />
          </InputIcon>
          <InputText v-model="filters.global.value" placeholder="Search devices..." />
        </IconField>
        <Button
          icon="pi pi-refresh"
          rounded
          severity="secondary"
          aria-label="Refresh"
          @click="loadRouters"
        />
      </div>
    </div>

    <!-- DataTable -->
    <DataTable
      :value="routers"
      :loading="loading"
      v-model:filters="filters"
      filterMode="lenient"
      filterDisplay="menu"
      :globalFilterFields="['hostname', 'role', 'management_ip_address', 'chassis_id']"
      :rows="10"
      :rowsPerPageOptions="[10, 20, 50]"
      paginator
      :totalRecords="totalRecords"
      tableStyle="min-width: 50rem"
      stripedRows
      showGridlines
      v-model:expandedRows="expandedRows"
      dataKey="id"
      @rowExpand="onRowExpand"
    >
      <!-- Expansion Template -->
      <template #expansion="slotProps">
        <div class="expand-section">
          <div v-if="deviceInfoLoading[slotProps.data.id]" class="expand-loading">Loading device details...</div>
          <div v-else>
            <!-- Two column layout: RouterService + Buttons | MonitoringService -->
            <div class="expand-details-row">
              <!-- Left column: RouterService info at top, buttons at bottom -->
              <div class="expand-col expand-col-left">
                <!-- Device Details header moved here -->
                <h5 class="expand-title">Device Details</h5>
                <!-- RouterService details at top -->
                <div class="router-service-details">
                  <div class="mb-2"><b>Reachable:</b> <span class="details-value">
                    <span :class="slotProps.data.reachable ? 'text-green-600' : 'text-red-500'">
                      {{ slotProps.data.reachable ? 'Yes' : 'No' }}
                    </span>
                  </span></div>
                  <div class="mb-2"><b>Role:</b> <span class="details-value">{{ slotProps.data.role }}</span></div>
                  <div class="mb-2"><b>Hostname:</b> <span class="details-value">{{ slotProps.data.hostname }}</span></div>
                  <div class="mb-2"><b>Management IP:</b> <span class="details-value">{{ slotProps.data.management_ip_address }}</span></div>
                  <div class="mb-2"><b>Chassis MAC:</b> <span class="details-value">{{ formatMac(slotProps.data.chassis_id) }}</span></div>
                  <div class="mb-2"><b>First Discovered:</b> <span class="details-value">{{ formatDate(slotProps.data.first_discovered) }}</span></div>
                  <div class="mb-2"><b>Last Discovered:</b> <span class="details-value">{{ formatDate(slotProps.data.last_discovered) }}</span></div>
                </div>
                
                <!-- Action buttons at bottom of left column -->
                <div class="expand-actions-left-bottom-horizontal">
                  <Button
                    label="Show Interfaces"
                    icon="pi pi-sitemap"
                    size="small"
                    @click="toggleInterfaces(slotProps.data.id)"
                    :disabled="interfacesLoading[slotProps.data.id]"
                  />
                  <Button
                    label="Show VRFs"
                    icon="pi pi-database"
                    size="small"
                    @click="toggleVRFs(slotProps.data.id)"
                    :disabled="vrfsLoading[slotProps.data.id]"
                  />
                  <Button
                    label="Show OSPF"
                    icon="pi pi-share-alt"
                    size="small"
                    @click="toggleOSPF(slotProps.data.id)"
                    :disabled="ospfLoading[slotProps.data.id]"
                  />
                </div>
              </div>
              
              <!-- Right column: MonitoringService info -->
              <div class="expand-col expand-col-right">
                <div class="mb-2"><b>Uptime:</b> <span class="details-value">
                  <span v-if="slotProps.data.reachable && deviceInfo[slotProps.data.id]">
                    {{ deviceInfo[slotProps.data.id].uptime_formatted }}
                  </span>
                  <span v-else>N/A</span>
                </span></div>
                <div class="mb-2"><b>Software Version:</b> <span class="details-value">
                  <span v-if="slotProps.data.reachable && deviceInfo[slotProps.data.id]">
                    {{ deviceInfo[slotProps.data.id].ios_version }}
                  </span>
                  <span v-else>N/A</span>
                </span></div>
                <div class="mb-2"><b>Manufacturer:</b> <span class="details-value">
                  <span v-if="slotProps.data.reachable && deviceInfo[slotProps.data.id]">
                    {{ deviceInfo[slotProps.data.id].manufacturer }}
                  </span>
                  <span v-else>N/A</span>
                </span></div>
                <div class="mb-2"><b>Serial Number:</b> <span class="details-value">
                  <span v-if="slotProps.data.reachable && deviceInfo[slotProps.data.id]">
                    {{ deviceInfo[slotProps.data.id].serial_number }}
                  </span>
                  <span v-else>N/A</span>
                </span></div>
                <div class="mb-2"><b>Chassis:</b> <span class="details-value">
                  <span v-if="slotProps.data.reachable && deviceInfo[slotProps.data.id]">
                    {{ deviceInfo[slotProps.data.id].chassis_description }}
                  </span>
                  <span v-else>N/A</span>
                </span></div>
                <div class="mb-2"><b>Hardware Version:</b> <span class="details-value">
                  <span v-if="slotProps.data.reachable && deviceInfo[slotProps.data.id]">
                    {{ deviceInfo[slotProps.data.id].hardware_version }}
                  </span>
                  <span v-else>N/A</span>
                </span></div>
                <div class="mb-2"><b>Part Number:</b> <span class="details-value">
                  <span v-if="slotProps.data.reachable && deviceInfo[slotProps.data.id]">
                    {{ deviceInfo[slotProps.data.id].part_number }}
                  </span>
                  <span v-else>N/A</span>
                </span></div>
                <div class="mb-2"><b>CPU Cores:</b> <span class="details-value">
                  <span v-if="slotProps.data.reachable && deviceInfo[slotProps.data.id]">
                    {{ deviceInfo[slotProps.data.id].cpu_cores }}
                  </span>
                  <span v-else>N/A</span>
                </span></div>
                <div class="mb-2"><b>Total System Memory:</b> <span class="details-value">
                  <span v-if="slotProps.data.reachable && deviceInfo[slotProps.data.id]">
                    {{ deviceInfo[slotProps.data.id].total_system_memory_mb }} MB
                  </span>
                  <span v-else>N/A</span>
                </span></div>
                <div class="mb-2"><b>Total System Storage:</b> <span class="details-value">
                  <span v-if="slotProps.data.reachable && deviceInfo[slotProps.data.id]">
                    {{ deviceInfo[slotProps.data.id].total_system_storage_mb }} MB
                  </span>
                  <span v-else>N/A</span>
                </span></div>
                <div class="mb-2"><b>Current Time:</b> <span class="details-value">
                  <span v-if="slotProps.data.reachable && deviceInfo[slotProps.data.id]">
                    {{ formatDeviceTime(deviceInfo[slotProps.data.id].current_datetime) }}
                  </span>
                  <span v-else>N/A</span>
                </span></div>
                <div class="mb-2"><b>Manufacturing Date:</b> <span class="details-value">
                  <span v-if="slotProps.data.reachable && deviceInfo[slotProps.data.id]">
                    {{ formatDeviceTime(deviceInfo[slotProps.data.id].manufacturing_date) }}
                  </span>
                  <span v-else>N/A</span>
                </span></div>
              </div>
            </div>
          </div>
          
          <!-- Expandable tables remain at the bottom -->
          <div v-if="showInterfaces[slotProps.data.id]" class="expand-table">
            <h6>Interfaces</h6>
            <div v-if="interfacesLoading[slotProps.data.id]" class="expand-loading">Loading interfaces...</div>
            <table v-else class="min-w-full text-sm">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Addressing</th>
                  <th>IP</th>
                  <th>MAC</th>
                  <th>Enabled</th>
                  <th>VRF</th>
                  <th>Category</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="iface in interfaces[slotProps.data.id]" :key="iface.id">
                  <td>{{ iface.name }}</td>
                  <td>
                    {{ getAddressingType(iface) }}
                  </td>
                  <td>{{ iface.ip_address || '-' }}</td>
                  <td>{{ formatMac(iface.mac_address) }}</td>
                  <td class="text-center">
                    <i :class="iface.enabled ? 'pi pi-check text-green-600' : 'pi pi-times text-red-500'"></i>
                  </td>
                  <td>{{ iface.vrf || '-' }}</td>
                  <td>{{ getCategoryLabel(iface.category) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-if="showVRFs[slotProps.data.id]" class="expand-table">
            <h6>VRFs</h6>
            <div v-if="vrfsLoading[slotProps.data.id]" class="expand-loading">Loading VRFs...</div>
            <table v-else class="min-w-full text-sm">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>RD</th>
                  <th>Import RTs</th>
                  <th>Export RTs</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="vrf in vrfs[slotProps.data.id]" :key="vrf.id">
                  <td>{{ vrf.name || '-' }}</td>
                  <td>{{ vrf.route_distinguisher || '-' }}</td>
                  <td>
                    <span v-if="vrf.import_targets && vrf.import_targets.length">
                      <span v-for="rt in vrf.import_targets" :key="rt" class="mr-1">{{ rt }}</span>
                    </span>
                    <span v-else>-</span>
                  </td>
                  <td>
                    <span v-if="vrf.export_targets && vrf.export_targets.length">
                      <span v-for="rt in vrf.export_targets" :key="rt" class="mr-1">{{ rt }}</span>
                    </span>
                    <span v-else>-</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-if="showOSPF[slotProps.data.id]" class="expand-table">
            <h6>OSPF Processes</h6>
            <div v-if="ospfLoading[slotProps.data.id]" class="expand-loading">Loading OSPF processes...</div>
            <table v-else class="min-w-full text-sm">
              <thead>
                <tr>
                  <th></th>
                  <th>Process ID</th>
                  <th>Router ID</th>
                  <th>Priority</th>
                  <th>VRF</th>
                  <th>Networks</th>
                </tr>
              </thead>
              <tbody>
                <template v-for="proc in ospf[slotProps.data.id] || []" :key="proc.id">
                  <tr>
                    <td>
                      <Button
                        icon="pi pi-chevron-down"
                        size="small"
                        text
                        v-if="!ospfExpanded[proc.id]"
                        @click="expandOSPFProcess(slotProps.data.id, proc.id)"
                      />
                      <Button
                        icon="pi pi-chevron-up"
                        size="small"
                        text
                        v-if="ospfExpanded[proc.id]"
                        @click="ospfExpanded[proc.id] = false"
                      />
                    </td>
                    <td>{{ proc.process_id || '-' }}</td>
                    <td>{{ proc.ospf_router_id || '-' }}</td>
                    <td>{{ proc.priority !== undefined && proc.priority !== null ? proc.priority : '-' }}</td>
                    <td>{{ proc.vrf || '-' }}</td>
                    <td>{{ proc.network_count !== undefined && proc.network_count !== null ? proc.network_count : '-' }}</td>
                  </tr>
                  <tr v-if="ospfExpanded[proc.id]">
                    <td colspan="6" style="padding: 0;">
                      <div v-if="ospfProcessLoading[proc.id]" class="p-2">Loading networks...</div>
                      <table v-else class="min-w-full text-xs">
                        <thead style="border-top: 0;">
                          <tr>
                            <th>Area</th>
                            <th>Network</th>
                            <th>Subnet Mask</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="net in ospfProcessDetail[proc.id]?.networks || []" :key="net.id">
                            <td>{{ (net.area !== undefined && net.area !== null && net.area !== '') ? net.area : '-' }}</td>
                            <td>{{ net.network || '-' }}</td>
                            <td>{{ net.subnet_mask || '-' }}</td>
                          </tr>
                          <tr v-if="(ospfProcessDetail[proc.id]?.networks || []).length === 0">
                            <td colspan="3" class="text-center text-600">No networks</td>
                          </tr>
                        </tbody>
                      </table>
                    </td>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>
        </div>
      </template>

      <!-- Table Columns -->
      <Column expander />
      <Column field="hostname" sortable>
        <template #header>
          <i class="pi pi-desktop text-primary"></i> Hostname
        </template>
        <template #body="{ data }">
          <span>{{ data.hostname }}</span>
        </template>
      </Column>

      <Column field="role" sortable>
        <template #header>
          <i class="pi pi-wrench text-primary"></i> Role
        </template>
        <template #body="{ data }">
          <Tag :value="data.role" :severity="getRoleSeverity(data.role)" />
        </template>
        <template #filter="{ filterCallback }">
          <Dropdown
            v-model="roleFilter"
            :options="roleOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Any"
            class="p-column-filter"
            :showClear="true"
            @change="filterCallback"
          >
            <template #value="slotProps">
              <Tag
                v-if="slotProps.value"
                :value="getRoleLabel(slotProps.value)"
                :severity="getRoleSeverity(slotProps.value)"
              />
              <span v-else>Any</span>
            </template>
          </Dropdown>
        </template>
      </Column>

      <Column field="management_ip_address" sortable>
        <template #header>
          <i class="pi pi-globe text-primary"></i> Management IP
        </template>
        <template #body="{ data }">
          <span>{{ data.management_ip_address }}</span>
        </template>
      </Column>

      <Column field="chassis_id" sortable>
        <template #header>
          <i class="pi pi-box text-primary"></i> Chassis MAC
        </template>
        <template #body="{ data }">
          <span>{{ formatMac(data.chassis_id) }}</span>
        </template>
      </Column>

      <Column field="first_discovered" sortable>
        <template #header>
          <i class="pi pi-calendar text-primary"></i> First Discovered
        </template>
        <template #body="{ data }">
          <span>{{ formatDate(data.first_discovered) }}</span>
        </template>
      </Column>
    </DataTable>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { useToast } from 'primevue/usetoast'
import RouterService from '@/service/RouterService'
import MonitoringService from '@/service/MonitoringService'

// Components
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Tag from 'primevue/tag'
import Dropdown from 'primevue/dropdown'
import Toast from 'primevue/toast'
import { FilterMatchMode } from '@primevue/core/api'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'

// State
const toast = useToast()
const routers = ref([])
const loading = ref(false)
const expandedRows = ref([])
const totalRecords = ref(0)
const roleFilter = ref(null)

// Filter setup
const filters = ref({
  global: { value: null, matchMode: FilterMatchMode.CONTAINS },
})

const roleOptions = [
  { label: 'Provider Core', value: 'Provider Core' },
  { label: 'Provider Edge', value: 'Provider Edge' },
  { label: 'Customer Edge', value: 'Customer Edge' },
]

// Utility functions
const getRoleSeverity = (role) => {
  switch (role) {
    case 'Provider Core':
      return 'danger'  // red
    case 'Provider Edge':
      return 'warning' // yellow/orange
    case 'Customer Edge':
      return 'info'    // blue
    default:
      return null
  }
}

const getRoleLabel = (value) => {
  return roleOptions.find((option) => option.value === value)?.label || value
}

// Format MAC address from abcd.0000.2555 to AB:CD:00:00:25:55
const formatMac = (mac) => {
  if (!mac) return ''
  // Remove dots, colons, and dashes, then uppercase
  let cleaned = mac.replace(/[\.\:\-]/g, '').toUpperCase()
  if (cleaned.length !== 12) return mac
  // Format as XX:XX:XX:XX:XX:XX
  return cleaned.match(/.{1,2}/g).join(':')
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

const formatMemory = (kb) => {
  if (!kb) return '0 KB'
  if (typeof kb === 'string') kb = parseInt(kb)
  if (kb >= 1024 * 1024) return `${(kb / (1024 * 1024)).toFixed(1)} GB`
  if (kb >= 1024) return `${(kb / 1024).toFixed(1)} MB`
  return `${kb} KB`
}

const formatDeviceTime = (isoString) => {
  if (!isoString) return ''
  // Remove trailing timezone if present (e.g. "+00:00")
  const clean = isoString.replace(/([.]\d+)?Z(\+\d{2}:\d{2})?$/, 'Z')
  const date = new Date(clean)
  if (isNaN(date.getTime())) return isoString
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  }).format(date)
}

// Helper for Addressing type
const getAddressingType = (iface) => {
  // If iface has a property indicating DHCP, use it, else fallback to static
  // Common property names: iface.dhcp, iface.is_dhcp, iface.addressing, iface.addressing_type
  if (iface.dhcp === true || iface.is_dhcp === true || iface.addressing === 'dhcp' || iface.addressing_type === 'dhcp') {
    return 'DHCP'
  }
  return 'Static'
}

// Helper for Category label
const getCategoryLabel = (category) => {
  if (!category) return ''
  switch (category.toLowerCase()) {
    case 'physical':
      return 'Physical'
    case 'logical':
      return 'Logical'
    case 'loopback':
      return 'Loopback'
    default:
      return category
  }
}

// API calls
const loadRouters = async () => {
  try {
    loading.value = true
    const data = await RouterService.getRouters()
    routers.value = data
    totalRecords.value = data.length
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to load devices',
      life: 3000,
    })
  } finally {
    loading.value = false
  }
}

const editDevice = (device) => {
  // TODO: Implement edit functionality
  console.log('Edit device:', device)
}

const configureDevice = (device) => {
  // TODO: Implement configure functionality
  console.log('Configure device:', device)
}

// Expansion details state
const interfaces = reactive({})
const interfacesLoading = reactive({})
const showInterfaces = reactive({})
const vrfs = reactive({})
const vrfsLoading = reactive({})
const showVRFs = reactive({})
const ospf = reactive({})
const ospfLoading = reactive({})
const showOSPF = reactive({})
const ospfExpanded = reactive({})
const ospfProcessDetail = reactive({})
const ospfProcessLoading = reactive({})
const deviceInfo = reactive({})
const deviceInfoLoading = reactive({})

const onRowExpand = async ({ data }) => {
  showInterfaces[data.id] = false
  showVRFs[data.id] = false
  showOSPF[data.id] = false

  // Fetch device info
  deviceInfoLoading[data.id] = true
  try {
    deviceInfo[data.id] = await new MonitoringService().getDeviceInfo(data.id)
  } catch {
    deviceInfo[data.id] = null
  }
  deviceInfoLoading[data.id] = false
}

const toggleInterfaces = async (routerId) => {
  if (!showInterfaces[routerId]) {
    interfacesLoading[routerId] = true
    try {
      interfaces[routerId] = await RouterService.getRouterInterfaces(routerId)
    } catch {
      interfaces[routerId] = []
    }
    interfacesLoading[routerId] = false
  }
  showInterfaces[routerId] = !showInterfaces[routerId]
}

const toggleVRFs = async (routerId) => {
  if (!showVRFs[routerId]) {
    vrfsLoading[routerId] = true
    try {
      vrfs[routerId] = await RouterService.getRouterVRFs(routerId)
    } catch {
      vrfs[routerId] = []
    }
    vrfsLoading[routerId] = false
  }
  showVRFs[routerId] = !showVRFs[routerId]
}

const toggleOSPF = async (routerId) => {
  if (!showOSPF[routerId]) {
    ospfLoading[routerId] = true
    try {
      ospf[routerId] = await RouterService.getRouterOSPF(routerId)
    } catch {
      ospf[routerId] = []
    }
    ospfLoading[routerId] = false
  }
  showOSPF[routerId] = !showOSPF[routerId]
}

const expandOSPFProcess = async (routerId, processId) => {
  ospfExpanded[processId] = true
  ospfProcessLoading[processId] = true
  try {
    ospfProcessDetail[processId] = await RouterService.getRouterOSPFProcess(routerId, processId)
  } catch {
    ospfProcessDetail[processId] = { networks: [] }
  }
  ospfProcessLoading[processId] = false
}

// Lifecycle
onMounted(() => {
  loadRouters()
})
</script>

<style scoped>
:deep(.p-datatable-wrapper) {
  border-radius: 6px;
}

:deep(.p-column-filter) {
  width: 100%;
}

/* Ensure consistent button sizes */
:deep(.p-button.p-button-icon-only) {
  width: 2.5rem;
  height: 2.5rem;
}

/* Expansion section styling - theme aware */
.expand-section {
  background: var(--surface-ground, #f8fafc);
  border: 1px solid var(--surface-border, #e5e7eb);
  padding: 2rem 1.5rem 1.5rem 1.5rem;
  margin: 0.5rem 0;
  box-shadow: 0 2px 8px 0 rgba(0,0,0,0.03);
}
.expand-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 1.25rem;
  color: var(--primary-color, #2563eb);
}

/* Two column layout: RouterService + Buttons | MonitoringService */
.expand-details-row {
  display: flex;
  flex-direction: row;
  gap: 2.5rem;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
}

/* Left column: RouterService details + buttons */
.expand-col.expand-col-left {
  flex: 1 1 320px;
  min-width: 260px;
  max-width: 480px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 100%;
}

/* Right column: MonitoringService details */
.expand-col.expand-col-right {
  flex: 1 1 320px;
  min-width: 260px;
  max-width: 480px;
  margin-left: 0;
  margin-right: 0;
  align-self: flex-start;
}

/* RouterService details at top of left column */
.router-service-details {
  flex-grow: 1;
  margin-bottom: 2rem;
}

/* Action buttons at bottom of left column */
.expand-actions-left-bottom-horizontal {
  display: flex;
  flex-direction: row;
  gap: 0.75rem;
  padding-top: 1rem;
  border-top: 1px solid var(--surface-border, #e5e7eb);
  justify-content: flex-start;
}
.expand-actions-left-bottom-horizontal .p-button {
  flex: 1 1 0;
  min-width: 0;
  white-space: nowrap;
}

.expand-actions-left-bottom,
.expand-actions-horizontal,
.expand-actions-vertical,
.expand-actions {
  display: none;
}

.expand-table {
  background: var(--surface-card, #fff);
  border: 1px solid var(--surface-border, #e5e7eb);
  padding: 1rem;
  margin-top: 1rem;
  box-shadow: 0 1px 4px 0 rgba(0,0,0,0.02);
  overflow-x: auto;
}

.expand-table table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  background: transparent;
  font-size: 0.97em;
}

.expand-table th,
.expand-table td {
  padding: 0.5rem 0.75rem;
  text-align: left;
  border-bottom: 1px solid var(--surface-border, #e5e7eb);
}

.expand-table th:nth-child(5),
.expand-table td:nth-child(5) {
  text-align: center;
}

.expand-table th {
  background: var(--surface-ground, #f3f4f6);
  font-weight: 600;
  color: var(--primary-color, #2563eb);
  border-top: 1px solid var(--surface-border, #e5e7eb);
}

.expand-table tr:last-child td {
  border-bottom: none;
}

.expand-table tbody tr:nth-child(even) {
  background: var(--surface-ground, #f8fafc);
}

.expand-table h6 {
  font-size: 1.08rem;
  font-weight: 600;
  margin-bottom: 0.7rem;
  color: var(--primary-color, #2563eb);
}

.expand-table .text-center {
  text-align: center;
}

.expand-table .text-600 {
  color: #64748b;
}

.expand-table .ml-4 {
  margin-left: 1.5rem;
}

.expand-loading {
  color: var(--text-color-secondary, #64748b);
  font-style: italic;
  padding: 0.5rem 0;
}

.details-value {
  margin-left: 0.25em;
  display: inline;
}
</style>