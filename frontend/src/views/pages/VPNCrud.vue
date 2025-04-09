<template>
  <div>
    <div class="card">
      <div class="font-semibold text-2xl mb-4">Manage VPNs</div>
      <!-- Toolbar -->
      <Toolbar class="mb-6">
        <template #start>
          <Button
            label="New"
            icon="pi pi-plus"
            severity="secondary"
            class="mr-2"
            @click="openNew"
          />
          <Button
            label="Delete"
            icon="pi pi-trash"
            severity="secondary"
            @click="confirmDeleteSelected"
            :disabled="!selectedVPNs || !selectedVPNs.length"
          />
        </template>
      </Toolbar>

      <!-- DataTable -->
      <DataTable
        ref="dt"
        v-model:selection="selectedVPNs"
        :value="vpns"
        dataKey="id"
        :paginator="true"
        :rows="10"
        paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
        :rowsPerPageOptions="[5, 10, 25]"
        currentPageReportTemplate="Showing {first} to {last} of {totalRecords} VPNs"
        selectionMode="multiple"
        :loading="loading"
        class="p-datatable-gridlines"
      >
        <template #header>
          <div class="flex flex-wrap gap-2 items-center justify-between">
            <h4 class="m-0">VPNs</h4>
          </div>
        </template>

        <Column selectionMode="multiple" style="width: 3rem" :exportable="false"></Column>
        <Column field="name" header="Name" sortable style="min-width: 16rem">
          <template #body="slotProps">
            <span class="font-bold">{{ slotProps.data.name }}</span>
          </template>
        </Column>
        <Column field="customer.name" header="Customer" sortable style="min-width: 16rem">
          <template #body="slotProps">
            <Tag :value="slotProps.data.customer || 'N/A'" severity="info" />
          </template>
        </Column>
        <Column field="site_count" header="Sites" sortable style="min-width: 8rem">
          <template #body="slotProps">
            <Badge :value="slotProps.data.site_count || 0" severity="success" />
          </template>
        </Column>
        <Column :exportable="false" style="min-width: 12rem">
          <template #body="slotProps">
            <Button
              icon="pi pi-eye"
              outlined
              rounded
              class="mr-2"
              severity="help"
              @click="viewVPN(slotProps.data)"
            />
            <Button
              icon="pi pi-pencil"
              outlined
              rounded
              class="mr-2"
              @click="editVPN(slotProps.data)"
            />
            <Button
              icon="pi pi-trash"
              outlined
              rounded
              severity="danger"
              @click="confirmDeleteVPN(slotProps.data)"
            />
          </template>
        </Column>
      </DataTable>
    </div>

    <!-- VPN Dialog -->
    <Dialog
      v-model:visible="vpnDialog"
      :appendTo="'body'"
      :style="{ width: '850px' }"
      :header="isEditing ? 'Edit VPN' : 'New VPN'"
      :modal="true"
      class="p-fluid"
    >
      <div class="grid">
        <!-- Left Column - Basic Info -->
        <div class="col-12 md:col-5">
          <div class="card">
            <h5>Basic Information</h5>
            <div class="field">
              <label for="name" class="block font-bold mb-3">Name*</label>
              <InputText
                id="name"
                v-model.trim="vpn.name"
                :class="{ 'p-invalid': submitted && !vpn.name }"
                required
                autofocus
              />
              <small v-if="submitted && !vpn.name" class="text-red-500"> Name is required. </small>
            </div>

            <div class="field">
              <label for="customer" class="block font-bold mb-3">Customer*</label>
              <Dropdown
                id="customer"
                v-model="selectedCustomer"
                :options="customers"
                optionLabel="name"
                placeholder="Select a Customer"
                :class="{ 'p-invalid': submitted && !selectedCustomer }"
                @change="handleCustomerChange"
                :disabled="isEditing"
              />
              <small v-if="submitted && !selectedCustomer" class="text-red-500">
                Customer is required.
              </small>
            </div>

            <div class="field">
              <label for="description" class="block font-bold mb-3">Description</label>
              <Textarea id="description" v-model="vpn.description" rows="3" autoResize />
            </div>
          </div>
        </div>

        <!-- Right Column - Site Selection -->
        <div class="col-12 md:col-7">
          <div class="card">
            <h5>Site Selection</h5>
            <small v-if="submitted && selectedSites.length < 2" class="text-red-500 block mb-3">
              At least two sites are required.
            </small>
            <DataTable
              v-model:selection="selectedSites"
              :value="customerSites"
              dataKey="id"
              :scrollable="true"
              scrollHeight="400px"
              selectionMode="multiple"
              class="p-datatable-sm"
            >
              <Column selectionMode="multiple" headerStyle="width: 3rem" />
              <Column field="name" header="Site Name" sortable>
                <template #body="slotProps">
                  <span :class="{ 'font-bold': isExistingSite(slotProps.data) }">
                    {{ slotProps.data.name }}
                  </span>
                </template>
              </Column>
              <Column field="location" header="Location" sortable />
            </DataTable>
          </div>
        </div>
      </div>

      <template #footer>
        <Button label="Cancel" icon="pi pi-times" text @click="hideDialog" />
        <Button label="Save" icon="pi pi-check" @click="saveVPN" />
      </template>
    </Dialog>

    <!-- Delete VPN Dialog -->
    <Dialog
      v-model:visible="deleteVPNDialog"
      :style="{ width: '450px' }"
      header="Confirm"
      :modal="true"
    >
      <div class="flex items-center gap-4">
        <i class="pi pi-exclamation-triangle !text-3xl" />
        <span v-if="vpn"
          >Are you sure you want to delete <b>{{ vpn.name }}</b
          >?</span
        >
      </div>
      <template #footer>
        <Button label="No" icon="pi pi-times" text @click="deleteVPNDialog = false" />
        <Button label="Yes" icon="pi pi-check" severity="danger" @click="deleteVPN" />
      </template>
    </Dialog>

    <!-- Delete Selected VPNs Dialog -->
    <Dialog
      v-model:visible="deleteSelectedVPNDialog"
      :style="{ width: '450px' }"
      header="Confirm"
      :modal="true"
    >
      <div class="flex items-center gap-4">
        <i class="pi pi-exclamation-triangle !text-3xl" />
        <span>Are you sure you want to delete the selected VPNs?</span>
      </div>
      <template #footer>
        <Button label="No" icon="pi pi-times" text @click="deleteSelectedVPNDialog = false" />
        <Button label="Yes" icon="pi pi-check" severity="danger" @click="deleteSelectedVPNs" />
      </template>
    </Dialog>
    <!-- VPN Details Dialog -->
    <Dialog
      v-model:visible="vpnDetailsDialogVisible"
      :style="{ width: '600px' }"
      header="VPN Details"
      :modal="true"
    >
      <div v-if="vpn" class="flex flex-col gap-4">
        <div class="grid">
          <!-- Basic Info -->
          <div class="col-12 md:col-6">
            <div class="card">
              <h5>Basic Information</h5>
              <div class="flex flex-col gap-3">
                <div>
                  <span class="font-bold">Name:</span>
                  <div class="mt-1">{{ vpn.name }}</div>
                </div>
                <div>
                  <span class="font-bold">Customer:</span>
                  <div class="mt-1">
                    <Tag :value="vpn.customer.name || 'N/A'" severity="info" />
                  </div>
                </div>
                <div>
                  <span class="font-bold">Description:</span>
                  <div class="mt-1">{{ vpn.description || 'N/A' }}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Sites -->
          <div class="col-12">
            <div class="card">
              <h5>Connected Sites</h5>
              <DataTable
                :value="vpn.sites"
                :scrollable="true"
                scrollHeight="200px"
                class="p-datatable-sm"
              >
                <Column field="name" header="Site Name" />
                <Column field="location" header="Location" />
              </DataTable>
            </div>
          </div>
        </div>
      </div>
    </Dialog>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import VPNService from '@/service/VPNService'
