<template>
  <div>
    <h2>Site Management</h2>

    <!-- Create Site Form -->
    <div v-if="showCreateForm" style="border: 1px solid #ccc; padding: 20px; margin: 20px 0">
      <h3>{{ isEditing ? 'Edit Site' : 'Create New Site' }}</h3>

      <div style="margin-bottom: 15px">
        <label>Name*:</label>
        <input
          v-model="formData.name"
          type="text"
          required
          style="width: 100%; padding: 8px; margin-top: 5px"
        />
      </div>

      <div style="margin-bottom: 15px">
        <label>Location:</label>
        <input
          v-model="formData.location"
          type="text"
          style="width: 100%; padding: 8px; margin-top: 5px"
        />
      </div>

      <div style="margin-bottom: 15px">
        <label>Description:</label>
        <textarea
          v-model="formData.description"
          style="width: 100%; padding: 8px; margin-top: 5px; height: 60px"
        ></textarea>
      </div>

      <div style="margin-bottom: 15px">
        <label>Link Network:</label>
        <input
          v-model="formData.link_network"
          type="text"
          placeholder="e.g., 192.168.0.0"
          style="width: 100%; padding: 8px; margin-top: 5px"
        />
      </div>

      <div v-if="!isEditing" style="margin-bottom: 15px">
        <label>Customer*:</label>
        <select
          v-model="formData.customer_id"
          required
          style="width: 100%; padding: 8px; margin-top: 5px"
        >
          <option value="">Select Customer</option>
          <option v-for="customer in customers" :key="customer.id" :value="customer.id">
            {{ customer.name }}
          </option>
        </select>
      </div>

      <div v-if="!isEditing" style="margin-bottom: 15px">
        <label>PE Router*:</label>
        <select
          v-model="selectedPERouter"
          @change="fetchPEInterfaces"
          required
          style="width: 100%; padding: 8px; margin-top: 5px"
        >
          <option value="">Select PE Router</option>
          <option v-for="router in peRouters" :key="router.id" :value="router.id">
            {{ router.hostname }}
          </option>
        </select>
      </div>

      <div v-if="!isEditing && selectedPERouter" style="margin-bottom: 15px">
        <label>PE Interface*:</label>
        <select
          v-model="formData.assigned_interface_id"
          required
          style="width: 100%; padding: 8px; margin-top: 5px"
        >
          <option value="">Select Interface</option>
          <option v-for="iface in peInterfaces" :key="iface.id" :value="iface.id">
            {{ iface.name }}
          </option>
        </select>
      </div>

      <div style="margin-top: 20px">
        <button @click="saveSite" :disabled="saving" style="padding: 10px 20px; margin-right: 10px">
          {{ saving ? 'Saving...' : isEditing ? 'Update' : 'Create' }}
        </button>
        <button @click="cancelForm" style="padding: 10px 20px">Cancel</button>
      </div>

      <div v-if="formError" style="color: red; margin-top: 10px">
        {{ formError }}
      </div>
    </div>

    <!-- Action Buttons -->
    <div style="margin: 20px 0">
      <button
        @click="openCreateForm"
        v-if="!showCreateForm"
        style="padding: 10px 20px; margin-right: 10px"
      >
        Create New Site
      </button>
      <button @click="fetchSites" style="padding: 10px 20px">Refresh</button>
    </div>

    <!-- Sites List -->
    <div v-if="loading" style="padding: 20px; text-align: center">Loading sites...</div>

    <div v-else-if="sites.length === 0" style="padding: 20px; text-align: center; color: #666">
      No sites found. Create your first site above.
    </div>

    <div v-else>
      <table style="width: 100%; border-collapse: collapse; margin-top: 20px">
        <thead>
          <tr style="background-color: #f5f5f5">
            <th style="border: 1px solid #ccc; padding: 10px; text-align: left">Name</th>
            <th style="border: 1px solid #ccc; padding: 10px; text-align: left">Location</th>
            <th style="border: 1px solid #ccc; padding: 10px; text-align: left">Customer</th>
            <th style="border: 1px solid #ccc; padding: 10px; text-align: left">Link Network</th>
            <th style="border: 1px solid #ccc; padding: 10px; text-align: left">PE Router</th>
            <th style="border: 1px solid #ccc; padding: 10px; text-align: left">Interface</th>
            <th style="border: 1px solid #ccc; padding: 10px; text-align: left">DHCP Scope</th>
            <th style="border: 1px solid #ccc; padding: 10px; text-align: left">Status</th>
            <th style="border: 1px solid #ccc; padding: 10px; text-align: left">Routing</th>
            <th style="border: 1px solid #ccc; padding: 10px; text-align: left">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="site in sites" :key="site.id">
            <td style="border: 1px solid #ccc; padding: 10px">{{ site.name }}</td>
            <td style="border: 1px solid #ccc; padding: 10px">{{ site.location || 'N/A' }}</td>
            <td style="border: 1px solid #ccc; padding: 10px">
              {{ site.customer?.name || 'N/A' }}
            </td>
            <td style="border: 1px solid #ccc; padding: 10px">{{ site.link_network || 'N/A' }}</td>
            <td style="border: 1px solid #ccc; padding: 10px">
              {{ site.assigned_interface?.router?.hostname || 'N/A' }}
            </td>
            <td style="border: 1px solid #ccc; padding: 10px">
              {{ site.assigned_interface?.name || 'N/A' }}
            </td>
            <td style="border: 1px solid #ccc; padding: 10px">{{ site.dhcp_scope || 'N/A' }}</td>
            <td style="border: 1px solid #ccc; padding: 10px">
              <span :style="{ color: getStatusColor(site.status) }">
                {{ getStatusText(site.status) }}
              </span>
            </td>
            <td style="border: 1px solid #ccc; padding: 10px">
              <span :style="{ color: site.has_routing ? 'green' : 'red' }">
                {{ site.has_routing ? 'Enabled' : 'Disabled' }}
              </span>
            </td>
            <td style="border: 1px solid #ccc; padding: 10px">
              <button @click="editSite(site)" style="padding: 5px 10px; margin-right: 5px">
                Edit
              </button>
              <button
                @click="deleteSite(site)"
                style="
                  padding: 5px 10px;
                  margin-right: 5px;
                  background-color: #dc3545;
                  color: white;
                "
                :disabled="deleting === site.id"
              >
                {{ deleting === site.id ? 'Deleting...' : 'Delete' }}
              </button>
              <button
                v-if="site.has_routing"
                @click="disableRouting(site)"
                style="padding: 5px 10px; background-color: #fd7e14; color: white"
                :disabled="routingAction === site.id"
              >
                {{ routingAction === site.id ? 'Processing...' : 'Disable Routing' }}
              </button>
              <button
                v-else
                @click="enableRouting(site)"
                :style="{
                  padding: '5px 10px',
                  backgroundColor: isStatusActive(site.status) ? '#28a745' : '#6c757d',
                  color: 'white',
                  opacity: isStatusActive(site.status) ? '1' : '0.6',
                  cursor: isStatusActive(site.status) ? 'pointer' : 'not-allowed',
                }"
                :disabled="routingAction === site.id || !isStatusActive(site.status)"
              >
                {{ routingAction === site.id ? 'Processing...' : 'Enable Routing' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Messages -->
    <div
      v-if="message"
      :style="{
        padding: '10px',
        marginTop: '20px',
        backgroundColor: messageType === 'error' ? '#f8d7da' : '#d4edda',
        color: messageType === 'error' ? '#721c24' : '#155724',
        border: '1px solid ' + (messageType === 'error' ? '#f5c6cb' : '#c3e6cb'),
        borderRadius: '4px',
      }"
    >
      {{ message }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import SiteService from '@/service/SiteService'
import RouterService from '@/service/RouterService'
import CustomerService from '@/service/CustomerService'

// State
const sites = ref([])
const customers = ref([])
const peRouters = ref([])
const peInterfaces = ref([])
const selectedPERouter = ref('')
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
  link_network: '',
  customer_id: '',
  assigned_interface_id: '',
})

