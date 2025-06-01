<template>
  <div>
    <div class="card vpn-card">
      <div class="font-semibold text-2xl mb-4">Manage VPNs</div>
      <!-- Toolbar -->
      <Toolbar class="mb-6">
        <template #start>
          <Button
            label="New"
            icon="pi pi-plus"
            severity="primary"
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
        <template #end>
          <Button label="Export" icon="pi pi-upload" severity="secondary" @click="exportCSV" class="mr-2" />
          <Button label="Refresh" icon="pi pi-refresh" severity="secondary" @click="fetchVPNs" :loading="loading" />
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
        :filters="filters"
        paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
        :rowsPerPageOptions="[5, 10, 25]"
        currentPageReportTemplate="Showing {first} to {last} of {totalRecords} VPNs"
        selectionMode="multiple"
        :loading="loading"
        class="p-datatable-gridlines"
        stripedRows
        showGridlines
      >
        <template #header>
          <div class="flex flex-wrap gap-2 items-center justify-between">
            <div class="font-semibold text-xl my-2">VPNs</div>
            <IconField>
              <InputIcon>
                <i class="pi pi-search" />
              </InputIcon>
              <InputText v-model="filters['global'].value" placeholder="Search VPNs..." />
            </IconField>
          </div>
        </template>

        <Column selectionMode="multiple" style="width: 3rem" :exportable="false"></Column>
        <Column field="name" header="Name" sortable style="min-width: 10rem">
          <template #body="slotProps">
            <span class="font-bold">{{ slotProps.data.name }}</span>
          </template>
        </Column>
        <Column field="customer.name" header="Customer" sortable style="min-width: 10rem">
          <template #body="slotProps">
            <span class="text-700">{{ slotProps.data.customer?.name || slotProps.data.customer || 'N/A' }}</span>
          </template>
        </Column>
        <Column field="site_count" header="Sites" sortable style="min-width: 10rem">
          <template #body="slotProps">
            <Badge :value="slotProps.data.site_count || 0" severRemoity="success" />
          </template>
        </Column>
        <Column field="created_at" header="Created" sortable style="min-width: 10rem">
          <template #body="slotProps">
            <span>{{ formatDateTime(slotProps.data.created_at) }}</span>
          </template>
        </Column>
        <Column :exportable="false" style="min-width: 12rem" headerClass="text-center" bodyClass="actions-center">
          <template #body="slotProps">
            <div class="actions-center">
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
                severity="warn"
                @click="editVPN(slotProps.data)"
              />
              <Button
                icon="pi pi-trash"
                outlined
                rounded
                severity="danger"
                @click="confirmDeleteVPN(slotProps.data)"
              />
            </div>
          </template>
        </Column>
        <template #empty>
          <div class="text-center text-color-secondary py-3">No VPNs registered yet.</div>
        </template>
      </DataTable>
    </div>

    <!-- VPN Dialog -->
    <Dialog
      v-model:visible="vpnDialogVisible"
      :appendTo="'body'"
      :style="{ width: '450px' }"
      :header="isEditing ? 'Edit VPN' : 'New VPN'"
      :modal="true"
    >
      <div class="flex flex-col gap-6">
        <div>
          <label for="name" class="block font-bold mb-3">Name:</label>
          <InputText
            id="name"
            v-model.trim="formData.name"
            required
            autofocus
            :invalid="submitted && !formData.name"
            fluid
            placeholder="Enter VPN name"
          />
          <small v-if="submitted && !formData.name" class="text-red-500">Name is required.</small>
        </div>
        <div>
          <label for="description" class="block font-bold mb-3">Description:</label>
          <Textarea
            id="description"
            v-model="formData.description"
            rows="3"
            fluid
            placeholder="Enter description"
          />
        </div>
        <div v-if="!isEditing">
          <label for="customer" class="block font-bold mb-3">Customer:</label>
          <Dropdown
            id="customer"
            v-model="formData.customer_id"
            :options="customers"
            optionLabel="name"
            optionValue="id"
            placeholder="Select customer"
            :class="{ 'p-invalid': submitted && !formData.customer_id }"
            class="w-full"
            showClear
            filter
            filterPlaceholder="Search customers..."
            @change="handleCustomerChange"
          />
          <small v-if="submitted && !formData.customer_id" class="text-red-500">
            Customer is required.
          </small>
        </div>
        <div>
          <label class="block font-bold mb-3">Sites:</label>
          <DataTable
            v-model:selection="formData.site_ids"
            :value="customerSites"
            dataKey="id"
            selectionMode="multiple"
            class="p-datatable-sm"
            stripedRows
            showGridlines
            :scrollable="true"
            scrollHeight="200px"
          >
            <Column selectionMode="multiple" headerStyle="width: 3rem" />
            <Column field="name" header="Site" sortable />
            <Column field="location" header="Location" sortable />
            <!-- Customer Edge column, using backend structure -->
            <Column header="Customer Edge">
              <template #body="slotProps">
                <span>
                  {{ slotProps.data.router || 'N/A' }}
                </span>
              </template>
            </Column>
          </DataTable>
          <small v-if="submitted && (!formData.site_ids || formData.site_ids.length < 2)" class="text-red-500">
            At least two sites are required.
          </small>
        </div>
        <small v-if="formError" class="text-red-500 block mt-2">{{ formError }}</small>
      </div>
      <template #footer>
        <Button label="Cancel" icon="pi pi-times" text @click="cancelForm" />
        <Button label="Save" icon="pi pi-check" :loading="saving" @click="handleSave" />
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
      :style="{ width: '700px', maxWidth: '95vw' }"
      header="VPN Details"
      :modal="true"
    >
      <div v-if="vpn" class="flex flex-col gap-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pl-4">
          <div>
            <div class="font-bold mb-1">Name:</div>
            <div class="mb-2">{{ vpn.name }}</div>
            <div class="font-bold mb-1">Customer:</div>
            <div class="mb-2">
              <div>{{ vpn.customer?.name || '-' }}</div>
              <div v-if="vpn.customer">
                <small class="text-500">Email: {{ vpn.customer.email || '-' }}</small><br>
                <small class="text-500">Phone: {{ vpn.customer.phone_number || '-' }}</small>
              </div>
            </div>
            <div class="font-bold mb-1">Description:</div>
            <div class="mb-2 whitespace-pre-line">
              {{ vpn.description && vpn.description.trim() ? vpn.description : 'No description' }}
            </div>
          </div>
          <div>
            <div class="font-bold mb-1">Created:</div>
            <div class="mb-2">{{ formatDateTime(vpn.created_at) || '-' }}</div>
            <div class="font-bold mb-1">Last Updated:</div>
            <div class="mb-2">{{ formatDateTime(vpn.updated_at) || '-' }}</div>
          </div>
        </div>
        <div>
          <div class="font-bold mb-2">Connected Sites:</div>
          <DataTable
            :value="vpn.sites"
            :scrollable="true"
            scrollHeight="220px"
            class="p-datatable-sm"
            stripedRows
            showGridlines
          >
            <Column field="name" header="Site" />
            <Column field="location" header="Location" />
            <Column header="VRF">
              <template #body="slotProps">
                <span v-if="slotProps.data.vrf">
                  {{ slotProps.data.vrf.name || '-' }}
                  <small v-if="slotProps.data.vrf.rd" class="text-500">(RD: {{ slotProps.data.vrf.rd }})</small>
                </span>
                <span v-else>-</span>
              </template>
            </Column>
            <Column header="Customer Edge">
              <template #body="slotProps">
                <span v-if="slotProps.data.router">
                  {{ slotProps.data.router.hostname || '-' }}
                </span>
                <span v-else>-</span>
              </template>
            </Column>
          </DataTable>
        </div>
      </div>
      <template #footer>
        <Button label="Close" icon="pi pi-times" text @click="vpnDetailsDialogVisible = false" />
      </template>
    </Dialog>

    <!-- Floating Message Alert -->
    <Toast ref="toast" position="top-right" />
    <div v-if="message" class="fixed top-0 right-0 z-5 m-3" style="z-index: 1100">
      <Message :severity="messageType === 'error' ? 'error' : 'success'" :closable="true" @close="message = ''"
        class="shadow-3">
        <template #messageicon>
          <i :class="getIcon(messageType)" class="mr-2"></i>
        </template>
        {{ message }}
      </Message>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted, watch } from 'vue'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import Message from 'primevue/message'
