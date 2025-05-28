<template>
  <div class="card h-full">
    <div class="card-header">
      <h5 class="text-lg m-0">Service Overview</h5>
      <div class="flex items-center gap-2">
        <Button
          icon="pi pi-refresh"
          text
          rounded
          size="small"
          :loading="loading"
          @click="fetchServiceData"
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
          class="flex items-center justify-center bg-green-100 dark:bg-green-400/20 rounded-lg w-8 h-8 shadow"
        >
          <i class="pi pi-users text-green-500 text-xl"></i>
        </div>
      </div>
    </div>

    <div class="card-content">
      <!-- Quick Stats -->
      <div class="grid grid-cols-3 gap-4 mb-3">
        <div class="surface-100 p-2 pr-4 border-round flex flex-col items-center gap-1">
          <div class="flex items-center justify-center bg-blue-100 dark:bg-blue-400/20 rounded-full w-9 h-9 shadow mb-1">
            <i class="pi pi-users text-blue-500 text-xl"></i>
          </div>
          <div class="text-base font-medium">{{ stats.totalCustomers }}</div>
          <div class="text-500 text-xs">Customers</div>
        </div>
        <div class="surface-100 p-2 pr-4 border-round flex flex-col items-center gap-1">
          <div class="flex items-center justify-center bg-orange-100 dark:bg-orange-400/20 rounded-full w-9 h-9 shadow mb-1">
            <i class="pi pi-map-marker text-orange-500 text-xl"></i>
          </div>
          <div class="text-base font-medium">{{ stats.totalSites }}</div>
          <div class="text-500 text-xs">Sites</div>
        </div>
        <div class="surface-100 p-2 pr-4 border-round flex flex-col items-center gap-1">
          <div class="flex items-center justify-center bg-purple-100 dark:bg-purple-400/20 rounded-full w-9 h-9 shadow mb-1">
            <i class="pi pi-shield text-purple-500 text-xl"></i>
          </div>
          <div class="text-base font-medium">{{ stats.totalVpns }}</div>
          <div class="text-500 text-xs">VPNs</div>
        </div>
      </div>

      <!-- Separator -->
      <div class="w-full border-t border-gray-200 dark:border-surface-700 my-4"></div>

      <!-- Loading State -->
      <div v-if="loading" class="flex justify-center items-center p-4">
        <i class="pi pi-spin pi-spinner text-primary" style="font-size: 1.5rem"></i>
      </div>

      <!-- Recent Activity -->
      <div v-else-if="recentCustomers.length > 0">
        <div class="flex items-center my-2">
          <div class="text-sm font-bold" style="color: var(--surface-900)">
            Recent changes:
          </div>
          <Button
            icon="pi pi-list"
            text
            rounded
            size="small"
            class="ml-auto"
            tooltip="View All Activity"
          />
        </div>
        <div
          style="max-height: 260px; scrollbar-gutter: stable; scrollbar-width: thin;"
        >
          <div
            v-for="(customer, idx) in recentCustomers"
            :key="customer.id"
            :class="[
              'p-2 rounded-md mb-2 cursor-pointer hover:surface-100 transition-colors duration-200 recent-item-highlight'
            ]"
            @click="viewCustomerDetails(customer.id)"
          >
            <!-- Name, Sites, VPNs on the same row -->
            <div class="flex justify-between items-center">
              <div class="font-medium text-sm">{{ customer.name }}</div>
              <div class="flex flex-row items-center gap-2">
                <Tag :value="`${customer.vpns?.length || 0} VPNs`" severity="info" />
                <Tag :value="`${customer.sites?.length || 0} Sites`" severity="success" />
              </div>
            </div>
            <!-- Email/phone and time on the same row -->
            <div class="flex justify-between items-center mt-0.5">
              <div class="flex flex-col">
                <div class="text-500 text-xs flex items-center">
                  <i class="pi pi-envelope mr-2" style="font-size: 0.85em"></i>
                  {{ customer.email }}
                </div>
                <div v-if="customer.phone_number" class="text-500 text-xs flex items-center">
                  <i class="pi pi-phone mr-2" style="font-size: 0.85em"></i>
                  {{ customer.phone_number }}
                </div>
              </div>
              <div class="flex items-center text-xs text-500 ml-4">
                <i class="pi pi-calendar mr-1"></i>
                {{ formatDate(customer.lastActivity) }}
              </div>
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
  totalSites: 0,
  totalVpns: 0,
})
const recentCustomers = ref([])

function formatDate(date) {
  if (!date) return ''
  return new Date(date).toLocaleDateString()
}

const fetchServiceData = async () => {
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

    // Map customer IDs to their sites and VPNs
    const customerSites = {}
    const customerVPNs = {}
    const customerLastActivity = {}

    sites.forEach(site => {
      if (site.customer?.id) {
        if (!customerSites[site.customer.id]) customerSites[site.customer.id] = []
        customerSites[site.customer.id].push(site)
        // Track last activity for customer based on site
        if (!customerLastActivity[site.customer.id] || new Date(site.updated_at) > new Date(customerLastActivity[site.customer.id])) {
          customerLastActivity[site.customer.id] = site.updated_at || site.created_at
        }
      }
    })

    vpns.forEach(vpn => {
      if (vpn.customer_id) {
        if (!customerVPNs[vpn.customer_id]) customerVPNs[vpn.customer_id] = []
        customerVPNs[vpn.customer_id].push(vpn)
        // Track last activity for customer based on vpn
        if (!customerLastActivity[vpn.customer_id] || new Date(vpn.updated_at) > new Date(customerLastActivity[vpn.customer_id])) {
          customerLastActivity[vpn.customer_id] = vpn.updated_at || vpn.created_at
        }
      }
    })

    customers.forEach(customer => {
      // Track last activity for customer based on customer record itself
      const custActivity = customer.updated_at || customer.created_at
      if (!customerLastActivity[customer.id] || new Date(custActivity) > new Date(customerLastActivity[customer.id])) {
        customerLastActivity[customer.id] = custActivity
      }
    })

    // Calculate statistics
    stats.value = {
      totalCustomers: customers.length,
      totalSites: sites.length,
      totalVpns: vpns.length,
    }

    // Find most recently "concerned" customers (by any activity)
    const sortableCustomers = customers.map(customer => ({
      ...customer,
      vpns: customerVPNs[customer.id] || [],
      sites: customerSites[customer.id] || [],
      lastActivity: customerLastActivity[customer.id] || customer.updated_at || customer.created_at,
    }))
    recentCustomers.value = sortableCustomers
      .sort((a, b) => new Date(b.lastActivity || 0) - new Date(a.lastActivity || 0))
      .slice(0, 5)
  } catch (error) {
    console.error('Error fetching service data:', error)
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to load service data',
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
  fetchServiceData()
  const interval = setInterval(fetchServiceData, 60000)
  onUnmounted(() => clearInterval(interval))
})
</script>

<style scoped>
/* Always show vertical scrollbar for custom-scrollbar */
.custom-scrollbar {
  scrollbar-color: var(--surface-300) var(--surface-50);
  scrollbar-width: thin;
  overflow-y: scroll;
}
.custom-scrollbar::-webkit-scrollbar {
  width: 8px;
  background: var(--surface-50);
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: var(--surface-300);
  border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-corner {
  background: var(--surface-50);
}

/* Add a left border highlight for recent items */
.recent-item-highlight {
  border-left: 3px solid var(--primary-color, #6366f1);
  /* fallback to a blue if --primary-color is not set */
  background: none !important;
}
</style>
