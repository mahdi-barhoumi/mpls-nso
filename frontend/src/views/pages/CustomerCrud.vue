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
          <Button label="Export" icon="pi pi-upload" severity="secondary" @click="exportCSV" />
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
      >
        <template #header>
          <div class="flex flex-wrap gap-2 items-center justify-between">
            <div class="font-semibold text-xl mb-4">Customers</div>
            <IconField>
              <InputIcon>
                <i class="pi pi-search" />
              </InputIcon>
              <InputText v-model="filters['global'].value" placeholder="Search..." />
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
        <Column field="created_at" header="Created At" sortable style="min-width: 12rem">
          <template #body="slotProps">
            {{ formatDate(slotProps.data.created_at) }}
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
          </template>
        </Column>
      </DataTable>
    </div>

    <!-- Customer Details Dialog -->
    <Dialog
      v-model:visible="customerDetailsDialogVisible"
      :style="{ width: '450px' }"
      header="Customer Details"
      :modal="true"
    >
      <div class="flex flex-col gap-4">
        <div><span class="font-bold">Name:</span> {{ currentCustomer.name }}</div>
        <div><span class="font-bold">Email:</span> {{ currentCustomer.email }}</div>
        <div><span class="font-bold">Phone Number:</span> {{ currentCustomer.phone_number }}</div>
        <div><span class="font-bold">Description:</span> {{ currentCustomer.description }}</div>
        <div>
          <span class="font-bold">Created At:</span> {{ formatDate(currentCustomer.created_at) }}
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'
import CustomerService from '@/service/CustomerService'
import { FilterMatchMode } from '@primevue/core/api'

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

// Toast and Confirm
const toast = useToast()
const confirm = useConfirm()

// Fetch Customers
const fetchCustomers = async () => {
  loading.value = true
  try {
    const response = await CustomerService.getCustomers()
    customers.value = Array.isArray(response) ? response : [] // Ensure it's an array
  } catch (error) {
    customers.value = [] // Fallback to an empty array on error
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to fetch customers',
      life: 3000,
    })
  } finally {
    loading.value = false
  }
}

// Open Customer Details Dialog
const viewCustomer = (customer) => {
  currentCustomer.value = { ...customer }
  customerDetailsDialogVisible.value = true
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
      toast.add({ severity: 'success', summary: 'Success', detail: 'Customer Updated', life: 3000 })
    } else {
      await CustomerService.createCustomer(currentCustomer.value)
      toast.add({ severity: 'success', summary: 'Success', detail: 'Customer Created', life: 3000 })
    }
    fetchCustomers()
    customerDialogVisible.value = false
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to save customer',
      life: 3000,
    })
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
    toast.add({ severity: 'success', summary: 'Success', detail: 'Customer Deleted', life: 3000 })
    fetchCustomers()
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to delete customer',
      life: 3000,
    })
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
    toast.add({ severity: 'success', summary: 'Success', detail: 'Customers Deleted', life: 3000 })
    fetchCustomers()
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to delete customers',
      life: 3000,
    })
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

// Lifecycle
onMounted(fetchCustomers)
</script>

<style scoped>
.field {
  margin-bottom: 1rem;
}
</style>