import Toast from 'primevue/toast'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Dropdown from 'primevue/dropdown'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Badge from 'primevue/badge'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import { FilterMatchMode } from '@primevue/core/api'
import VPNService from '@/service/VPNService'
import CustomerService from '@/service/CustomerService'

// Component state
const toast = useToast()
const loading = ref(false)
const vpns = ref([])
const customers = ref([])
const customerSites = ref([])
const selectedVPNs = ref([])
const dt = ref(null)
const vpnDialogVisible = ref(false)
const deleteVPNDialog = ref(false)
const deleteSelectedVPNDialog = ref(false)
const vpnDetailsDialogVisible = ref(false)
const message = ref('')
const messageType = ref('success')
const filters = ref({
  global: { value: null, matchMode: FilterMatchMode.CONTAINS },
})
const isEditing = ref(false)
const submitted = ref(false)
const saving = ref(false)
const formError = ref('')
const formData = ref({
  id: null,
  name: '',
  description: '',
  customer_id: '',
  site_ids: [],
})
const currentVPN = ref({})
const vpn = ref(null) // Add this line to define the vpn ref

// Helper for floating message icon
const getIcon = (type) => {
  switch (type) {
    case 'error':
      return 'pi pi-times-circle'
    case 'success':
      return 'pi pi-check-circle'
    case 'warning':
      return 'pi pi-exclamation-triangle'
    case 'info':
      return 'pi pi-info-circle'
    default:
      return 'pi pi-check-circle'
  }
}

