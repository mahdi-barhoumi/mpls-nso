<template>
  <div class="card">
    <div class="flex flex-wrap gap-2 items-center justify-between">
      <div class="font-semibold text-xl mb-4">Sites</div>
      <IconField>
        <InputIcon>
          <i class="pi pi-search" />
        </InputIcon>
        <InputText v-model="filters['global'].value" placeholder="Search..." />
      </IconField>
    </div>

    <div v-if="loading" class="flex align-items-center justify-content-center py-6">
      <ProgressSpinner style="width: 50px; height: 50px" strokeWidth="4" />
      <span class="ml-3 text-900 font-medium">Loading sites...</span>
    </div>

    <div v-else-if="sites.length === 0" class="flex align-items-center justify-content-center py-8">
      <div class="text-center">
        <i class="pi pi-info-circle text-6xl text-400 mb-3"></i>
        <div class="text-900 font-medium text-xl mb-2">No Sites Found</div>
        <div class="text-600">Create your first site to get started</div>
      </div>
    </div>

    <div v-else>
      <DataTable
        :value="sites"
        stripedRows
        showGridlines
        responsiveLayout="scroll"
        :paginator="sites.length > 10"
        :rows="10"
        :rowsPerPageOptions="[5, 10, 25, 50]"
        :filters="filters"
        filterDisplay="menu"
        paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
        currentPageReportTemplate="Showing {first} to {last} of {totalRecords} entries"
      >
        <Column field="name" header="Name" :sortable="true" class="font-medium">
          <template #body="slotProps">
            <span class="text-900 font-medium">{{ slotProps.data.name }}</span>
          </template>
        </Column>

        <Column field="location" header="Location" :sortable="true">
          <template #body="slotProps">
            <span class="text-700">{{ slotProps.data.location || 'N/A' }}</span>
          </template>
        </Column>

        <Column field="customer.name" header="Customer" :sortable="true">
          <template #body="slotProps">
            <span class="text-700">{{ slotProps.data.customer?.name || 'N/A' }}</span>
          </template>
        </Column>

        <Column header="Provider Interface">
          <template #body="slotProps">
            <div class="text-700">
              <div class="font-medium">
                {{ slotProps.data.assigned_interface?.router?.hostname || 'N/A' }}
              </div>
              <small class="text-500"
                >via {{ slotProps.data.assigned_interface?.name || 'N/A' }}</small
              >
            </div>
          </template>
        </Column>

        <Column field="CE_router.hostname" header="Customer Edge" :sortable="true">
          <template #body="slotProps">
            <span class="text-700">{{ slotProps.data.CE_router?.hostname || 'N/A' }}</span>
          </template>
        </Column>

        <Column field="dhcp_scope" header="Management Subnet" :sortable="true">
          <template #body="slotProps">
            <span class="text-700">{{ slotProps.data.dhcp_scope || 'N/A' }}</span>
          </template>
        </Column>

        <Column field="link_network" header="Link Subnet" :sortable="true">
          <template #body="slotProps">
            <span class="text-700">{{ slotProps.data.link_network || 'N/A' }}</span>
          </template>
        </Column>

        <Column field="status" header="Status" :sortable="true">
          <template #body="slotProps">
            <Tag
              :value="getStatusText(slotProps.data.status)"
              :severity="getStatusSeverity(slotProps.data.status)"
            />
          </template>
        </Column>

        <Column header="Routing">
          <template #body="slotProps">
            <div class="flex align-items-center gap-2">
              <Tag
                :value="slotProps.data.has_routing ? 'Enabled' : 'Disabled'"
                :severity="slotProps.data.has_routing ? 'success' : 'danger'"
              />
              <Button
                v-if="slotProps.data.has_routing"
                icon="pi pi-lock"
                label="Disable"
                severity="danger"
                variant="text"
                size="small"
                v-tooltip.top="'Disable Network Access'"
                :loading="routingAction === slotProps.data.id"
                @click="handleDisableRouting(slotProps.data)"
              />
              <Button
                v-else
                icon="pi pi-lock-open"
                label="Enable"
                severity="success"
                variant="text"
                size="small"
                v-tooltip.top="'Enable Network Access'"
                :loading="routingAction === slotProps.data.id"
                :disabled="!isStatusActive(slotProps.data.status)"
                @click="handleEnableRouting(slotProps.data)"
              />
            </div>
          </template>
        </Column>

        <Column header="Actions" :exportable="false" class="text-center">
          <template #body="slotProps">
            <div class="flex gap-2 justify-content-center">
              <Button
                icon="pi pi-pencil"
                severity="info"
                size="small"
                outlined
                v-tooltip.top="'Edit Site'"
                @click="handleEdit(slotProps.data)"
              />

              <Button
                icon="pi pi-trash"
                severity="danger"
                size="small"
                outlined
                v-tooltip.top="'Delete Site'"
                :loading="deleting === slotProps.data.id"
                @click="handleDelete(slotProps.data)"
              />
            </div>
          </template>
        </Column>
      </DataTable>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { FilterMatchMode } from '@primevue/core/api'

const props = defineProps({
  sites: Array,
  loading: Boolean,
  deleting: Number,
  routingAction: Number,
})

const emit = defineEmits(['edit', 'delete', 'enable-routing', 'disable-routing'])

const filters = ref({
  global: { value: null, matchMode: FilterMatchMode.CONTAINS },
})

// Helper functions for status handling
const isStatusActive = (status) => {
  if (typeof status === 'boolean') {
    return status === true
  }
  return status === 'active'
}

const getStatusText = (status) => {
  if (typeof status === 'boolean') {
    return status ? 'Active' : 'Inactive'
  }
  if (status === 'active') return 'Active'
  if (status === 'inactive') return 'Inactive'
  return status || 'Offline'
}

const getStatusSeverity = (status) => {
  if (isStatusActive(status)) {
    return 'success'
  }
  if (typeof status === 'boolean' && status === false) {
    return 'danger'
  }
  if (status === 'inactive') {
    return 'danger'
  }
  return 'warning'
}

const handleEdit = (site) => {
  emit('edit', site)
}

const handleDelete = (site) => {
  emit('delete', site)
}

const handleEnableRouting = (site) => {
  emit('enable-routing', site)
}

const handleDisableRouting = (site) => {
  emit('disable-routing', site)
}
</script>
