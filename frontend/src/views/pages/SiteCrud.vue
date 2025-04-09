<template>
  <div>
    <div class="card">
      <div class="font-semibold text-2xl mb-4">Manage Sites</div>
      <!-- Toolbar -->
      <Toolbar class="mb-6">
        <template #start>
          <Button
            label="New"
            icon="pi pi-plus"
            severity="secondary"
            class="mr-2"
            @click="openNewSiteDialog"
          />
          <Button
            label="Delete"
            icon="pi pi-trash"
            severity="secondary"
            @click="confirmDeleteSelected"
            :disabled="!selectedSites || !selectedSites.length"
          />
        </template>
      </Toolbar>

      <!-- DataTable -->
      <DataTable
        ref="dt"
        v-model:selection="selectedSites"
        :value="sites"
        dataKey="id"
        :paginator="true"
        :rows="10"
        :filters="filters"
        paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
        :rowsPerPageOptions="[5, 10, 25]"
        currentPageReportTemplate="Showing {first} to {last} of {totalRecords} sites"
        selectionMode="multiple"
        :loading="loading"
        class="p-datatable-gridlines"
      >
        <template #header>
          <div class="flex flex-wrap gap-2 items-center justify-between">
            <h4 class="m-0">Sites</h4>
          </div>
        </template>

        <Column selectionMode="multiple" style="width: 3rem" :exportable="false"></Column>
        <Column field="name" header="Name" sortable style="min-width: 16rem"></Column>
        <Column field="location" header="Location" sortable style="min-width: 16rem"></Column>
        <Column field="customer.name" header="Customer" sortable style="min-width: 16rem">
          <template #body="slotProps">
            {{ slotProps.data.customer?.name || 'N/A' }}
          </template>
        </Column>
        <Column
          field="assigned_interface.name"
          header="PE Interface"
          sortable
          style="min-width: 16rem"
        >
          <template #body="slotProps">
            {{
              `${slotProps.data.assigned_interface?.router?.hostname || 'N/A'} - ${
                slotProps.data.assigned_interface?.name || 'N/A'
              }`
            }}
          </template>
        </Column>
        <Column field="dhcp_scope" header="DHCP Scope" sortable style="min-width: 16rem"></Column>
        <Column :exportable="false" style="min-width: 12rem">
          <template #body="slotProps">
            <Button
              icon="pi pi-pencil"
              outlined
              rounded
              class="mr-2"
              @click="editSite(slotProps.data)"
            />
            <Button
              icon="pi pi-trash"
              outlined
              rounded
              severity="danger"
              @click="confirmDeleteSite(slotProps.data)"
            />
          </template>
        </Column>
      </DataTable>
    </div>

    <!-- Site Dialog -->
    <Dialog
      v-model:visible="siteDialogVisible"
      :appendTo="'body'"
      :style="{ width: '450px' }"
      :header="isEditing ? 'Edit Site' : 'New Site'"
      :modal="true"
    >
      <div class="flex flex-col gap-6">
        <div>
          <label for="name" class="block font-bold mb-3">Name</label>
          <InputText
            id="name"
            v-model.trim="currentSite.name"
            required="true"
            autofocus
            :invalid="submitted && !currentSite.name"
            fluid
          />
          <small v-if="submitted && !currentSite.name" class="text-red-500"
            >Name is required.</small
          >
        </div>
        <div>
          <label for="location" class="block font-bold mb-3">Location</label>
          <InputText id="location" v-model="currentSite.location" fluid />
        </div>
        <div>
          <label for="pe_router" class="block font-bold mb-3">PE Router</label>
          <Dropdown
            id="pe_router"
            v-model="selectedPERouter"
            :options="peRouters"
            optionLabel="hostname"
            placeholder="Select a PE Router"
            @change="fetchPERouterInterfaces"
            required
            :disabled="isEditing"
          />
        </div>
        <div v-if="selectedPERouter">
          <label for="pe_interface" class="block font-bold mb-3">PE Interface</label>
          <Dropdown
            id="pe_interface"
            v-model="currentSite.assigned_interface"
            :options="peInterfaces"
            optionLabel="name"
            placeholder="Select a PE Interface"
            required
            :disabled="isEditing"
          />
        </div>
        <div>
          <label for="customer" class="block font-bold mb-3">Customer</label>
          <Dropdown
            id="customer"
            v-model="currentSite.customer"
            :options="customers"
            optionLabel="name"
            placeholder="Select a Customer"
            required
            :disabled="isEditing"
          />
        </div>
      </div>
      <template #footer>
        <Button label="Cancel" icon="pi pi-times" text @click="closeDialog" />
        <Button label="Save" icon="pi pi-check" @click="saveSite" />
      </template>
    </Dialog>
    <!-- Confirm Delete Site Dialog -->
    <Dialog
      v-model:visible="deleteSiteDialog"
      :style="{ width: '450px' }"
      header="Confirm"
      :modal="true"
    >
      <div class="flex items-center gap-4">
        <i class="pi pi-exclamation-triangle !text-3xl" />
        <span v-if="currentSite"
          >Are you sure you want to delete <b>{{ currentSite.name }}</b
          >?</span
        >
      </div>
      <template #footer>
        <Button label="No" icon="pi pi-times" text @click="deleteSiteDialog = false" />
        <Button label="Yes" icon="pi pi-check" severity="danger" @click="deleteSite" />
      </template>
    </Dialog>

    <!-- Confirm Delete Selected Sites Dialog -->
    <Dialog
      v-model:visible="deleteSitesDialog"
      :style="{ width: '450px' }"
      header="Confirm"
      :modal="true"
    >
      <div class="flex items-center gap-4">
        <i class="pi pi-exclamation-triangle !text-3xl" />
        <span>Are you sure you want to delete the selected sites?</span>
      </div>
      <template #footer>
        <Button label="No" icon="pi pi-times" text @click="deleteSitesDialog = false" />
        <Button label="Yes" icon="pi pi-check" severity="danger" @click="deleteSelectedSites" />
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import SiteService from '@/service/SiteService'
import RouterService from '@/service/RouterService'
import CustomerService from '@/service/CustomerService'
import { FilterMatchMode } from '@primevue/core/api'