import CustomerService from '@/service/CustomerService'
import { FilterMatchMode } from '@primevue/core/api'

// Component state
const toast = useToast()
const loading = ref(false) // Add this line
const vpns = ref([])
const vpn = ref({})
const selectedVPNs = ref([])
const vpnDialog = ref(false)
const deleteVPNDialog = ref(false)
const submitted = ref(false)
const isEditing = ref(false)
const customers = ref([])
const dt = ref(null) // Add DataTable reference
const deleteSelectedVPNDialog = ref(false) // Add this missing ref
const selectedCustomer = ref(null)
const customerSites = ref([])
const selectedSites = ref([])
const vpnDetailsDialogVisible = ref(false)
const filters = ref({
  global: { value: null, matchMode: FilterMatchMode.CONTAINS },
})

onMounted(async () => {
  try {
    await Promise.all([fetchVPNs(), fetchCustomers()])
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to load initial data',
      life: 3000,
    })
  }
})
// Fetch VPNs
const fetchVPNs = async () => {
  loading.value = true
  try {
    const response = await VPNService.getVPNs()
    vpns.value = Array.isArray(response) ? response : []
  } catch (error) {
    vpns.value = []
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to fetch VPNs',
      life: 3000,
    })
  } finally {
    loading.value = false
  }
}

