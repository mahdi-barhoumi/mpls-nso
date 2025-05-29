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
            severity="Primary"
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
        <template #end>
          <Button
            label="Export"
            icon="pi pi-upload"
            severity="secondary"
            @click="exportCSV"
            class="mr-2"
          />
          <Button
            label="Refresh"
            icon="pi pi-refresh"
            severity="secondary"
            @click="fetchSites"
            :loading="loading"
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
        stripedRows
        showGridlines
      >
        <template #header>
          <div class="flex flex-wrap gap-2 items-center justify-between">
            <div class="font-semibold text-xl my-2">Sites</div>
            <IconField>
              <InputIcon>
                <i class="pi pi-search" />
              </InputIcon>
              <InputText v-model="filters['global'].value" placeholder="Search sites..." />
            </IconField>
          </div>
        </template>

        <Column selectionMode="multiple" style="width: 3rem" :exportable="false"></Column>
        <Column field="name" header="Name" sortable style="min-width: 14rem">
          <template #body="slotProps">
            <span class="text-900 font-medium">{{ slotProps.data.name }}</span>
          </template>
        </Column>
        <Column field="location" header="Location" sortable style="min-width: 10rem">
          <template #body="slotProps">
            <span class="text-700">{{ slotProps.data.location || 'N/A' }}</span>
          </template>
        </Column>
        <Column field="customer.name" header="Customer" sortable style="min-width: 12rem">
          <template #body="slotProps">
            <span class="text-700">{{ slotProps.data.customer?.name || 'N/A' }}</span>
          </template>
        </Column>
        <Column header="Provider Interface" style="min-width: 14rem">
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
        <Column field="CE_router.hostname" header="Customer Edge" sortable style="min-width: 12rem">
          <template #body="slotProps">
            <span class="text-700">{{ slotProps.data.CE_router?.hostname || 'N/A' }}</span>
          </template>
        </Column>
        <Column field="dhcp_scope" header="Management Subnet" sortable style="min-width: 10rem">
          <template #body="slotProps">
            <span class="text-700">{{ slotProps.data.dhcp_scope || 'N/A' }}</span>
          </template>
        </Column>
        <Column field="link_network" header="Link Subnet" sortable style="min-width: 10rem">
          <template #body="slotProps">
            <span class="text-700">{{ slotProps.data.link_network || 'N/A' }}</span>
          </template>
        </Column>
        <Column field="status" header="Status" sortable style="min-width: 8rem">
          <template #body="slotProps">
            <Tag
              :value="getStatusText(slotProps.data.status)"
              :severity="getStatusSeverity(slotProps.data.status)"
            />
          </template>
        </Column>
        <Column header="Routing" style="min-width: 10rem">
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
                @click="disableRouting(slotProps.data)"
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
                @click="enableRouting(slotProps.data)"
              />
            </div>
          </template>
        </Column>
        <Column
          :exportable="false"
          style="min-width: 12rem"
          headerClass="text-center"
          bodyClass="actions-center"
        >
          <template #body="slotProps">
            <div class="actions-center">
              <Button
                icon="pi pi-eye"
                outlined
                rounded
                class="mr-2"
                severity="help"
                @click="viewSite(slotProps.data)"
              />
              <Button
                icon="pi pi-pencil"
                outlined
                rounded
                class="mr-2"
                severity="warn"
                @click="editSite(slotProps.data)"
              />
              <Button
                icon="pi pi-trash"
                outlined
                rounded
                severity="danger"
                :loading="deleting === slotProps.data.id"
                @click="confirmDeleteSite(slotProps.data)"
              />
            </div>
          </template>
        </Column>
        <template #empty>
          <div class="text-center text-color-secondary py-3">No sites registered yet.</div>
        </template>
      </DataTable>
    </div>

    <!-- Site Details Dialog -->
    <Dialog
      v-model:visible="siteDetailsDialogVisible"
      :style="{ width: '700px', maxWidth: '95vw' }"
      header="Site Details"
      :modal="true"
    >
      <div class="flex flex-col gap-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pl-4">
          <div>
            <div class="font-bold mb-1">Name:</div>
            <div class="mb-2">{{ currentSite.name }}</div>
            <div class="font-bold mb-1">Location:</div>
            <div class="mb-2">{{ currentSite.location || '-' }}</div>
            <div class="font-bold mb-1">Customer:</div>
            <div class="mb-2">{{ currentSite.customer?.name || '-' }}</div>
            <div class="font-bold mb-1">Status:</div>
            <div class="mb-2">
              <Tag :value="getStatusText(currentSite.status)" :severity="getStatusSeverity(currentSite.status)" />
            </div>
          </div>
          <div>
            <div class="font-bold mb-1">Description:</div>
            <div class="mb-2 whitespace-pre-line">
              {{ currentSite.description && currentSite.description.trim() ? currentSite.description : 'No description' }}
            </div>
            <div class="font-bold mb-1">Provider Interface:</div>
            <div class="mb-2">
              <span>{{ currentSite.assigned_interface?.router?.hostname || '-' }}</span>
              <small v-if="currentSite.assigned_interface?.name" class="ml-2 text-500">via {{ currentSite.assigned_interface?.name }}</small>
            </div>
            <div class="font-bold mb-1">Customer Edge:</div>
            <div class="mb-2">{{ currentSite.CE_router?.hostname || '-' }}</div>
          </div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pl-4">
          <div>
            <div class="font-bold mb-1">Management Subnet:</div>
            <div class="mb-2">{{ currentSite.dhcp_scope || '-' }}</div>
          </div>
          <div>
            <div class="font-bold mb-1">Link Subnet:</div>
            <div class="mb-2">{{ currentSite.link_network || '-' }}</div>
          </div>
        </div>
      </div>
      <template #footer>
        <Button
          label="Close"
          icon="pi pi-times"
          text
          @click="siteDetailsDialogVisible = false"
        />
      </template>
    </Dialog>

    <!-- Site Form Dialog -->
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
            v-model.trim="formData.name"
            required="true"
            autofocus
            :invalid="submitted && !formData.name"
            fluid
          />
          <small v-if="submitted && !formData.name" class="text-red-500"
            >Name is required.</small
          >
        </div>
        <div>
          <label for="location" class="block font-bold mb-3">Location</label>
          <InputText id="location" v-model="formData.location" fluid />
        </div>
        <div>
          <label for="description" class="block font-bold mb-3">Description</label>
          <Textarea
            id="description"
            v-model="formData.description"
            rows="3"
            cols="20"
            fluid
          />
        </div>
        <div v-if="!isEditing">
          <label for="customer" class="block font-bold mb-3">Customer</label>
          <Dropdown
            id="customer"
            v-model="formData.customer_id"
            :options="customers"
            optionLabel="name"
            optionValue="id"
            placeholder="Select Customer"
            :class="{ 'p-invalid': submitted && !formData.customer_id }"
            class="w-full"
          />
          <small v-if="submitted && !formData.customer_id" class="text-red-500">
            Customer is required.
          </small>
        </div>
        <div v-if="!isEditing">
          <label for="peRouter" class="block font-bold mb-3">PE Router</label>
          <Dropdown
            id="peRouter"
            v-model="selectedPERouter"
            :options="peRouters"
            optionLabel="hostname"
            optionValue="id"
            placeholder="Select PE Router"
            :class="{ 'p-invalid': submitted && !selectedPERouter }"
            class="w-full"
            @change="handlePERouterChange"
          />
          <small v-if="submitted && !selectedPERouter" class="text-red-500">
            PE Router is required.
          </small>
        </div>
        <div v-if="!isEditing && selectedPERouter">
          <label for="interface" class="block font-bold mb-3">PE Interface</label>
          <Dropdown
            id="interface"
            v-model="formData.assigned_interface_id"
            :options="peInterfaces"
            optionLabel="name"
            optionValue="id"
            placeholder="Select Interface"
            :class="{ 'p-invalid': submitted && !formData.assigned_interface_id }"
            class="w-full"
          />
          <small v-if="submitted && !formData.assigned_interface_id" class="text-red-500">
            Interface is required.
          </small>
        </div>
        <small v-if="formError" class="text-red-500 block mt-2">{{ formError }}</small>
      </div>
      <template #footer>
        <Button label="Cancel" icon="pi pi-times" text @click="cancelForm" />
        <Button
          label="Save"
          icon="pi pi-check"
          :loading="saving"
          @click="handleSave"
        />
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

    <!-- Floating Message Alert -->
    <Toast ref="toast" position="top-right" />
    <div v-if="message" class="fixed top-0 right-0 z-5 m-3" style="z-index: 1100">
      <Message
        :severity="messageType === 'error' ? 'error' : 'success'"
        :closable="true"
        @close="message = ''"
        class="shadow-3"
      >
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
import Tag from 'primevue/tag'
import ProgressSpinner from 'primevue/progressspinner'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import { FilterMatchMode } from '@primevue/core/api'
import SiteService from '@/service/SiteService'
import RouterService from '@/service/RouterService'
import CustomerService from '@/service/CustomerService'

