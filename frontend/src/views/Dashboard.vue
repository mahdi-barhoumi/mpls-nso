<script setup>
import MapWidget from '@/components/dashboard/MapWidget.vue'
import RouterWidget from '@/components/dashboard/RouterWidget.vue'
import VPNOverviewWidget from '@/components/dashboard/VPNOverviewWidget.vue'
import CustomerWidget from '@/components/dashboard/CustomerWidget.vue'
import { ref } from 'vue'

const selectedRouter = ref(null)

const handleRouterSelect = (router) => {
  selectedRouter.value = router
}
</script>

<template>
  <div class="grid grid-cols-12 gap-4 h-[calc(100vh-12rem)]">
    <!-- Left Column: Map and Router Details -->
    <div class="col-span-12 lg:col-span-8 grid grid-rows-2 gap-4 h-full">
      <!-- Network Map -->
      <div class="h-full">
        <MapWidget @node-selected="handleRouterSelect" class="h-full" />
      </div>

      <!-- Router Details -->
      <div class="h-full">
        <RouterWidget :selected-router="selectedRouter" class="h-full" />
      </div>
    </div>

    <!-- Right Column: VPN Overview and Customer Info -->
    <div class="col-span-12 lg:col-span-4 grid grid-rows-2 gap-4 h-full">
      <!-- VPN Overview Widget -->
      <div class="h-full">
        <VPNOverviewWidget class="h-full" />
      </div>

      <!-- Customer Widget -->
      <div class="h-full">
        <CustomerWidget class="h-full" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.card {
  margin-bottom: 0;
  height: 100%;
}

/* Ensure grid gaps don't cause overflow */
.grid {
  min-height: 0;
  min-width: 0;
}

/* Ensure content fits in grid cells */
.col-span-12,
.lg\:col-span-8,
.lg\:col-span-4 {
  min-height: 0;
  min-width: 0;
}

/* Custom scrollbars for better aesthetics */
:deep(.custom-scrollbar) {
  scrollbar-width: thin;
  scrollbar-color: var(--surface-400) var(--surface-100);
}

:deep(.custom-scrollbar::-webkit-scrollbar) {
  width: 4px;
}

:deep(.custom-scrollbar::-webkit-scrollbar-track) {
  background: var(--surface-100);
  border-radius: 3px;
}

:deep(.custom-scrollbar::-webkit-scrollbar-thumb) {
  background-color: var(--surface-400);
  border-radius: 3px;
}
</style>
