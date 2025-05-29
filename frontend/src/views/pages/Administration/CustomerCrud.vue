<template>
  <div>
    <div class="card">
      <div class="font-semibold text-2xl mb-4">Manage Customers</div>
      <!-- Toolbar -->
      <Toolbar class="mb-6">
        <template #start>
          <Button
            label="New"
            icon="pi pi-plus"
            severity="Primary"
            class="mr-2"
            @click="openNewCustomerDialog"
          />
          <Button
            label="Delete"
            icon="pi pi-trash"
            severity="secondary"
            @click="confirmDeleteSelected"
            :disabled="!selectedCustomers || !selectedCustomers.length"
          />
        </template>
        <template #end>
          <Button label="Export" icon="pi pi-upload" severity="secondary" @click="exportCSV" class="mr-2" />
          <Button
            label="Refresh"
            icon="pi pi-refresh"
            severity="secondary"
            @click="fetchCustomers"
            :loading="loading"
          />
        </template>
      </Toolbar>

      <!-- DataTable -->
      <DataTable
        ref="dt"
        v-model:selection="selectedCustomers"
        :value="customers"
        dataKey="id"
        :paginator="true"
        :rows="10"
        :filters="filters"
        paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
        :rowsPerPageOptions="[5, 10, 25]"
        currentPageReportTemplate="Showing {first} to {last} of {totalRecords} customers"
        selectionMode="multiple"
        :loading="loading"
        class="p-datatable-gridlines"
        stripedRows
        showGridlines
      >
        <template #header>
          <div class="flex flex-wrap gap-2 items-center justify-between">
            <div class="font-semibold text-xl my-2">Customers</div>
            <IconField>
              <InputIcon>
                <i class="pi pi-search" />
              </InputIcon>
              <InputText v-model="filters['global'].value" placeholder="Search customers..." />
            </IconField>
          </div>
        </template>

        <Column selectionMode="multiple" style="width: 3rem" :exportable="false"></Column>
        <Column field="name" header="Name" sortable style="min-width: 16rem"></Column>
        <Column field="email" header="Email" sortable style="min-width: 16rem"></Column>
        <Column
          field="phone_number"
          header="Phone Number"
          sortable
          style="min-width: 12rem"
        ></Column>
        <Column field="created_at" header="Registered" sortable style="min-width: 12rem">
          <template #body="slotProps">
            {{ formatDateTime(slotProps.data.created_at) }}
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
                @click="viewCustomer(slotProps.data)"
              />
              <Button
                icon="pi pi-pencil"
                outlined
                rounded
                class="mr-2"
                severity="warn"
                @click="editCustomer(slotProps.data)"
              />
              <Button
                icon="pi pi-trash"
                outlined
                rounded
                severity="danger"
                @click="confirmDeleteCustomer(slotProps.data)"
              />
            </div>
          </template>
        </Column>
        <template #empty>
          <div class="text-center text-color-secondary py-3">No customers registered yet.</div>
        </template>
      </DataTable>
    </div>

    <!-- Customer Details Dialog -->
    <Dialog
      v-model:visible="customerDetailsDialogVisible"
      :style="{ width: '700px', maxWidth: '95vw' }"
      header="Customer Details"
      :modal="true"
    >
      <div class="flex flex-col gap-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pl-4">
          <div>
            <div class="font-bold mb-1">Name:</div>
            <div class="mb-2">{{ currentCustomer.name }}</div>
            <div class="font-bold mb-1">Email:</div>
            <div class="mb-2">{{ currentCustomer.email }}</div>
            <div class="font-bold mb-1">Phone Number:</div>
            <div class="mb-2">{{ currentCustomer.phone_number }}</div>
            <div class="font-bold mb-1">Registered:</div>
            <div class="mb-2">{{ formatDateTime(currentCustomer.created_at) }}</div>
          </div>
          <div>
            <div class="font-bold mb-1">Description:</div>
            <div class="mb-2 whitespace-pre-line">
              {{ currentCustomer.description && currentCustomer.description.trim() ? currentCustomer.description : 'No description' }}
            </div>
          </div>
        </div>

        <div v-if="currentCustomer.sites && currentCustomer.sites.length" class="mt-2">
          <div class="font-bold text-lg mb-2">Sites</div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div
              v-for="site in currentCustomer.sites"
              :key="site.id"
              class="p-3 rounded site-card"
            >
              <div class="font-semibold">{{ site.name }}</div>
              <div class="text-sm text-color-secondary">{{ site.description }}</div>
              <div class="mt-1 text-xs">
                <span class="font-bold">Location:</span> {{ site.location || '-' }}<br>
                <span class="font-bold">Customer Edge:</span> {{ site.router || '-' }}
              </div>
            </div>
          </div>
        </div>

        <div v-if="currentCustomer.vpns && currentCustomer.vpns.length" class="mt-2">
          <div class="font-bold text-lg mb-2">VPNs</div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div
              v-for="vpn in currentCustomer.vpns"
              :key="vpn.id"
              class="p-3 rounded vpn-card"
            >
              <div class="font-semibold">{{ vpn.name }}</div>
              <div class="text-sm text-color-secondary">{{ vpn.description }}</div>
              <div class="mt-1 text-xs">
                <span class="font-bold">Connects:</span>
                <div v-if="vpn.sites && vpn.sites.length" class="flex flex-wrap gap-2 mt-1">
                  <Tag
                    v-for="site in vpn.sites"
                    :key="site.id"
                    :value="site.name"
                    class="mb-1"
                    style="max-width: 100%; white-space: normal;"
                  />
                </div>
                <span v-else>-</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <Button
          label="Close"
          icon="pi pi-times"
          text
          @click="customerDetailsDialogVisible = false"
        />
      </template>
    </Dialog>

    <!-- Customer Dialog -->
    <Dialog
      v-model:visible="customerDialogVisible"
      :appendTo="'body'"
      :style="{ width: '450px' }"
      :header="isEditing ? 'Edit Customer' : 'New Customer'"
      :modal="true"
    >
      <div class="flex flex-col gap-6">
        <div>
          <label for="name" class="block font-bold mb-3">Name</label>
          <InputText
            id="name"
            v-model.trim="currentCustomer.name"
            required="true"
            autofocus
            :invalid="submitted && !currentCustomer.name"
            fluid
          />
          <small v-if="submitted && !currentCustomer.name" class="text-red-500"
            >Name is required.</small
          >
        </div>
        <div>
          <label for="email" class="block font-bold mb-3">Email</label>
          <InputText id="email" v-model="currentCustomer.email" type="email" fluid />
        </div>
        <div>
          <label for="phone_number" class="block font-bold mb-3">Phone Number</label>
          <InputText id="phone_number" v-model="currentCustomer.phone_number" fluid />
        </div>
        <div>
          <label for="description" class="block font-bold mb-3">Description</label>
          <Textarea
            id="description"
            v-model="currentCustomer.description"
            rows="3"
            cols="20"
            fluid
          />
        </div>
      </div>

      <template #footer>
        <Button label="Cancel" icon="pi pi-times" text @click="closeDialog" />
        <Button label="Save" icon="pi pi-check" @click="saveCustomer" />
      </template>
    </Dialog>
    <!-- Confirm Delete Customer Dialog -->
    <Dialog
      v-model:visible="deleteCustomerDialog"
      :style="{ width: '450px' }"
      header="Confirm"
      :modal="true"
    >
      <div class="flex items-center gap-4">
        <i class="pi pi-exclamation-triangle !text-3xl" />
        <span v-if="currentCustomer"
          >Are you sure you want to delete <b>{{ currentCustomer.name }}</b
          >?</span
        >
      </div>
      <template #footer>
        <Button label="No" icon="pi pi-times" text @click="deleteCustomerDialog = false" />
        <Button label="Yes" icon="pi pi-check" severity="danger" @click="deleteCustomer" />
      </template>
    </Dialog>

    <!-- Confirm Delete Selected Customers Dialog -->
    <Dialog
      v-model:visible="deleteCustomersDialog"
      :style="{ width: '450px' }"
      header="Confirm"
      :modal="true"
    >
      <div class="flex items-center gap-4">
        <i class="pi pi-exclamation-triangle !text-3xl" />
        <span>Are you sure you want to delete the selected customers?</span>
      </div>
      <template #footer>
        <Button label="No" icon="pi pi-times" text @click="deleteCustomersDialog = false" />
        <Button label="Yes" icon="pi pi-check" severity="danger" @click="deleteSelectedCustomers" />
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
import { ref, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'
import CustomerService from '@/service/CustomerService'
import { FilterMatchMode } from '@primevue/core/api'
import Tag from 'primevue/tag'

// State
const customers = ref([])
const selectedCustomers = ref([])
const currentCustomer = ref({})
const customerDialogVisible = ref(false)
const customerDetailsDialogVisible = ref(false) // New state for details dialog
const deleteCustomerDialog = ref(false)
const deleteCustomersDialog = ref(false)
const loading = ref(false)
const submitted = ref(false)
const isEditing = ref(false)
const dt = ref(null) // Reference for the DataTable
const filters = ref({
  global: { value: null, matchMode: FilterMatchMode.CONTAINS },
})

// Message state (like SiteCrud)
const toast = useToast()
const message = ref('')
const messageType = ref('success')

// Icon helper (like SiteCrud)
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

// Unified message function
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

// Fetch Customers
const fetchCustomers = async () => {
  loading.value = true
  try {
    const response = await CustomerService.getCustomers()
    customers.value = Array.isArray(response) ? response : [] // Ensure it's an array
  } catch (error) {
    customers.value = [] // Fallback to an empty array on error
    showMessage('Failed to fetch customers', 'error')
  } finally {
    loading.value = false
  }
}

// Fetch and show customer details (with sites and vpns)
const viewCustomer = async (customer) => {
  try {
    const data = await CustomerService.getCustomer(customer.id)
    currentCustomer.value = data
    customerDetailsDialogVisible.value = true
  } catch (error) {
    showMessage('Failed to fetch customer details', 'error')
  }
}

// Open New Customer Dialog
const openNewCustomerDialog = () => {
  currentCustomer.value = {}
  submitted.value = false
  isEditing.value = false
  customerDialogVisible.value = true
}

// Edit Customer
const editCustomer = (customer) => {
  currentCustomer.value = { ...customer }
  isEditing.value = true
  customerDialogVisible.value = true
}

// Save Customer
const saveCustomer = async () => {
  submitted.value = true
  if (!currentCustomer.value.name) return

  try {
    if (isEditing.value) {
      await CustomerService.updateCustomer(currentCustomer.value.id, currentCustomer.value)
      showMessage('Customer updated successfully')
    } else {
      await CustomerService.createCustomer(currentCustomer.value)
      showMessage('Customer created successfully')
    }
    fetchCustomers()
    customerDialogVisible.value = false
  } catch (error) {
    showMessage('Failed to save customer', 'error')
  }
}

// Confirm Delete Customer
const confirmDeleteCustomer = (customer) => {
  currentCustomer.value = customer
  deleteCustomerDialog.value = true
}

// Delete Customer
const deleteCustomer = async () => {
  try {
    await CustomerService.deleteCustomer(currentCustomer.value.id)
    showMessage('Customer deleted successfully')
    fetchCustomers()
  } catch (error) {
    showMessage('Failed to delete customer', 'error')
  } finally {
    deleteCustomerDialog.value = false
  }
}

// Confirm Delete Selected Customers
const confirmDeleteSelected = () => {
  deleteCustomersDialog.value = true
}

// Delete Selected Customers
const deleteSelectedCustomers = async () => {
  try {
    const ids = selectedCustomers.value.map((customer) => customer.id)
    await Promise.all(ids.map((id) => CustomerService.deleteCustomer(id)))
    showMessage('Customers deleted successfully')
    fetchCustomers()
  } catch (error) {
    showMessage('Failed to delete customers', 'error')
  } finally {
    deleteCustomersDialog.value = false
    selectedCustomers.value = []
  }
}

// Export CSV
const exportCSV = () => {
  if (dt.value) {
    dt.value.exportCSV() // Call the exportCSV method on the DataTable reference
  } else {
    console.error('DataTable reference is not available.')
  }
}

// Utility: Format Date
const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString()
}

// Utility: Format Date and Time
const formatDateTime = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  // Format: YYYY-MM-DD HH:mm:ss
  const pad = (n) => n.toString().padStart(2, '0')
  const year = date.getFullYear()
  const month = pad(date.getMonth() + 1)
  const day = pad(date.getDate())
  const hours = pad(date.getHours())
  const minutes = pad(date.getMinutes())
  const seconds = pad(date.getSeconds())
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

// Lifecycle
onMounted(fetchCustomers)
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

/* Floating message positioning (like SiteCrud) */
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