// State
const sites = ref([])
const customers = ref([])
const peRouters = ref([])
const peInterfaces = ref([])
const showCreateForm = ref(false) // legacy, not used
const isEditing = ref(false)
const loading = ref(false)
const saving = ref(false)
const deleting = ref(null)
const routingAction = ref(null)
const message = ref('')
const messageType = ref('success')
const formError = ref('')
const submitted = ref(false)
const selectedSites = ref([])
const filters = ref({
  global: { value: null, matchMode: FilterMatchMode.CONTAINS },
})

const formData = ref({
  name: '',
  location: '',
  description: '',
  customer_id: '',
  assigned_interface_id: '',
})

const selectedPERouter = ref('')
const dt = ref(null) // Add DataTable ref for export

// Dialog states
const siteDialogVisible = ref(false)
const siteDetailsDialogVisible = ref(false)
const deleteSiteDialog = ref(false)
const deleteSitesDialog = ref(false)
const currentSite = ref({})

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

// Message
const toast = useToast()
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

// CRUD and Form logic
const openNewSiteDialog = () => {
  formData.value = {
    name: '',
    location: '',
    description: '',
    customer_id: '',
    assigned_interface_id: '',
  }
  peInterfaces.value = []
  selectedPERouter.value = ''
  isEditing.value = false
  siteDialogVisible.value = true
  formError.value = ''
  submitted.value = false
}

