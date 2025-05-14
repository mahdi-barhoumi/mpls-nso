<template>
  <div class="card h-full">
    <div class="card-header">
      <h5 class="text-lg m-0">Customers Overview</h5>
      <div class="flex items-center gap-2">
        <Button
          icon="pi pi-refresh"
          text
          rounded
          size="small"
          :loading="loading"
          @click="fetchCustomerData"
          tooltip="Refresh"
        />
        <Button
          icon="pi pi-external-link"
          text
          rounded
          size="small"
          @click="navigateToCustomers"
          tooltip="Manage Customers"
        />
        <div
          class="flex items-center justify-center bg-green-100 dark:bg-green-400/10 rounded-lg w-8 h-8"
        >
          <i class="pi pi-users text-green-500"></i>
        </div>
      </div>
    </div>

    <div class="card-content">
      <!-- Quick Stats -->
      <div class="grid grid-cols-3 gap-2 mb-3">
        <div class="surface-100 p-2 border-round">
          <div class="text-base font-medium">{{ stats.totalCustomers }}</div>
          <div class="text-500 text-xs">Customers</div>
        </div>
        <div class="surface-100 p-2 border-round">
          <div class="text-base font-medium">{{ stats.totalSites }}</div>
          <div class="text-500 text-xs">Total Sites</div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex justify-center items-center p-4">
        <i class="pi pi-spin pi-spinner text-primary" style="font-size: 1.5rem"></i>
      </div>

      <!-- Recent Activity -->
      <div v-else-if="recentCustomers.length > 0" class="overflow-y-auto custom-scrollbar">
        <div
          v-for="customer in recentCustomers"
          :key="customer.id"
          class="p-2 border-round surface-50 mb-2 cursor-pointer hover:surface-100 transition-colors duration-200"
          @click="viewCustomerDetails(customer.id)"
        >
          <div class="flex justify-between items-center">
            <div>
              <div class="font-medium text-sm">{{ customer.name }}</div>
              <div class="text-500 text-xs">{{ customer.email }}</div>
            </div>
            <Tag :value="`${customer.vpns?.length || 0} VPNs`" severity="info" />
          </div>
          <div class="flex justify-between mt-2">
            <div class="text-xs text-500">
              <i class="pi pi-map-marker mr-1"></i>
              {{ customer.sites?.length || 0 }} Sites
            </div>
            <div class="text-xs text-500">
              <i class="pi pi-calendar mr-1"></i>
              {{ new Date(customer.created_at).toLocaleDateString() }}
            </div>
          </div>
        </div>
      </div>

      <div v-else class="text-center text-500 text-sm p-3">No customers found</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import Tag from 'primevue/tag'
import Button from 'primevue/button'
import CustomerService from '@/service/CustomerService'
import VPNService from '@/service/VPNService'
import SiteService from '@/service/SiteService'

const router = useRouter()
const toast = useToast()
const loading = ref(false)
const stats = ref({
  totalCustomers: 0,
  activeServices: 0,
  totalSites: 0,
})
const recentCustomers = ref([])

const fetchCustomerData = async () => {
  loading.value = true
  try {
    const [customerResponse, vpnResponse, siteResponse] = await Promise.all([
      CustomerService.getCustomers(),
      VPNService.getVPNs(),
      SiteService.getSites(),
    ])

    const customers = Array.isArray(customerResponse) ? customerResponse : []
    const vpns = Array.isArray(vpnResponse) ? vpnResponse : []
    const sites = Array.isArray(siteResponse) ? siteResponse : []

    // Create a map of customer IDs to their sites
    const customerSites = sites.reduce((acc, site) => {
      if (site.customer?.id) {
        if (!acc[site.customer.id]) {
          acc[site.customer.id] = []
        }
        acc[site.customer.id].push(site)
      }
      return acc
    }, {})

    // Create a map of customer IDs to their VPNs
    const customerVPNs = vpns.reduce((acc, vpn) => {
      if (vpn.customer_id) {
        if (!acc[vpn.customer_id]) {
          acc[vpn.customer_id] = []
        }
        acc[vpn.customer_id].push(vpn)
      }
      return acc
    }, {})

    // Calculate statistics
    const totalSites = sites.length
    const activeVpns = vpns.filter((vpn) => vpn.status === 'active').length

    stats.value = {
      totalCustomers: customers.length,
      activeServices: activeVpns,
      totalSites,
    }

    // Process recent customers with their related data
    const sortableCustomers = [...customers]
    recentCustomers.value = sortableCustomers
      .sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0))
      .slice(0, 5)
      .map((customer) => ({
        ...customer,
        vpns: customerVPNs[customer.id] || [],
        sites: customerSites[customer.id] || [],
      }))
  } catch (error) {
    console.error('Error fetching customer data:', error)
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to load customer data',
      life: 3000,
    })
  } finally {
    loading.value = false
  }
}

const viewCustomerDetails = (customerId) => {
  router.push(`/customers/${customerId}`)
}

const navigateToCustomers = () => {
  router.push('/customers')
}

onMounted(() => {
  fetchCustomerData()
  const interval = setInterval(fetchCustomerData, 60000)
  onUnmounted(() => clearInterval(interval))
})
</script>
