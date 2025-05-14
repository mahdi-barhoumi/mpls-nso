<template>
  <div class="card h-full flex flex-col">
    <div v-if="selectedRouter" class="h-full flex flex-col">
      <!-- Header -->
      <div class="flex-none flex justify-between items-center mb-3">
        <div>
          <h5 class="text-lg m-0">Router Details</h5>
          <div class="text-surface-500 dark:text-surface-0 font-medium text-lg">
            {{ routerData?.hostname }}
          </div>
        </div>
        <div
          class="flex items-center justify-center bg-blue-100 dark:bg-blue-400/10 rounded-lg w-8 h-8"
        >
          <i class="pi pi-server text-blue-500"></i>
        </div>
      </div>

      <!-- Quick Stats -->
      <div class="flex-none grid grid-cols-3 gap-2 mb-3">
        <div class="surface-100 p-2 border-round">
          <div class="flex items-center justify-between mb-1">
            <span class="text-muted-color text-xs">Role</span>
            <i class="pi pi-cog text-orange-500 text-sm"></i>
          </div>
          <div class="text-sm font-medium">{{ routerData?.role || 'N/A' }}</div>
        </div>

        <div class="surface-100 p-2 border-round">
          <div class="flex items-center justify-between mb-1">
            <span class="text-muted-color text-xs">IP</span>
            <i class="pi pi-desktop text-cyan-500 text-sm"></i>
          </div>
          <div class="text-sm font-medium">{{ routerData?.management_ip || 'N/A' }}</div>
        </div>

        <div class="surface-100 p-2 border-round">
          <div class="flex items-center justify-between mb-1">
            <span class="text-muted-color text-xs">Interfaces</span>
            <i class="pi pi-sitemap text-purple-500 text-sm"></i>
          </div>
          <div class="text-sm font-medium">{{ interfaces?.length || 0 }}</div>
        </div>
      </div>

      <!-- Interfaces Grid -->
      <div class="flex-1 min-h-0">
        <div class="h-full overflow-y-auto custom-scrollbar">
          <div class="grid grid-cols-3 gap-2 pr-2">
            <div v-for="iface in interfaces" :key="iface.name" class="surface-50 p-2 border-round">
              <div class="flex items-center justify-between mb-1">
                <span class="font-medium text-sm truncate" :title="iface.name">{{
                  iface.name
                }}</span>
                <i
                  :class="[
                    'pi text-sm',
                    iface.is_connected
                      ? 'pi-check-circle text-green-500'
                      : 'pi-times-circle text-red-500',
                  ]"
                ></i>
              </div>
              <div class="text-xs text-muted-color">
                <div v-if="iface.ip_address" class="truncate" :title="iface.ip_address">
                  IP: {{ iface.ip_address }}
                </div>
                <div>Type: {{ iface.category }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="h-full flex items-center justify-center">
      <div class="text-center text-muted-color">
        <i class="pi pi-arrow-up text-xl mb-2 block"></i>
        <span class="text-sm">Select a router from the map to view details</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import RouterService from '@/service/RouterService'

const props = defineProps({
  selectedRouter: {
    type: String,
    default: null,
  },
})

const routerData = ref(null)
const interfaces = ref(null)

watch(
  () => props.selectedRouter,
  async (newId) => {
    if (newId) {
      try {
        routerData.value = await RouterService.getRouterById(newId)
        interfaces.value = await RouterService.getRouterInterfaces(newId)
      } catch (error) {
        console.error('Error fetching router data:', error)
      }
    } else {
      routerData.value = null
      interfaces.value = null
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

/* Ensure the card takes full height */
.card {
  margin-bottom: 0;
}
</style>
