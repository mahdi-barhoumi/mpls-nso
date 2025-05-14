<template>
  <div>
    <div class="card">
      <div class="flex justify-between items-center mb-6">
        <div class="font-semibold text-2xl">Manage Sites</div>
        <div class="flex gap-2">
          <Button
            label="New Site"
            icon="pi pi-plus"
            severity="primary"
            raised
            @click="openNewSiteDialog"
          />
          <Button
            label="Delete Selected"
            icon="pi pi-trash"
            severity="danger"
            raised
            @click="confirmDeleteSelected"
            :disabled="!selectedSites || !selectedSites.length"
          />
        </div>
      </div>

      <!-- Grid View -->
      <div v-if="!loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="site in sites"
          :key="site.id"
          class="relative bg-surface-0 dark:bg-surface-900 p-4 border-round-xl shadow-md transition-all duration-200 hover:shadow-lg"
          :class="{ 'border-primary border-2': selectedSites.includes(site) }"
        >
          <!-- Selection Checkbox -->
          <div class="absolute top-3 right-3 flex gap-2 items-center">
            <Tag
              :value="site.status || 'offline'"
              :severity="site.status === 'active' ? 'success' : 'warning'"
              class="mr-2"
            />
            <Checkbox
              v-model="selectedSites"
              :value="site"
              :binary="false"
              :class="{ '!border-primary': selectedSites.includes(site) }"
            />
          </div>

          <!-- Site Info -->
          <div class="flex flex-col gap-3">
            <div class="flex items-center gap-2">
              <i class="pi pi-building text-xl text-primary"></i>
              <div class="font-bold text-xl">{{ site.name }}</div>
            </div>

            <div class="flex flex-col gap-2 text-surface-600 dark:text-surface-200">
              <!-- Location -->
              <div class="flex items-center gap-2" v-if="site.location">
                <i class="pi pi-map-marker"></i>
                <span>{{ site.location }}</span>
              </div>

              <!-- Customer -->
              <div class="flex items-center gap-2">
                <i class="pi pi-users"></i>
                <span>{{ site.customer?.name || 'N/A' }}</span>
              </div>

              <!-- PE Interface -->
              <div class="flex items-center gap-2">
                <i class="pi pi-server"></i>
                <span
                  >{{ site.assigned_interface?.router?.hostname || 'N/A' }} -
                  {{ site.assigned_interface?.name || 'N/A' }}</span
                >
              </div>

              <!-- DHCP Scope -->
              <div class="flex items-center gap-2" v-if="site.dhcp_scope">
                <i class="pi pi-bolt"></i>
                <span>{{ site.dhcp_scope }}</span>
              </div>

              <!-- Routing Status -->
              <div class="flex items-center justify-between gap-2">
                <div class="flex items-center gap-2">
                  <i class="pi pi-compass" :class="{ 'text-green-500': site.has_routing }"></i>
                  <div v-if="site.has_routing" class="text-green-500 font-semibold">
                    Routing Enabled
                  </div>
                  <div v-else class="text-surface-400">Routing Disabled</div>
                </div>
                <Button
                  v-if="site.has_routing"
                  label="Disable"
                  icon="pi pi-power-off"
                  size="small"
                  severity="secondary"
                  text
                  @click="disableRouting(site)"
                  :loading="routingLoadingId === site.id"
                />
                <Button
                  v-else
                  label="Enable"
                  icon="pi pi-power-off"
                  size="small"
                  severity="secondary"
                  text
                  @click="enableRouting(site)"
                  :loading="routingLoadingId === site.id"
                  :disabled="site.status !== 'active'"
                />
              </div>
            </div>

            <!-- Actions -->
            <div class="flex gap-2 mt-3 justify-end">
              <Button
                icon="pi pi-pencil"
                text
                rounded
                severity="secondary"
                @click="editSite(site)"
                tooltip="Edit Site"
              />
              <Button
                icon="pi pi-trash"
                text
                rounded
                severity="danger"
                @click="confirmDeleteSite(site)"
                tooltip="Delete Site"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-else class="flex justify-center items-center p-8">
        <ProgressSpinner />
      </div>

      <!-- Empty State -->
      <div
        v-if="!loading && sites.length === 0"
        class="flex flex-col items-center justify-center p-8 text-surface-600 dark:text-surface-200"
      >
        <i class="pi pi-inbox text-5xl mb-4"></i>
        <div class="text-xl font-semibold mb-2">No Sites Found</div>
        <p>Get started by creating your first site.</p>
        <Button
          label="Create Site"
          icon="pi pi-plus"
          severity="primary"
          class="mt-4"
          @click="openNewSiteDialog"
        />
      </div>
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
const routingLoadingId = ref(null)

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
const enableRouting = async (site) => {
  routingLoadingId.value = site.id
  try {
    await SiteService.enableRouting(site.id)
    toast.add({
      severity: 'success',
      summary: 'Success',
      detail: `Routing enabled for ${site.name}`,
      life: 3000,
    })
    fetchSites()
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to enable routing',
      life: 3000,
    })
  } finally {
    routingLoadingId.value = null
  }
}
const disableRouting = async (site) => {
  routingLoadingId.value = site.id
  try {
    await SiteService.disableRouting(site.id)
    toast.add({
      severity: 'success',
      summary: 'Success',
      detail: `Routing disabled for ${site.name}`,
      life: 3000,
    })
    fetchSites()
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to disable routing',
      life: 3000,
    })
  } finally {
    routingLoadingId.value = null
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
.card {
  background: var(--surface-card);
  padding: 2rem;
  border-radius: var(--border-radius);
  margin-bottom: 1rem;
}

/* Add smooth transition for card selection */
.border-primary {
  transition: border-color 0.2s;
}
</style>
