<!-- filepath: c:\Users\Moutaa\Documents\mpls-nso\frontend\src\views\pages\SiteCrud.vue -->
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
        <Column field="customer.name" header="Customer" sortable style="min-width: 16rem"></Column>
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
          <label for="customer" class="block font-bold mb-3">Customer</label>
          <Dropdown
            id="customer"
            v-model="currentSite.customer"
            :options="customers"
            optionLabel="name"
            placeholder="Select a Customer"
            required
          />
        </div>
        <div>
          <label for="dhcp_scope" class="block font-bold mb-3">DHCP Scope</label>
          <InputText
            id="dhcp_scope"
            v-model="currentSite.dhcp_scope"
            fluid
            readonly
            placeholder="Managed by backend"
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
import CustomerService from '@/service/CustomerService'
import { FilterMatchMode } from '@primevue/core/api'

// State
const sites = ref([])
const customers = ref([])
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

// Open New Site Dialog
const openNewSiteDialog = () => {
  currentSite.value = {}
  submitted.value = false
  isEditing.value = false
  siteDialogVisible.value = true
}

// Edit Site
const editSite = (site) => {
  currentSite.value = { ...site }
  isEditing.value = true
  siteDialogVisible.value = true
}

// Save Site
const saveSite = async () => {
  submitted.value = true
  if (!currentSite.value.name || !currentSite.value.customer) return

  try {
    if (isEditing.value) {
      await SiteService.updateSite(currentSite.value.id, currentSite.value)
      toast.add({ severity: 'success', summary: 'Success', detail: 'Site Updated', life: 3000 })
    } else {
      await SiteService.createSite(currentSite.value)
      toast.add({ severity: 'success', summary: 'Success', detail: 'Site Created', life: 3000 })
    }
    fetchSites()
    siteDialogVisible.value = false
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to save site',
      life: 3000,
    })
  }
}

// Confirm Delete Site
const confirmDeleteSite = (site) => {
  currentSite.value = site
  deleteSiteDialog.value = true
}

// Delete Site
const deleteSite = async () => {
  try {
    await SiteService.deleteSite(currentSite.value.id)
    toast.add({ severity: 'success', summary: 'Success', detail: 'Site Deleted', life: 3000 })
    fetchSites()
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

// Confirm Delete Selected Sites
const confirmDeleteSelected = () => {
  deleteSitesDialog.value = true
}

// Delete Selected Sites
const deleteSelectedSites = async () => {
  try {
    const ids = selectedSites.value.map((site) => site.id)
    await Promise.all(ids.map((id) => SiteService.deleteSite(id)))
    toast.add({ severity: 'success', summary: 'Success', detail: 'Sites Deleted', life: 3000 })
    fetchSites()
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to delete sites',
      life: 3000,
    })
  } finally {
    deleteSitesDialog.value = false
    selectedSites.value = []
  }
}

// Lifecycle
onMounted(() => {
  fetchSites()
  fetchCustomers()
})
</script>

<style scoped>
.field {
  margin-bottom: 1rem;
}
</style>