// Helper functions for status handling
const isStatusActive = (status) => {
  // Handle both boolean and string status values
  if (typeof status === 'boolean') {
    return status === true
  }
  return status === 'active'
}

const getStatusText = (status) => {
  // Convert status to display text
  if (typeof status === 'boolean') {
    return status ? 'Active' : 'Inactive'
  }
  // Handle string status values
  if (status === 'active') return 'Active'
  if (status === 'inactive') return 'Inactive'
  return status || 'Offline'
}

const getStatusColor = (status) => {
  // Return appropriate color based on status
  if (isStatusActive(status)) {
    return 'green'
  }
  if (typeof status === 'boolean' && status === false) {
    return 'red'
  }
  if (status === 'inactive') {
    return 'red'
  }
  return 'orange' // fallback for other statuses
}

// Methods
const showMessage = (msg, type = 'success') => {
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
    link_network: '',
    customer_id: '',
    assigned_interface_id: '',
  }
  selectedPERouter.value = ''
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

const fetchPEInterfaces = async () => {
  if (!selectedPERouter.value) {
    peInterfaces.value = []
    return
  }

  try {
    const response = await RouterService.getConnectedInterfaces(selectedPERouter.value)
    peInterfaces.value = response.filter((iface) => !iface.connected)
  } catch (error) {
    console.error('Error fetching PE interfaces:', error)
    showMessage('Failed to fetch PE interfaces', 'error')
    peInterfaces.value = []
  }
}

const saveSite = async () => {
  formError.value = ''

  // Validate required fields
  if (!formData.value.name) {
    formError.value = 'Name is required'
    return
  }

  if (!isEditing.value) {
    if (!formData.value.customer_id || !formData.value.assigned_interface_id) {
      formError.value = 'Customer and PE Interface are required'
      return
    }
  }

  saving.value = true

  try {
    if (isEditing.value) {
      const updatePayload = {
        name: formData.value.name,
        location: formData.value.location,
        description: formData.value.description,
      }
      await SiteService.updateSite(formData.value.id, updatePayload)
      showMessage('Site updated successfully')
    } else {
      await SiteService.createSite(formData.value)
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
    link_network: site.link_network || '',
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
  if (!isStatusActive(site.status)) {
    showMessage('Cannot enable routing on inactive site', 'error')
    return
  }
  if (site.router_id === null || site.router_id === undefined) {
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