//onMounted

// Fetch Customers
const fetchCustomers = async () => {
  try {
    const response = await CustomerService.getCustomers()
    customers.value = Array.isArray(response) ? response : []
  } catch (error) {
    customers.value = []
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to fetch customers',
      life: 3000,
    })
  }
}
// Handle customer selection change
const handleCustomerChange = async () => {
  if (selectedCustomer.value) {
    try {
      const response = await CustomerService.getCustomer(selectedCustomer.value.id)
      console.log('Customer sites:', response)
      customerSites.value = response.sites
      selectedSites.value = []
    } catch (error) {
      toast.add({
        severity: 'error',
        summary: 'Error',
        detail: 'Failed to load customer sites',
        life: 3000,
      })
    }
  }
}
// edit VPN
const editVPN = async (vpnData) => {
  try {
    vpn.value = { ...vpnData }
    selectedCustomer.value = {
      id: vpnData.customer_id,
      name: vpnData.customer,
    }

    // Fetch customer details including sites
    if (selectedCustomer.value) {
      const response = await CustomerService.getCustomer(selectedCustomer.value.id)
      customerSites.value = response.sites || []

      // Get full VPN details including sites
      const vpnDetails = await VPNService.getVPN(vpnData.id)

      // Set selected sites based on the VPN's current sites
      selectedSites.value = customerSites.value.filter((site) =>
        vpnDetails.sites.some((vpnSite) => vpnSite.id === site.id),
      )
    }

    isEditing.value = true
    vpnDialog.value = true
  } catch (error) {
    console.error('Error in editVPN:', error)
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to load VPN details',
      life: 3000,
    })
  }
}
// View VPN Details
const viewVPN = async (vpnData) => {
  try {
    // Get full VPN details including sites
    const vpnDetails = await VPNService.getVPN(vpnData.id)
    vpn.value = vpnDetails
    vpnDetailsDialogVisible.value = true
  } catch (error) {
    console.error('Error fetching VPN details:', error)
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to load VPN details',
      life: 3000,
    })
  }
}
// Open new VPN dialog
const openNew = () => {
  vpn.value = {}
  selectedCustomer.value = null
  customerSites.value = []
  selectedSites.value = []
  submitted.value = false
  isEditing.value = false
  vpnDialog.value = true
}
const isExistingSite = (site) => {
  if (!isEditing.value || !vpn.value.sites) return false
  return selectedSites.value.some((s) => s.id === site.id)
}
// Hide dialog
const hideDialog = () => {
  vpnDialog.value = false
  submitted.value = false
}

