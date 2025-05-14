<template>
  <div class="card h-full">
    <div class="card-header">
      <h5 class="text-lg m-0">VPNs Overview</h5>
      <div class="flex items-center gap-2">
        <Button
          icon="pi pi-refresh"
          text
          rounded
          size="small"
          :loading="loading"
          @click="fetchVPNData"
          tooltip="Refresh"
        />
        <Button
          icon="pi pi-external-link"
          text
          rounded
          size="small"
          @click="navigateToVPNs"
          tooltip="Manage VPNs"
        />
        <Button
          icon="pi pi-sitemap"
          text
          rounded
          size="small"
          @click="navigateToTopology"
          tooltip="View Full Topology"
        />
        <div
          class="flex items-center justify-center bg-purple-100 dark:bg-purple-400/10 rounded-lg w-8 h-8"
        >
          <i class="pi pi-shield text-purple-500"></i>
        </div>
      </div>
    </div>

    <div class="card-content">
      <!-- Quick Stats Grid -->
      <div class="grid grid-cols-2 gap-3 mb-3">
        <div class="surface-100 p-2 border-round">
          <div class="text-base font-medium">{{ stats.activeVpns }}</div>
          <div class="text-500 text-sm">Active VPNs</div>
        </div>
        <div class="surface-100 p-2 border-round">
          <div class="text-base font-medium">{{ stats.totalSites }}</div>
          <div class="text-500 text-sm">Connected Sites</div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex justify-center items-center p-4">
        <i class="pi pi-spin pi-spinner text-primary" style="font-size: 1.5rem"></i>
      </div>

      <!-- VPN List -->
      <div v-else-if="vpnList.length > 0" class="overflow-y-auto custom-scrollbar">
        <div
          v-for="vpn in vpnList"
          :key="vpn.id"
          class="p-2 border-round surface-50 mb-2 cursor-pointer hover:surface-100 transition-colors duration-200"
          @click="viewVPNDetails(vpn.id)"
        >
          <div class="flex justify-between items-center">
            <div>
              <div class="font-medium text-sm">{{ vpn.name }}</div>
              <div class="text-500 text-xs">{{ vpn.customerName }}</div>
              <div class="text-400 text-xs mt-1">
                <i class="pi pi-clock mr-1"></i>
                {{ new Date(vpn.created_at).toLocaleDateString() }}
              </div>
            </div>
            <div class="flex flex-col items-end gap-2">
              <Tag
                :value="vpn.status"
                :severity="vpn.status === 'active' ? 'success' : 'warning'"
              />
              <Tag :value="`${vpn.sites.length} sites`" severity="info" class="text-xs" />
            </div>
          </div>
          <div class="flex justify-between mt-2 text-xs text-500">
            <div>
              <i class="pi pi-check-circle mr-1"></i>
              {{ vpn.activeConnections }} active links
            </div>
          </div>
        </div>
      </div>

      <div v-else class="text-center text-500 text-sm p-3">No VPNs found</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import Tag from 'primevue/tag'
import Button from 'primevue/button'
import VPNService from '@/service/VPNService'
import CustomerService from '@/service/CustomerService'
import SiteService from '@/service/SiteService'

const router = useRouter()
const toast = useToast()
const loading = ref(false)
const vpnList = ref([])

const stats = ref({
  activeVpns: 0,
  totalVpns: 0,
  totalSites: 0,
  activeConnections: 0,
})

const fetchVPNData = async () => {
  loading.value = true
  try {
    // Fetch all required data in parallel
    const [vpns, customers, sites] = await Promise.all([
      VPNService.getVPNs(),
      CustomerService.getCustomers(),
      SiteService.getSites(),
    ]) // Ensure all data is in array format
    const processedCustomers = Array.isArray(customers) ? customers : []
    const processedSites = Array.isArray(sites) ? sites : []

    // Create lookup maps for efficient data access
    const customerMap = new Map(processedCustomers.map((c) => [c.id, c]))
    const vpnSitesMap = new Map()
    processedSites.forEach((site) => {
      if (site.vpnId && !vpnSitesMap.has(site.vpnId)) {
        vpnSitesMap.set(site.vpnId, [])
      }
      if (site.vpnId) {
        vpnSitesMap.get(site.vpnId).push(site)
      }
    })
    const vpnsWithSites = vpns.filter((vpn) => vpnSitesMap.get(vpn.id)?.length > 0)
    stats.value = {
      totalVpns: vpns.length,
      activeVpns: vpnsWithSites.length,
      totalSites: sites.length,
      activeConnections: sites.filter((site) => site.status === 'active').length,
    }
    // Process VPN list with enhanced data
    const processedVpns = Array.isArray(vpns) ? vpns : []
    vpnList.value = processedVpns
      .sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0))
      .slice(0, 5)
      .map((vpn) => {
        const customer = customerMap.get(vpn.customer_id)
        const vpnSites = vpnSitesMap.get(vpn.id) || []
        return {
          ...vpn,
          customerName: customer?.name || 'Unknown Customer',
          sites: vpnSites,
          status: vpnSites.length > 0 ? 'active' : 'pending',
          activeConnections: vpnSites.filter((site) => site.status === 'active').length,
        }
      })
  } catch (error) {
    console.error('Error fetching VPN data:', error)
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to load VPN data',
      life: 3000,
    })
  } finally {
    loading.value = false
  }
}

const viewVPNDetails = (vpnId) => {
  router.push(`/vpns/${vpnId}`)
}

const navigateToVPNs = () => {
  router.push('/vpns')
}

const navigateToTopology = () => {
  router.push('/topology')
}

onMounted(() => {
  fetchVPNData()
  // Refresh data every minute
  const interval = setInterval(fetchVPNData, 60000)
  onUnmounted(() => clearInterval(interval))
})
</script>
