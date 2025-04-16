<template>
  <div class="col-span-12">
    <div class="card mb-1 p-3" v-if="selectedRouter">
      <div class="flex justify-between items-center mb-2">
        <div>
          <span class="block text-muted-color font-medium mb-2">Router Details</span>
          <div class="text-surface-900 dark:text-surface-0 font-medium text-lg">
            {{ routerData?.hostname }}
          </div>
        </div>
        <div
          class="flex items-center justify-center bg-blue-100 dark:bg-blue-400/10 rounded-border"
          style="width: 2rem; height: 2rem"
        >
          <i class="pi pi-server text-blue-500 !text-lg"></i>
        </div>
      </div>

      <div class="grid gap-2">
        <div class="col-12 md:col-4 mb-2">
          <div class="card mb-0 p-2">
            <div class="flex justify-between items-center mb-1">
              <div>
                <span class="block text-muted-color font-medium text-sm">Role</span>
                <div class="text-surface-900 dark:text-surface-0 text-sm">
                  {{ routerData?.role }}
                </div>
              </div>
              <div
                class="flex items-center justify-center bg-orange-100 dark:bg-orange-400/10 rounded-border"
                style="width: 1.5rem; height: 1.5rem"
              >
                <i class="pi pi-cog text-orange-500 text-sm"></i>
              </div>
            </div>
          </div>
        </div>

        <div class="col-12 md:col-4 mb-2">
          <div class="card mb-0 p-2">
            <div class="flex justify-between items-center mb-1">
              <div>
                <span class="block text-muted-color font-medium text-sm">Management IP</span>
                <div class="text-surface-900 dark:text-surface-0 text-sm">
                  {{ routerData?.management_ip }}
                </div>
              </div>
              <div
                class="flex items-center justify-center bg-cyan-100 dark:bg-cyan-400/10 rounded-border"
                style="width: 1.5rem; height: 1.5rem"
              >
                <i class="pi pi-desktop text-cyan-500 text-sm"></i>
              </div>
            </div>
          </div>
        </div>

        <div class="col-12">
          <div class="card mb-0 p-2">
            <div class="flex justify-between items-center mb-2">
              <span class="text-lg font-medium">Interfaces</span>
              <div
                class="flex items-center justify-center bg-purple-100 dark:bg-purple-400/10 rounded-border"
                style="width: 1.5rem; height: 1.5rem"
              >
                <i class="pi pi-sitemap text-purple-500 text-sm"></i>
              </div>
            </div>

            <div v-if="interfaces" class="grid gap-2 interfaces-scroll">
              <div
                v-for="iface in interfaces"
                :key="iface.name"
                class="col-12 sm:col-6 md:col-4 xl:col-3"
              >
                <div class="surface-100 p-2 border-round mb-1">
                  <div class="font-medium mb-1 text-sm">{{ iface.name }}</div>
                  <div class="text-xs text-muted-color">
                    <div v-if="iface.ip_address">IP: {{ iface.ip_address }}</div>
                    <div>Type: {{ iface.category }}</div>
                    <div class="flex align-items-center gap-1">
                      Status:
                      <i
                        :class="[
                          'pi',
                          iface.is_connected
                            ? 'pi-check-circle text-green-500'
                            : 'pi-times-circle text-red-500',
                        ]"
                      ></i>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-else class="card mb-0 p-4">
      <div class="text-center text-muted-color text-sm">
        Select a router from the map to view details
      </div>
    </div>
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
        this.routerData = await RouterService.getRouterById(id)
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

/* Make interfaces section scrollable and compact */
.interfaces-scroll {
  max-height: 220px;
  overflow-y: auto;
  margin-bottom: 0.5rem;
  padding-right: 2px;
}

/* Reduce card and grid spacing for compactness */
.card {
  padding: 0.75rem !important;
}
.grid {
  margin: 0 !important;
  gap: 0.5rem !important;
}
.col-12,
.md\:col-4,
.sm\:col-6,
.xl\:col-3 {
  padding: 0 !important;
}
</style>