// Save VPN
const saveVPN = async () => {
  submitted.value = true

  if (!vpn.value.name || !selectedCustomer.value || selectedSites.value.length < 2) {
    toast.add({
      severity: 'warn',
      summary: 'Warning',
      detail: 'Please fill in all required fields and select at least two sites',
      life: 3000,
    })
    return
  }

  try {
    const vpnData = {
      name: vpn.value.name,
      description: vpn.value.description,
      customer_id: selectedCustomer.value.id,
    }

    if (isEditing.value) {
      // Handle edit case
      const existingSites = new Set(vpn.value.sites?.map((site) => site.id) || [])
      const selectedSiteIds = new Set(selectedSites.value.map((site) => site.id))

      // Find sites to remove
      const sitesToRemove = [...existingSites].filter((id) => !selectedSiteIds.has(id))

      // Find sites to add
      const sitesToAdd = [...selectedSiteIds].filter((id) => !existingSites.has(id))

      // Update VPN basic info
      await VPNService.updateVPN(vpn.value.id, vpnData)

      // Remove sites that were unselected
      for (const siteId of sitesToRemove) {
        await VPNService.removeSiteFromVPN(vpn.value.id, siteId)
      }

      // Add newly selected sites
      for (const siteId of sitesToAdd) {
        await VPNService.addSiteToVPN(vpn.value.id, siteId)
      }

      toast.add({
        severity: 'success',
        summary: 'Success',
        detail: 'VPN updated successfully',
        life: 3000,
      })
    } else {
      // Handle create case
      const savedVPN = await VPNService.createVPN(vpnData)

      // Add selected sites to the VPN
      for (const site of selectedSites.value) {
        await VPNService.addSiteToVPN(savedVPN.id, site.id)
      }

      toast.add({
        severity: 'success',
        summary: 'Success',
        detail: 'VPN created successfully',
        life: 3000,
      })
    }

    // Refresh VPN list and close dialog
    vpns.value = await VPNService.getVPNs()
    vpnDialog.value = false
    submitted.value = false
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail:
        error.response?.data?.error || `Failed to ${isEditing.value ? 'update' : 'create'} VPN`,
      life: 3000,
    })
  }
}

// Delete confirmation
const confirmDeleteVPN = (vpnData) => {
  vpn.value = vpnData
  deleteVPNDialog.value = true
}

// Delete VPN
const deleteVPN = async () => {
  try {
    await VPNService.deleteVPN(vpn.value.id)
    vpns.value = vpns.value.filter((v) => v.id !== vpn.value.id)
    deleteVPNDialog.value = false

    toast.add({
      severity: 'success',
      summary: 'Success',
      detail: 'VPN deleted successfully',
      life: 3000,
    })
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: error.response?.data?.error || 'Failed to delete VPN',
      life: 3000,
    })
  }
}
// Delete Selected VPNs
const deleteSelectedVPNs = async () => {
  try {
    const ids = selectedVPNs.value.map((vpn) => vpn.id)
    await Promise.all(ids.map((id) => VPNService.deleteVPN(id)))

    toast.add({
      severity: 'success',
      summary: 'Success',
      detail: 'Selected VPNs deleted successfully',
      life: 3000,
    })

    await fetchVPNs() // Refresh the list
    deleteSelectedVPNDialog.value = false
    selectedVPNs.value = []
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to delete selected VPNs',
      life: 3000,
    })
  }
}

// Confirm Delete Selected
const confirmDeleteSelected = () => {
  deleteSelectedVPNDialog.value = true
}
</script>

<style scoped>
.p-dialog .grid {
  margin: 0;
}

.card {
  background: var(--surface-card);
  padding: 1.5rem;
  margin-bottom: 1rem;
  border-radius: var(--border-radius);
  box-shadow: var(--card-shadow);
}

.p-datatable.p-datatable-sm .p-datatable-header {
  padding: 0.5rem;
}

.p-datatable.p-datatable-sm .p-datatable-thead > tr > th {
  padding: 0.5rem;
}

.p-datatable.p-datatable-sm .p-datatable-tbody > tr > td {
  padding: 0.5rem;
}
</style>
