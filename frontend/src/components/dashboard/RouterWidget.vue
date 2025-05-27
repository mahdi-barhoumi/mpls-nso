<template>
  <div class="card h-full flex flex-col">
    <div v-if="selectedRouter" class="h-full flex flex-col">
      <!-- Header -->
      <div class="flex-none flex justify-between items-center mb-3">
        <div>
          <div class="flex items-center gap-3">
            <!-- ↓ gap-3 for moderate spacing -->
            <h5 class="text-lg m-0 font-semibold">
              Device: {{ routerData?.hostname || 'N/A' }}
            </h5>
            <div class="flex items-center gap-1">
              <span
                v-if="routerData"
                class="iface-status-dot"
                :class="routerData.reachable === true ? 'bg-green-400' : routerData.reachable === false ? 'bg-red-400' : 'bg-gray-400'"
                :title="routerData.reachable === true ? 'UP' : routerData.reachable === false ? 'DOWN' : 'UNKNOWN'"
              ></span>
              <span v-if="routerData" class="text-xs font-bold"
                :class="routerData.reachable === true ? 'text-green-500' : routerData.reachable === false ? 'text-red-500' : 'text-gray-400'">
                {{ routerData.reachable === true ? 'UP' : routerData.reachable === false ? 'DOWN' : 'UNKNOWN' }}
              </span>
            </div>
          </div>
          <div class="text-surface-500 dark:text-surface-0 text-sm mt-1">
            {{ routerData?.management_ip_address || 'No IP' }}
          </div>
        </div>
        <div class="rounded-lg w-8 h-8 flex items-center justify-center bg-blue-100 dark:bg-blue-400/10">
          <!-- Static icon instead of role text -->
          <i class="pi pi-server text-blue-500 text-lg"></i>
        </div>
      </div>

      <!-- Device Info Summary -->
      <div class="surface-100 p-3 border-round mb-1 grid grid-cols-3 gap-2 text-xs">
        <div class="flex items-center gap-3">
          <i class="pi pi-user text-green-500"></i>
          <div>
            <div class="text-muted-color">Role</div>
            <div class="font-medium">{{ routerData?.role || 'N/A' }}</div>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <i class="pi pi-box text-green-500"></i>
          <div>
            <div class="text-muted-color">Model</div>
            <div class="font-medium">{{ deviceInfo?.chassis_description || 'N/A' }}</div>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <i class="pi pi-database text-green-500"></i>
          <div>
            <div class="text-muted-color">Version</div>
            <div class="font-medium">{{ deviceInfo?.ios_version || 'N/A' }}</div>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <i class="pi pi-clock text-green-500"></i>
          <div>
            <div class="text-muted-color">Uptime</div>
            <div class="font-medium">{{ deviceInfo?.uptime_formatted || 'N/A' }}</div>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <i class="pi pi-sitemap text-green-500"></i>
          <div>
            <div class="text-muted-color">Interfaces</div>
            <div class="font-medium">{{ interfaces?.length || 0 }}</div>
          </div>
        </div>
      </div>

      <!-- Separator -->
      <div class="w-full border-t border-gray-200 dark:border-surface-700 mb-4"></div>

      <!-- Interfaces Grid -->
      <div class="flex-1 min-h-0">
        <div class="h-full overflow-y-scroll custom-scrollbar">
          <div class="grid grid-cols-2 md:grid-cols-3 gap-2 pr-1">
            <div
              v-for="iface in interfaces"
              :key="iface.name"
              class="iface-card p-2 border-round flex flex-col gap-1"
              :class="[
                iface.enabled ? 'iface-highlight-up' : 'iface-highlight-down',
                !iface.is_connected && 'iface-down'
              ]"
              :title="iface.name"
            >
              <div class="flex items-center gap-2">
                <span
                  class="iface-status-dot"
                  :class="iface.enabled ? 'bg-green-400' : 'bg-red-400'"
                  :title="iface.enabled ? 'Connected' : 'Disconnected'"
                ></span>
                <span class="font-medium text-xs truncate flex-1">{{ iface.name }}</span>
                <span class="text-xs font-mono" :class="iface.enabled ? 'text-green-400' : 'text-red-400'">
                  {{ iface.enabled ? 'UP' : 'DOWN' }}
                </span>
              </div>
              <div class="text-2xs text-muted-color truncate">
                {{ iface.ip_address || 'No IP' }}
              </div>
              <div class="text-2xs text-muted-color truncate">
                {{ iface.category }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="h-full flex items-center justify-center">
      <div class="text-center text-muted-color">
        <span class="text-2xl font-bold mb-2 block">↑</span>
        <span class="text-sm">Select a device from the map to view details</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import RouterService from '@/service/RouterService'
import MonitoringService from '@/service/MonitoringService'

const monitoringService = new MonitoringService()
const props = defineProps({
  selectedRouter: {
    type: String,
    default: null,
  },
})

const routerData = ref(null)
const interfaces = ref(null)
const deviceInfo = ref(null)

watch(
  () => props.selectedRouter,
  async (newId) => {
    if (newId) {
      try {
        routerData.value = await RouterService.getRouterById(newId)
        interfaces.value = await RouterService.getRouterInterfaces(newId)
        deviceInfo.value = await monitoringService.getDeviceInfo(newId)
      } catch (error) {
        console.error('Error fetching router data:', error)
        deviceInfo.value = null
      }
    } else {
      routerData.value = null
      interfaces.value = null
      deviceInfo.value = null
    }
  },
  { immediate: true },
)
</script>

<style scoped>
:deep(.custom-scrollbar) {
  scrollbar-width: thin;
  scrollbar-color: var(--surface-400) var(--surface-100);
}
:deep(.custom-scrollbar::-webkit-scrollbar) {
  width: 4px;
  height: 4px;
}
:deep(.custom-scrollbar::-webkit-scrollbar-track) {
  background: var(--surface-100);
  border-radius: 3px;
}
:deep(.custom-scrollbar::-webkit-scrollbar-thumb) {
  background-color: var(--surface-400);
  border-radius: 3px;
}

.card {
  margin-bottom: 0;
}

.iface-card {
  border: 1px solid var(--surface-200);
  min-width: 0;
  cursor: pointer;
  transition: box-shadow 0.15s, border-left 0.15s;
  box-shadow: 0 0 0 0 transparent;
  background: var(--surface-50);
  border-left: 3px solid transparent;
}
.iface-card:hover {
  box-shadow: 0 2px 8px 0 rgba(60, 60, 60, 0.07);
  border-color: var(--primary-200);
  background: var(--surface-100);
}
.iface-down {
  opacity: 0.7;
  filter: grayscale(0.2);
}
.iface-status-dot {
  width: 0.75em;
  height: 0.75em;
  border-radius: 50%;
  display: inline-block;
  margin-right: 0.1em;
}
.text-2xs {
  font-size: 0.7rem;
  line-height: 1.1;
}

/* Left border highlight for interface status */
.iface-highlight-up {
  border-left: 3px solid #22c55e !important; /* green-500 */
}
.iface-highlight-down {
  border-left: 3px solid #ef4444 !important; /* red-500 */
}
</style>