// State
const sites = ref([])
const customers = ref([])
const peRouters = ref([])
const peInterfaces = ref([])
const selectedPERouter = ref(null)
const selectedSites = ref([])
const currentSite = ref({})
const siteDialogVisible = ref(false)
const deleteSiteDialog = ref(false)
const deleteSitesDialog = ref(false)
const loading = ref(false)
const submitted = ref(false)
const isEditing = ref(false)
const filters = ref({
  global: { value: null, matchMode: FilterMatchMode.CONTAINS },
})

// Toast
const toast = useToast()

// Fetch Sites
const fetchSites = async () => {
  loading.value = true
  try {
    const response = await SiteService.getSites()
    sites.value = Array.isArray(response) ? response : []
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to fetch sites',
      life: 3000,
    })
  } finally {
    loading.value = false
  }
}

// Fetch Customers
const fetchCustomers = async () => {
  try {
    const response = await CustomerService.getCustomers()
    customers.value = Array.isArray(response) ? response : []
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to fetch customers',
      life: 3000,
    })
  }
}

// Fetch PE Routers
const fetchPERouters = async () => {
  try {
    const response = await RouterService.getPERouters() // Fetch only PE routers
    peRouters.value = Array.isArray(response) ? response : []
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to fetch PE routers',
      life: 3000,
    })
  }
}

// Fetch PE Router Interfaces
const fetchPERouterInterfaces = async () => {
  if (!selectedPERouter.value) return
  try {
    const response = await RouterService.getConnectedInterfaces(selectedPERouter.value.id)
    // Filter interfaces to only show those that are not connected
    peInterfaces.value = response.filter((iface) => !iface.connected)
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to fetch PE router interfaces',
      life: 3000,
    })
  }
}
const editSite = (site) => {
  currentSite.value = { ...site }
  selectedPERouter.value = site.pe_router || null
  peInterfaces.value = [] // Reset interfaces
  isEditing.value = true
  siteDialogVisible.value = true
}
const confirmDeleteSite = (site) => {
  currentSite.value = site
  deleteSiteDialog.value = true
}
const deleteSite = async () => {
  try {
    await SiteService.deleteSite(currentSite.value.id)
    toast.add({
      severity: 'success',
      summary: 'Success',
      detail: 'Site deleted successfully',
      life: 3000,
    })
    fetchSites() // Refresh the site list
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to delete site',
      life: 3000,
    })
  } finally {
    deleteSiteDialog.value = false
  }
}
const confirmDeleteSelected = () => {
  if (!selectedSites.value.length) {
    toast.add({
      severity: 'warn',
      summary: 'Warning',
      detail: 'No sites selected for deletion',
      life: 3000,
    })
    return
  }
  deleteSitesDialog.value = true
}
const deleteSelectedSites = async () => {
  try {
    const ids = selectedSites.value.map((site) => site.id)
    await Promise.all(ids.map((id) => SiteService.deleteSite(id)))
    toast.add({
      severity: 'success',
      summary: 'Success',
      detail: 'Selected sites deleted successfully',
      life: 3000,
    })
    fetchSites() // Refresh the site list
    selectedSites.value = [] // Clear the selection
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to delete selected sites',
      life: 3000,
    })
  } finally {
    deleteSitesDialog.value = false
  }
}
const saveSite = async () => {
  submitted.value = true

  // Validate required fields
  if (
    !currentSite.value.name ||
    !currentSite.value.customer ||
    !currentSite.value.assigned_interface
  ) {
    toast.add({
      severity: 'warn',
      summary: 'Warning',
      detail: 'Please fill in all required fields',
      life: 3000,
    })
    return
  }

  try {
    if (isEditing.value) {
      // Update existing site with only editable fields
      const updatePayload = {
        id: currentSite.value.id,
        name: currentSite.value.name,
        location: currentSite.value.location,
      }
      await SiteService.updateSite(currentSite.value.id, updatePayload)
      toast.add({
        severity: 'success',
        summary: 'Success',
        detail: 'Site updated successfully',
        life: 3000,
      })
    } else {
      // Create new site with all fields
      const createPayload = {
        name: currentSite.value.name,
        location: currentSite.value.location,
        customer_id: currentSite.value.customer.id,
        assigned_interface_id: currentSite.value.assigned_interface.id,
      }
      await SiteService.createSite(createPayload)
      toast.add({
        severity: 'success',
        summary: 'Success',
        detail: 'Site created successfully',
        life: 3000,
      })
    }

    // Refresh the site list and close the dialog
    fetchSites()
    siteDialogVisible.value = false
    submitted.value = false
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to save site',
      life: 3000,
    })
  }
}
const closeDialog = () => {
  siteDialogVisible.value = false
  submitted.value = false
}
// Open New Site Dialog
const openNewSiteDialog = () => {
  currentSite.value = {}
  selectedPERouter.value = null
  peInterfaces.value = []
  submitted.value = false
  isEditing.value = false
  siteDialogVisible.value = true
}

// Lifecycle
onMounted(() => {
  fetchSites()
  fetchCustomers()
  fetchPERouters()
})
</script>

<style scoped>
.field {
  margin-bottom: 1rem;
}
</style>
