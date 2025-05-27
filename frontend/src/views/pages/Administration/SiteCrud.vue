<template>
  <div class="card">
    <h5 class="mb-4">Site Management</h5>

    <!-- Toolbar -->
    <Toolbar class="mb-4">
      <template #start>
        <Button label="New" icon="pi pi-plus" class="mr-2" @click="openNewSiteDialog" />
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
          label="Refresh"
          icon="pi pi-refresh"
          severity="secondary"
          @click="fetchSites"
          :loading="loading"
        />
      </template>
    </Toolbar>

    <!-- Site Form Component -->
    <div v-if="showCreateForm" class="mb-5">
      <SiteForm
        :show="showCreateForm"
        :is-editing="isEditing"
        :customers="customers"
        :pe-routers="peRouters"
        :pe-interfaces="peInterfaces"
        :saving="saving"
        :error="formError"
        :initial-data="formData"
        @save="saveSite"
        @cancel="cancelForm"
        @pe-router-change="fetchPEInterfaces"
      />
    </div>

    <!-- Sites List Component -->
    <SiteList
      :sites="sites"
      :loading="loading"
      :deleting="deleting"
      :routing-action="routingAction"
      @edit="editSite"
      @delete="deleteSite"
      @enable-routing="enableRouting"
      @disable-routing="disableRouting"
    />

    <!-- Floating Message Alert Component -->
    <Toast ref="toast" position="top-right" />

    <!-- Alternative floating message using OverlayPanel if you prefer custom implementation -->
    <div v-if="message" class="fixed top-0 right-0 z-5 m-3" style="z-index: 1100">
      <Message
        :severity="messageType === 'error' ? 'error' : 'success'"
        :closable="true"
        @close="message = ''"
        class="shadow-3"
      >
        {{ message }}
      </Message>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import Message from 'primevue/message'
import Toast from 'primevue/toast'
import SiteForm from '@/components/SiteCrud/SiteForm.vue'
import SiteList from '@/components/SiteCrud/SiteList.vue'
import SiteService from '@/service/SiteService'
import RouterService from '@/service/RouterService'
import CustomerService from '@/service/CustomerService'

// Toast setup
const toast = useToast()

// State
const sites = ref([])
const customers = ref([])
const peRouters = ref([])
const peInterfaces = ref([])
const showCreateForm = ref(false)
const isEditing = ref(false)
const loading = ref(false)
const saving = ref(false)
const deleting = ref(null)
const routingAction = ref(null)
const message = ref('')
const messageType = ref('success')
const formError = ref('')

const formData = ref({
  name: '',
  location: '',
  description: '',
  customer_id: '',
  assigned_interface_id: '',
})

// Methods
const showMessage = (msg, type = 'success') => {
  // Use PrimeVue Toast for better UX
  toast.add({
    severity: type === 'error' ? 'error' : 'success',
    summary: type === 'error' ? 'Error' : 'Success',
    detail: msg,
    life: 5000,
  })

  // Also set local message for custom floating display if preferred
  message.value = msg
  messageType.value = type
  setTimeout(() => {
    message.value = ''
  }, 5000)
}

const openCreateForm = () => {
  formData.value = {
    name: '',
    location: '',
    description: '',
    customer_id: '',
    assigned_interface_id: '',
  }
  peInterfaces.value = []
  isEditing.value = false
  showCreateForm.value = true
  formError.value = ''
}

const cancelForm = () => {
  showCreateForm.value = false
  formError.value = ''
}

const fetchSites = async () => {
  loading.value = true
  try {
    const response = await SiteService.getSites()
    sites.value = Array.isArray(response) ? response : []
    showMessage('Sites loaded successfully')
  } catch (error) {
    console.error('Error fetching sites:', error)
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
    console.error('Error fetching customers:', error)
    showMessage('Failed to fetch customers', 'error')
  }
}

const fetchPERouters = async () => {
  try {
    const response = await RouterService.getPERouters()
    peRouters.value = Array.isArray(response) ? response : []
  } catch (error) {
    console.error('Error fetching PE routers:', error)
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
    console.error('Error fetching PE interfaces:', error)
    showMessage('Failed to fetch PE interfaces', 'error')
    peInterfaces.value = []
  }
}

const saveSite = async (siteData) => {
  formError.value = ''

  // Validate required fields
  if (!siteData.name) {
    formError.value = 'Name is required'
    return
  }

  if (!isEditing.value) {
    if (!siteData.customer_id || !siteData.assigned_interface_id) {
      formError.value = 'Customer and PE Interface are required'
      return
    }
  }

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
      await SiteService.createSite(siteData)
      showMessage('Site created successfully')
    }

    showCreateForm.value = false
    fetchSites()
  } catch (error) {
    console.error('Error saving site:', error)
    formError.value = 'Failed to save site. Please try again.'
  } finally {
    saving.value = false
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
  showCreateForm.value = true
  formError.value = ''
}

const deleteSite = async (site) => {
  if (!confirm(`Are you sure you want to delete "${site.name}"?`)) {
    return
  }

  deleting.value = site.id

  try {
    await SiteService.deleteSite(site.id)
    showMessage(`Site "${site.name}" deleted successfully`)
    fetchSites()
  } catch (error) {
    console.error('Error deleting site:', error)
    showMessage('Failed to delete site', 'error')
  } finally {
    deleting.value = null
  }
}

const enableRouting = async (site) => {
  // Status validation
  const isStatusActive = (status) => {
    if (typeof status === 'boolean') {
      return status === true
    }
    return status === 'active'
  }

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
    console.error('Error enabling routing:', error)
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
    console.error('Error disabling routing:', error)
    showMessage('Failed to disable routing', 'error')
  } finally {
    routingAction.value = null
  }
}

// Lifecycle
onMounted(() => {
  fetchSites()
  fetchCustomers()
  fetchPERouters()
})
</script>

<style scoped>
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
