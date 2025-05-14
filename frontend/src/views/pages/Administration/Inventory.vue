<template>
  <div class="card">
    <Toast />
    <!-- Header -->
    <div class="flex flex-wrap justify-between gap-2 mb-4">
      <h4 class="text-2xl font-medium m-0">Device Inventory</h4>
      <div class="flex gap-2">
        <span class="p-input-icon-left">
          <i class="pi pi-search" />
          <InputText v-model="filters.global.value" placeholder="Search devices..." />
        </span>
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
    >
      <!-- Expansion Template -->
      <template #expansion="slotProps">
        <div class="p-3">
          <h5 class="text-lg mb-3">Device Details</h5>
          <div class="grid">
            <div class="col-12 md:col-6 lg:col-3">
              <div class="surface-0 shadow-1 p-3 border-round">
                <div class="text-900 font-medium mb-2">Interfaces</div>
                <div class="text-700">
                  <i class="pi pi-link mr-2"></i>
                  {{ slotProps.data.interface_count || 0 }} interfaces
                </div>
              </div>
            </div>
            <div class="col-12 md:col-6 lg:col-3">
              <div class="surface-0 shadow-1 p-3 border-round">
                <div class="text-900 font-medium mb-2">VRF Count</div>
                <div class="text-700">
                  <i class="pi pi-server mr-2"></i>
                  {{ slotProps.data.vrf_count || 0 }} VRFs
                </div>
              </div>
            </div>
            <div class="col-12 md:col-6 lg:col-3">
              <div class="surface-0 shadow-1 p-3 border-round">
                <div class="text-900 font-medium mb-2">Last Discovery</div>
                <div class="text-700">
                  <i class="pi pi-clock mr-2"></i>
                  {{ formatDate(slotProps.data.last_discovered) }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- Table Columns -->
      <Column expander />
      <Column field="hostname" header="Hostname" sortable>
        <template #body="{ data }">
          <div class="flex align-items-center gap-2">
            <i class="pi pi-desktop text-primary"></i>
            <span>{{ data.hostname }}</span>
          </div>
        </template>
      </Column>

      <Column field="role" header="Role" sortable>
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

      <Column field="management_ip_address" header="Management IP" sortable>
        <template #body="{ data }">
          <div class="flex align-items-center gap-2">
            <i class="pi pi-sitemap text-primary"></i>
            <span>{{ data.management_ip_address }}</span>
          </div>
        </template>
      </Column>

      <Column field="chassis_id" header="Chassis ID" sortable>
        <template #body="{ data }">
          <div class="flex align-items-center gap-2">
            <i class="pi pi-box text-primary"></i>
            <span>{{ data.chassis_id }}</span>
          </div>
        </template>
      </Column>
    </DataTable>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import RouterService from '@/service/RouterService'

// Components
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Tag from 'primevue/tag'
import Dropdown from 'primevue/dropdown'
import Toast from 'primevue/toast'
import { FilterMatchMode } from '@primevue/core/api'

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
  { label: 'Provider Edge', value: 'Provider Edge' },
  { label: 'Customer Edge', value: 'Customer Edge' },
]

// Utility functions
const getRoleSeverity = (role) => {
  switch (role) {
    case 'Provider Edge':
      return 'warning'
    case 'Customer Edge':
      return 'info'
    default:
      return null
  }
}

const getRoleLabel = (value) => {
  return roleOptions.find((option) => option.value === value)?.label || value
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
</style>
