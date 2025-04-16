<template>
  <div class="surface-card p-4 border-round shadow-2">
    <div v-if="selectedRouter">
      <h2 class="text-xl font-bold mb-4">Router Details</h2>
      <div class="grid">
        <div class="col-12 mb-3">
          <span class="font-bold">Hostname: </span>
          <span>{{ routerData?.hostname }}</span>
        </div>
        <div class="col-12 mb-3">
          <span class="font-bold">Role: </span>
          <span>{{ routerData?.role }}</span>
        </div>
        <div class="col-12 mb-3">
          <span class="font-bold">Management IP: </span>
          <span>{{ routerData?.management_ip }}</span>
        </div>
        <div class="col-12 mb-3">
          <h3 class="text-lg font-bold mb-2">Interfaces</h3>
          <div v-if="interfaces" class="surface-100 p-3 border-round">
            <div
              v-for="iface in interfaces"
              :key="iface.name"
              class="mb-3 p-2 border-bottom-1 surface-border"
            >
              <div class="font-bold">{{ iface.name }}</div>
              <div class="pl-3">
                <div v-if="iface.ip_address">IP: {{ iface.ip_address }}</div>
                <div>Type: {{ iface.category }}</div>
                <div>Status: {{ iface.is_connected ? 'Connected' : 'Not Connected' }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-else class="text-center p-4 text-500">Select a router from the map to view details</div>
  </div>
</template>

<script>
import RouterService from '@/service/RouterService'

export default {
  name: 'RouterWidget',
  props: {
    selectedRouter: {
      type: String,
      default: null,
    },
  },
  data() {
    return {
      routerData: null,
      interfaces: null,
    }
  },
  watch: {
    selectedRouter: {
      immediate: true,
      handler(newId) {
        if (newId) {
          this.fetchRouterData(newId)
        } else {
          this.routerData = null
          this.interfaces = null
        }
      },
    },
  },
  methods: {
    async fetchRouterData(id) {
      try {
        const routers = await RouterService.getRouters()
        this.routerData = routers.find((r) => r.id === id)
        this.interfaces = await RouterService.getRouterInterfaces(id)
      } catch (error) {
        console.error('Error fetching router data:', error)
      }
    },
  },
}
</script>

<style scoped>
.surface-card {
  height: 100%;
  overflow-y: auto;
}
</style>