const cancelForm = () => {
  siteDialogVisible.value = false
  formError.value = ''
  submitted.value = false
}

const handleSave = () => {
  submitted.value = true
  if (
    !formData.value.name ||
    (!isEditing.value &&
      (!formData.value.customer_id ||
        !selectedPERouter.value ||
        !formData.value.assigned_interface_id))
  ) {
    return
  }
  saveSite(formData.value)
}

const fetchSites = async () => {
  loading.value = true
  try {
    const response = await SiteService.getSites()
    sites.value = Array.isArray(response) ? response : []
  } catch (error) {
    sites.value = []
    showMessage('Failed to fetch sites', 'error')
  } finally {
    loading.value = false
  }
}

const fetchCustomers = async () => {
  try {
    const response = await CustomerService.getCustomers()
    customers.value = Array.isArray(response) ? response : []
  } catch (error) {
    customers.value = []
    showMessage('Failed to fetch customers', 'error')
  }
}

const fetchPERouters = async () => {
  try {
    const response = await RouterService.getPERouters()
    peRouters.value = Array.isArray(response) ? response : []
  } catch (error) {
    peRouters.value = []
    showMessage('Failed to fetch PE routers', 'error')
  }
}

const fetchPEInterfaces = async (routerId) => {
  if (!routerId) {
    peInterfaces.value = []
    return
  }
  try {
    const response = await RouterService.getConnectedInterfaces(routerId)
    peInterfaces.value = response.filter((iface) => !iface.connected)
  } catch (error) {
    peInterfaces.value = []
    showMessage('Failed to fetch PE interfaces', 'error')
  }
}

const handlePERouterChange = () => {
  fetchPEInterfaces(selectedPERouter.value)
  formData.value.assigned_interface_id = ''
}