// Helper to format ISO date string to 'YYYY-MM-DD HH:mm:ss'
const formatDateTime = (isoString) => {
  if (!isoString) return ''
  const d = new Date(isoString)
  const pad = (n) => n.toString().padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

// Message
const showMessage = (msg, type = 'success') => {
  toast.add({
    severity: type === 'error' ? 'error' : 'success',
    summary: type === 'error' ? 'Error' : 'Success',
    detail: msg,
    life: 5000,
  })
  message.value = msg
  messageType.value = type
  setTimeout(() => {
    message.value = ''
  }, 5000)
}

onMounted(async () => {
  try {
    await Promise.all([fetchVPNs(), fetchCustomers()])
  } catch (error) {
    showMessage('Failed to load initial data', 'error')
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
    showMessage('Failed to fetch VPNs', 'error')
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
    customers.value = []
    showMessage('Failed to fetch customers', 'error')
  }
}

// Fetch sites for selected customer
const handleCustomerChange = async () => {
  if (formData.value.customer_id) {
    try {
      const response = await CustomerService.getCustomer(formData.value.customer_id)
      customerSites.value = response.sites || []
      // If editing, preserve selected sites that still exist for this customer
      if (isEditing.value) {
        const validSiteIds = customerSites.value.map(s => s.id)
        formData.value.site_ids = formData.value.site_ids.filter(id => validSiteIds.includes(id))
      } else {
        formData.value.site_ids = []
      }
    } catch (error) {
      customerSites.value = []
      showMessage('Failed to load customer sites', 'error')
    }
  } else {
    customerSites.value = []
    formData.value.site_ids = []
  }
}

// Open new VPN dialog
const openNew = () => {
  formData.value = {
    id: null,
    name: '',
    description: '',
    customer_id: '',
    site_ids: [],
  }
  customerSites.value = []
  isEditing.value = false
  vpnDialogVisible.value = true
  formError.value = ''
  submitted.value = false
}

// Edit VPN
const editVPN = async (vpnData) => {
  try {
    // Fetch full VPN details
    const vpnDetails = await VPNService.getVPN(vpnData.id)
    
    // Set form data first
    formData.value = {
      id: vpnDetails.id,
      name: vpnDetails.name,
      description: vpnDetails.description || '',
      customer_id: vpnDetails.customer.id || vpnDetails.customer_id,
      site_ids: [], // This will be populated with site objects, not just IDs
    }
    
    currentVPN.value = vpnDetails
    isEditing.value = true
    
    // Load customer sites for this customer
    try {
      const response = await CustomerService.getCustomer(formData.value.customer_id)
      customerSites.value = response.sites || []
      
      // Set selected sites AFTER customerSites is loaded
      // IMPORTANT: Store site OBJECTS, not just IDs, for DataTable selection
      if (vpnDetails.sites && Array.isArray(vpnDetails.sites)) {
        formData.value.site_ids = customerSites.value.filter(site =>
          vpnDetails.sites.some(vpnSite => vpnSite.id === site.id)
        )
      } else {
        formData.value.site_ids = []
      }
    } catch (error) {
      customerSites.value = []
      formData.value.site_ids = []
      showMessage('Failed to load customer sites', 'error')
    }
    
    vpnDialogVisible.value = true
    formError.value = ''
    submitted.value = false
  } catch (error) {
    showMessage('Failed to load VPN details', 'error')
  }
}

// View VPN details
const viewVPN = async (vpnData) => {
  try {
    const vpnDetails = await VPNService.getVPN(vpnData.id)
    vpn.value = vpnDetails
    vpnDetailsDialogVisible.value = true
  } catch (error) {
    showMessage('Failed to load VPN details', 'error')
  }
}

// Cancel form
const cancelForm = () => {
  vpnDialogVisible.value = false
  formError.value = ''
  submitted.value = false
}

// Save VPN (create or update)
const handleSave = async () => {
  submitted.value = true
  formError.value = ''
  if (!formData.value.name || !formData.value.customer_id || !formData.value.site_ids || formData.value.site_ids.length < 2) {
    formError.value = 'Please fill in all required fields.'
    return
  }
  saving.value = true
  try {
    // Extract site IDs from site objects for API calls
    const siteIds = formData.value.site_ids.map(site => site.id)
    
    if (isEditing.value) {
      await VPNService.updateVPN(formData.value.id, {
        name: formData.value.name,
        description: formData.value.description,
        sites: siteIds, // Send IDs to API
      })
      showMessage('VPN updated successfully')
    } else {
      // Create VPN, then assign sites
      const created = await VPNService.createVPN({
        name: formData.value.name,
        description: formData.value.description,
        customer_id: formData.value.customer_id,
      })
      await VPNService.updateVPN(created.id, {
        sites: siteIds, // Send IDs to API
      })
      showMessage('VPN created successfully')
    }
    vpnDialogVisible.value = false
    await fetchVPNs()
  } catch (error) {
    formError.value = error.message || 'Failed to save VPN.'
  } finally {
    saving.value = false
    submitted.value = false
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

    showMessage('VPN deleted successfully')
  } catch (error) {
    showMessage(error.response?.data?.error || 'Failed to delete VPN', 'error')
  }
}
// Delete Selected VPNs
const deleteSelectedVPNs = async () => {
  try {
    const ids = selectedVPNs.value.map((vpn) => vpn.id)
    await Promise.all(ids.map((id) => VPNService.deleteVPN(id)))
    showMessage('Selected VPNs deleted successfully')
    await fetchVPNs()
    deleteSelectedVPNDialog.value = false
    selectedVPNs.value = []
  } catch (error) {
    showMessage('Failed to delete selected VPNs', 'error')
  }
}

// Confirm Delete Selected
const confirmDeleteSelected = () => {
  deleteSelectedVPNDialog.value = true
}

// Export CSV
const exportCSV = () => {
  if (dt.value) {
    dt.value.exportCSV()
  }
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

/* Darken the card background color using a pseudo element overlay */
.site-card,
.vpn-card {
  position: relative;
  border: none;
  overflow: hidden;
}

.site-card::before,
.vpn-card::before {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: rgba(255, 255, 255, 0.02);
  z-index: 1;
  border-radius: inherit;
  transition: background 0.2s;
}

.site-card > *,
.vpn-card > * {
  position: relative;
  z-index: 2;
}

/* Center actions in the Actions column */
.actions-center {
  display: flex;
  justify-content: center;
  align-items: center;
}

/* Floating message positioning (like CustomerCrud) */
.fixed {
  position: fixed !important;
}

.top-0 {
  top: 0 !important;
}

.right-0 {
  right: 0 !important;
}

.z-5 {
  z-index: 1100 !important;
}

/* Center Routing column header */
:deep(.p-datatable-thead th.justify-center) .p-datatable-column-title {
  justify-content: center;
  display: flex;
  width: 100%;
  text-align: center;
}

/* DataTable paddings for compact look */
.p-datatable.p-datatable-sm .p-datatable-header {
  padding: 0.5rem;
}

.p-datatable.p-datatable-sm .p-datatable-thead > tr > th,
.p-datatable.p-datatable-sm .p-datatable-tbody > tr > td {
  padding: 0.5rem;
}
</style>