const saveSite = async (siteData) => {
  formError.value = ''
  saving.value = true
  try {
    if (isEditing.value) {
      const updatePayload = {
        name: siteData.name,
        location: siteData.location,
        description: siteData.description,
      }
      await SiteService.updateSite(siteData.id, updatePayload)
      showMessage('Site updated successfully')
    } else {
      await SiteService.createSite({
        ...siteData,
        customer_id: siteData.customer_id,
        assigned_interface_id: siteData.assigned_interface_id,
      })
      showMessage('Site created successfully')
    }
    siteDialogVisible.value = false
    fetchSites()
  } catch (error) {
    formError.value = 'Failed to save site. Please try again.'
  } finally {
    saving.value = false
    submitted.value = false
  }
}

const viewSite = async (site) => {
  try {
    // Optionally fetch more details if needed
    currentSite.value = site
    siteDetailsDialogVisible.value = true
  } catch (error) {
    showMessage('Failed to fetch site details', 'error')
  }
}

const editSite = (site) => {
  formData.value = {
    id: site.id,
    name: site.name,
    location: site.location || '',
    description: site.description || '',
  }
  isEditing.value = true
  siteDialogVisible.value = true
  formError.value = ''
  submitted.value = false
}

const confirmDeleteSite = (site) => {
  currentSite.value = site
  deleteSiteDialog.value = true
}

const deleteSite = async () => {
  deleting.value = currentSite.value.id
  try {
    await SiteService.deleteSite(currentSite.value.id)
    showMessage(`Site "${currentSite.value.name}" deleted successfully`)
    fetchSites()
  } catch (error) {
    showMessage('Failed to delete site', 'error')
  } finally {
    deleting.value = null
    deleteSiteDialog.value = false
  }
}

const confirmDeleteSelected = () => {
  deleteSitesDialog.value = true
}

const deleteSelectedSites = async () => {
  try {
    const ids = selectedSites.value.map((site) => site.id)
    await Promise.all(ids.map((id) => SiteService.deleteSite(id)))
    showMessage('Sites deleted successfully')
    fetchSites()
  } catch (error) {
    showMessage('Failed to delete sites', 'error')
  } finally {
    deleteSitesDialog.value = false
    selectedSites.value = []
  }
}

const enableRouting = async (site) => {
  if (!isStatusActive(site.status)) {
    showMessage('Cannot enable routing on inactive site', 'error')
    return
  }
  if (site.CE_router === null || site.CE_router === undefined) {
    showMessage('No router is connected to this site', 'error')
    return
  }
  routingAction.value = site.id
  try {
    await SiteService.enableRouting(site.id)
    showMessage(`Routing enabled for "${site.name}"`)
    fetchSites()
  } catch (error) {
    showMessage('Failed to enable routing', 'error')
  } finally {
    routingAction.value = null
  }
}

const disableRouting = async (site) => {
  routingAction.value = site.id
  try {
    await SiteService.disableRouting(site.id)
    showMessage(`Routing disabled for "${site.name}"`)
    fetchSites()
  } catch (error) {
    showMessage('Failed to disable routing', 'error')
  } finally {
    routingAction.value = null
  }
}

// Export CSV
const exportCSV = () => {
  if (dt.value) {
    dt.value.exportCSV()
  }
}

// Lifecycle
onMounted(() => {
  fetchSites()
  fetchCustomers()
  fetchPERouters()
})

// Watch for initial data changes (for editing)
watch(
  () => formData.value,
  (newData) => {
    if (isEditing.value && newData) {
      formData.value = { ...newData }
    }
  },
  { immediate: true, deep: true },
)
</script>

<style scoped>
.field {
  margin-bottom: 1rem;
}
/* Center actions in the Actions column */
.actions-center {
  display: flex;
  justify-content: center;
  align-items: center;
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
  background: rgba(255, 255, 255, 0.02); /* subtle dark overlay */
  z-index: 1;
  border-radius: inherit;
  transition: background 0.2s;
}
.site-card > *,
.vpn-card > * {
  position: relative;
  z-index: 2;
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
</style>
